# Sparky CIRC 2026 -- siyi_watchdog
#
# Copyright 2026 UWRobotics

"""Restarts siyi_camera_node when the RTSP stream stops delivering frames.

The SIYI A8 drops its RTSP session roughly 30-50 s after sustained gimbal
control traffic starts -- measured across every command rate (5/10/20 Hz),
both command types (rate 0x07 and attitude 0x0E), both RTSP transports, and
both UDP and TCP control channels. Video alone survives indefinitely.

The GStreamer backend in siyi_ros2 reports the resulting EOS and stops; it
never rebuilds the pipeline, so the feed is frozen until the node restarts.
This node watches the camera's liveness topic and, when frames stop, signals
siyi_camera_node to exit so the launch file's ``respawn`` brings it back.

``/siyi/camera_info`` is the liveness signal: siyi_camera_node publishes it
once per frame from the same worker that publishes the image, so it tracks
the stream exactly while costing nothing to subscribe to.
"""

import os
import signal
import subprocess
import sys
import threading
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy
from sensor_msgs.msg import CameraInfo

# Must match siyi_camera_node's publisher QoS or no messages arrive.
_LIVENESS_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)


class CameraWatchdog(Node):
    """Signals a stalled camera node to exit so launch can respawn it."""

    def __init__(self, node_name='camera_watchdog'):
        super().__init__(node_name)

        self.declare_parameter('liveness_topic', '/siyi/camera_info')

        # No frames for this long counts as a stall. The stream runs ~23 fps
        # (~43 ms/frame) but a healthy stream was measured with gaps up to
        # 190 ms, so this is the practical floor -- going to 200 ms would
        # restart a stream that is merely jittering.
        self.declare_parameter('stall_timeout_s', 0.5)

        # Quiet window after start-up and after each restart. The pipeline
        # needs a couple of seconds to import, negotiate RTSP and produce a
        # first frame -- without this the watchdog kills it before it streams.
        self.declare_parameter('startup_grace_s', 10.0)

        # pgrep pattern used to find the camera process.
        self.declare_parameter('process_pattern', 'siyi_camera_node')

        # SIGINT lets rclpy shut down cleanly, so the RTSP session is torn
        # down properly. The camera does not ACK the FIN of an abandoned
        # session, leaving sockets in FIN-WAIT-1, so a clean exit matters.
        self.declare_parameter('kill_grace_s', 1.0)

        # Detection latency is stall_timeout_s + up to one check period, so
        # this stays well under the timeout.
        self.declare_parameter('check_period_s', 0.1)
        self.declare_parameter('enabled', True)

        self._liveness_topic = self.get_parameter('liveness_topic').value
        self._stall_timeout_s = self.get_parameter('stall_timeout_s').value
        self._startup_grace_s = self.get_parameter('startup_grace_s').value
        self._process_pattern = self.get_parameter('process_pattern').value
        self._kill_grace_s = self.get_parameter('kill_grace_s').value
        self._enabled = self.get_parameter('enabled').value

        self._lock = threading.Lock()
        self._last_frame_s = None      # None until the first frame ever arrives
        self._quiet_until_s = time.monotonic() + self._startup_grace_s
        self._restarts = 0
        self._restart_in_flight = False

        self.create_subscription(
            CameraInfo, self._liveness_topic, self.cb_liveness, _LIVENESS_QOS)
        self.create_timer(self.get_parameter('check_period_s').value, self.cb_check)

        self.get_logger().info(
            f'Camera watchdog armed on {self._liveness_topic} '
            f'(stall>{self._stall_timeout_s}s, grace={self._startup_grace_s}s, '
            f'pattern="{self._process_pattern}", enabled={self._enabled})')

    def cb_liveness(self, msg):
        """
        :type msg: CameraInfo
        """
        with self._lock:
            first = self._last_frame_s is None
            self._last_frame_s = time.monotonic()
        if first:
            self.get_logger().info('Stream is live')

    def cb_check(self):
        if not self._enabled or self._restart_in_flight:
            return

        now = time.monotonic()
        if now < self._quiet_until_s:
            return

        with self._lock:
            last = self._last_frame_s

        if last is None:
            # Never streamed at all -- the grace window has already expired,
            # so this is a camera node that came up but never connected.
            self.get_logger().warning(
                'No frames since start-up — restarting camera node')
        elif now - last > self._stall_timeout_s:
            self.get_logger().warning(
                f'No frames for {now - last:.1f}s — restarting camera node')
        else:
            return

        self._restart_in_flight = True
        threading.Thread(
            target=self._restart_camera, name='camera_restart', daemon=True).start()

    def _restart_camera(self):
        try:
            pids = self._camera_pids()
            if not pids:
                self.get_logger().error(
                    f'No process matching "{self._process_pattern}" — cannot '
                    'restart. Is the camera node running under this launch?')
                return

            for pid in pids:
                self._signal_process(pid)

            self._restarts += 1
            self.get_logger().info(
                f'Camera node signalled to exit (restart #{self._restarts}); '
                'waiting for launch respawn')
        finally:
            with self._lock:
                self._last_frame_s = None
            self._quiet_until_s = time.monotonic() + self._startup_grace_s
            self._restart_in_flight = False

    def _signal_process(self, pid):
        """SIGINT for a clean RTSP teardown, escalating to SIGKILL if it hangs."""
        try:
            os.kill(pid, signal.SIGINT)
        except ProcessLookupError:
            return
        except PermissionError:
            self.get_logger().error(f'Not permitted to signal pid {pid}')
            return

        deadline = time.monotonic() + self._kill_grace_s
        while time.monotonic() < deadline:
            if not self._pid_alive(pid):
                return
            time.sleep(0.2)

        self.get_logger().warning(
            f'pid {pid} ignored SIGINT for {self._kill_grace_s}s — sending SIGKILL')
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def _camera_pids(self):
        try:
            out = subprocess.run(
                ['pgrep', '-f', self._process_pattern],
                capture_output=True, text=True, timeout=5.0).stdout
        except (subprocess.SubprocessError, FileNotFoundError) as exc:
            self.get_logger().error(f'pgrep failed: {exc}')
            return []

        mine = os.getpid()
        pids = []
        for line in out.split():
            try:
                pid = int(line)
            except ValueError:
                continue
            # Never signal ourselves — our own command line contains the
            # pattern via the process_pattern parameter.
            if pid != mine:
                pids.append(pid)
        return pids

    @staticmethod
    def _pid_alive(pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True


def main(args=None):
    rclpy.init(args=args)
    node = CameraWatchdog()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except ExternalShutdownException:
        sys.exit(1)
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()
