# Sparky CIRC 2026 -- gimbal_teleop
#
# Copyright 2026 UWRobotics

"""D-pad teleoperation for the SIYI gimbal.

Maps the D-pad axes of a joystick (PS4 D-pad reports as the last two axes,
each -1 / 0 / +1) onto ``siyi_msgs/GimbalRateCmd`` messages published on
``/siyi/cmd/rate``, the rate-command path of ``siyi_node``.

A held direction produces a constant slew rate; releasing the D-pad sends
zero rate for ``zero_hold_s`` and then goes quiet (the ``siyi_node``
watchdog also zeroes the gimbal if commands stop arriving).
"""

import sys

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Joy
from siyi_msgs.msg import GimbalRateCmd

RATE_TOPIC = '/siyi/cmd/rate'


class GimbalJoyNode(Node):
    """Turns D-pad presses into gimbal yaw/pitch rate commands."""

    def __init__(self, node_name='gimbal_joy_node'):
        super().__init__(node_name)

        # PS4 over the Linux joystick interface: axis 6 = D-pad left/right
        # (+1 right), axis 7 = D-pad up/down (+1 down).
        self.declare_parameter('yaw_axis', 6)
        self.declare_parameter('pitch_axis', 7)

        # Slew rate applied while a direction is held, degrees per second.
        self.declare_parameter('yaw_rate_dps', 30.0)
        self.declare_parameter('pitch_rate_dps', 30.0)

        # Flip if the gimbal moves opposite to the pressed direction.
        self.declare_parameter('invert_yaw', False)
        self.declare_parameter('invert_pitch', False)

        # Axis magnitude above which the D-pad counts as pressed.
        self.declare_parameter('axis_threshold', 0.5)

        # Rate at which the held command is repeated to the gimbal.
        self.declare_parameter('publish_rate_hz', 20.0)

        # How long zero-rate commands keep being sent after release.
        self.declare_parameter('zero_hold_s', 0.5)

        # If /joy goes quiet for this long (controller unplugged, joy_node
        # died), stop commanding instead of latching the last direction.
        self.declare_parameter('joy_timeout_s', 0.5)

        # Button that must be held for the D-pad to move the gimbal.
        # -1 disables the check.
        self.declare_parameter('enable_button', -1)

        self.declare_parameter('frame_id', 'siyi_gimbal')

        self._yaw_axis = self.get_parameter('yaw_axis').value
        self._pitch_axis = self.get_parameter('pitch_axis').value
        self._yaw_rate_dps = self.get_parameter('yaw_rate_dps').value
        self._pitch_rate_dps = self.get_parameter('pitch_rate_dps').value
        self._yaw_sign = -1.0 if self.get_parameter('invert_yaw').value else 1.0
        self._pitch_sign = -1.0 if self.get_parameter('invert_pitch').value else 1.0
        self._axis_threshold = self.get_parameter('axis_threshold').value
        self._zero_hold_s = self.get_parameter('zero_hold_s').value
        self._joy_timeout_s = self.get_parameter('joy_timeout_s').value
        self._enable_button = self.get_parameter('enable_button').value
        self._frame_id = self.get_parameter('frame_id').value

        self._yaw_dir = 0.0
        self._pitch_dir = 0.0
        self._last_joy_ns = None  # None until the first Joy message arrives
        self._idle_since_ns = None  # set when the command first becomes zero

        self._pub = self.create_publisher(
            GimbalRateCmd, RATE_TOPIC, qos_profile_sensor_data)
        self.create_subscription(Joy, 'joy', self.cb_joy, 10)

        period = 1.0 / max(1.0, self.get_parameter('publish_rate_hz').value)
        self.create_timer(period, self.cb_timer)

        self.get_logger().info(
            f'Gimbal D-pad teleop ready (yaw axis {self._yaw_axis}, '
            f'pitch axis {self._pitch_axis}, '
            f'{self._yaw_rate_dps}/{self._pitch_rate_dps} dps) -> {RATE_TOPIC}')

    def cb_joy(self, msg):
        """
        :type msg: Joy
        """
        self._last_joy_ns = self.get_clock().now().nanoseconds

        needed = max(self._yaw_axis, self._pitch_axis)
        if len(msg.axes) <= needed:
            self.get_logger().warning(
                f'Joy message has {len(msg.axes)} axes, need at least '
                f'{needed + 1} -- check the yaw_axis/pitch_axis parameters',
                throttle_duration_sec=5.0)
            return

        if not self._enabled(msg):
            self._yaw_dir = 0.0
            self._pitch_dir = 0.0
            return

        self._yaw_dir = self._direction(msg.axes[self._yaw_axis]) * self._yaw_sign
        self._pitch_dir = self._direction(msg.axes[self._pitch_axis]) * self._pitch_sign

    def cb_timer(self):
        now_ns = self.get_clock().now().nanoseconds

        if self._joy_stale(now_ns):
            if self._yaw_dir != 0.0 or self._pitch_dir != 0.0:
                self.get_logger().warning(
                    'No joy messages for '
                    f'{self._joy_timeout_s} s -- stopping the gimbal')
            self._yaw_dir = 0.0
            self._pitch_dir = 0.0

        yaw_rate = self._yaw_dir * self._yaw_rate_dps
        pitch_rate = self._pitch_dir * self._pitch_rate_dps

        if yaw_rate == 0.0 and pitch_rate == 0.0:
            if self._idle_since_ns is None:
                self._idle_since_ns = now_ns
            # Send zeros for a moment after release, then stay off the wire.
            if (now_ns - self._idle_since_ns) > self._zero_hold_s * 1e9:
                return
        else:
            self._idle_since_ns = None

        msg = GimbalRateCmd()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id
        msg.yaw_rate_dps = float(yaw_rate)
        msg.pitch_rate_dps = float(pitch_rate)
        self._pub.publish(msg)

    def _joy_stale(self, now_ns):
        if self._last_joy_ns is None:
            return True
        return (now_ns - self._last_joy_ns) > self._joy_timeout_s * 1e9

    def _enabled(self, msg):
        if self._enable_button < 0:
            return True
        if len(msg.buttons) <= self._enable_button:
            self.get_logger().warning(
                f'Joy message has {len(msg.buttons)} buttons, need at least '
                f'{self._enable_button + 1} for enable_button',
                throttle_duration_sec=5.0)
            return False
        return bool(msg.buttons[self._enable_button])

    def _direction(self, axis_value):
        if axis_value > self._axis_threshold:
            return 1.0
        if axis_value < -self._axis_threshold:
            return -1.0
        return 0.0


def main(args=None):
    rclpy.init(args=args)
    node = GimbalJoyNode()

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
