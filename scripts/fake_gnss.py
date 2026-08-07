#!/usr/bin/env python3
"""Sparky CIRC 2026 -- fake VN-300 GNSS publisher.

Bench tool for exercising the RViz AerialMap (rviz_satellite) display without a
VN-300 attached. It fakes exactly what vn_sensor_msgs publishes -- a
sensor_msgs/NavSatFix on /vectornav/gnss stamped in the "vectornav" frame -- so
the groundstation stack cannot tell the difference.

The point is to see what each GNSS failure mode looks like on screen BEFORE it
happens in the field:

    # Healthy fix, rover circling on the map
    ./fake_gnss.py --tf

    # Antenna sees no satellites: NavSatFix keeps flowing, status is NO_FIX
    ./fake_gnss.py --tf --mode nofix

    # INS has not converged: lat/lon are NaN
    ./fake_gnss.py --tf --mode nan

    # Driver crashed / cable pulled: nothing on the topic at all
    ./fake_gnss.py --tf --mode silent

    # The realistic one -- fix drops out and recovers every 10 s
    ./fake_gnss.py --tf --mode dropout --dropout-period 10

--tf also publishes odom->base_link->vectornav so RViz can resolve the frame
with nothing else running. Drop it when the real drivetrain stack is up, or
robot_state_publisher and this script will fight over the same transform.

Copyright 2026 UWRobotics
"""

import argparse
import math

import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from tf2_ros import StaticTransformBroadcaster

# University of Waterloo, E5 parking lot -- the usual test site.
# CIRC itself runs in the Drumheller badlands, roughly 51.4636 / -112.7139.
DEFAULT_LAT = 43.4723
DEFAULT_LON = -80.5449
DEFAULT_ALT = 329.0

# Metres per degree of latitude. Good to ~0.1% over a parking-lot-sized area,
# which is far tighter than anything this bench tool needs to represent.
M_PER_DEG_LAT = 111320.0

# Mount offset copied from sparky.sensors.xacro. Kept in sync by hand: this
# script only publishes it under --tf, where the real URDF is absent.
VECTORNAV_XYZ = (0.0, 0.0, 0.2)
VECTORNAV_YAW = -math.pi / 2


class FakeGnss(Node):
    def __init__(self, args):
        super().__init__('fake_gnss')
        self.args = args
        self.start = self.get_clock().now()

        self.pub = self.create_publisher(NavSatFix, args.topic, 10)
        self.create_timer(1.0 / args.rate, self.tick)

        if args.tf:
            self.static_tf = StaticTransformBroadcaster(self)
            self.static_tf.sendTransform([
                self._tf('odom', 'base_link', (0.0, 0.0, 0.0), 0.0),
                self._tf('base_link', 'vectornav', VECTORNAV_XYZ, VECTORNAV_YAW),
            ])

        self.get_logger().info(
            f'mode={args.mode} topic={args.topic} rate={args.rate} Hz '
            f'origin={args.lat:.6f},{args.lon:.6f} radius={args.radius} m')

    def _tf(self, parent, child, xyz, yaw):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = parent
        t.child_frame_id = child
        t.transform.translation.x, t.transform.translation.y, t.transform.translation.z = xyz
        t.transform.rotation.z = math.sin(yaw / 2.0)
        t.transform.rotation.w = math.cos(yaw / 2.0)
        return t

    def _elapsed(self):
        return (self.get_clock().now() - self.start).nanoseconds / 1e9

    def _mode_now(self):
        """Resolve 'dropout' into the concrete mode for this instant."""
        if self.args.mode != 'dropout':
            return self.args.mode
        half = self.args.dropout_period / 2.0
        return 'fix' if (self._elapsed() % self.args.dropout_period) < half else 'nofix'

    def tick(self):
        mode = self._mode_now()
        if mode == 'silent':
            return

        msg = NavSatFix()
        msg.header.stamp = self.get_clock().now().to_msg()
        # Must match vectornav.yaml's frame_id -- rviz_satellite looks up TF
        # from the RViz Fixed Frame to whatever is stamped here.
        msg.header.frame_id = self.args.frame_id

        if mode == 'nofix':
            # What the real driver does when the GPS group reports GPSFIX_NOFIX:
            # it still publishes at full rate, it just flags the status. The
            # position fields keep their last/garbage values, which is exactly
            # why rviz_satellite refuses to trust them.
            msg.status.status = NavSatStatus.STATUS_NO_FIX
            msg.latitude = self.args.lat
            msg.longitude = self.args.lon
            msg.altitude = self.args.alt
        elif mode == 'nan':
            msg.status.status = NavSatStatus.STATUS_FIX
            msg.latitude = float('nan')
            msg.longitude = float('nan')
            msg.altitude = float('nan')
        else:
            # Drive a slow circle so tile loading and re-centering are visible.
            theta = 2.0 * math.pi * self._elapsed() / self.args.period
            north = self.args.radius * math.sin(theta)
            east = self.args.radius * math.cos(theta)
            msg.status.status = NavSatStatus.STATUS_FIX
            msg.latitude = self.args.lat + north / M_PER_DEG_LAT
            msg.longitude = self.args.lon + east / (
                M_PER_DEG_LAT * math.cos(math.radians(self.args.lat)))
            msg.altitude = self.args.alt

        msg.status.service = NavSatStatus.SERVICE_GPS
        msg.position_covariance = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 4.0]
        msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
        self.pub.publish(msg)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--mode', default='fix',
                   choices=['fix', 'nofix', 'nan', 'silent', 'dropout'],
                   help='GNSS health to simulate (default: fix)')
    p.add_argument('--dropout-period', type=float, default=10.0,
                   help='Full fix/no-fix cycle length for --mode dropout, seconds')
    p.add_argument('--topic', default='/vectornav/gnss')
    p.add_argument('--frame-id', dest='frame_id', default='vectornav')
    p.add_argument('--rate', type=float, default=20.0,
                   help='Publish rate, Hz -- matches the VN-300 BO1 divisor')
    p.add_argument('--lat', type=float, default=DEFAULT_LAT)
    p.add_argument('--lon', type=float, default=DEFAULT_LON)
    p.add_argument('--alt', type=float, default=DEFAULT_ALT)
    p.add_argument('--radius', type=float, default=20.0,
                   help='Circle radius in metres (0 to sit still)')
    p.add_argument('--period', type=float, default=60.0,
                   help='Seconds per lap of the circle')
    p.add_argument('--tf', action='store_true',
                   help='Also publish odom->base_link->vectornav. Omit when the '
                        'real drivetrain stack is running.')
    args = p.parse_args()

    rclpy.init()
    node = FakeGnss(args)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
