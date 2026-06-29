#!/usr/bin/env python3
# Copyright 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License").
#
# Publishes an RViz arrow Marker whose length and direction track the rover's
# actual velocity (from diff_drive_controller odometry). The arrow is anchored
# at base_link, so it follows the robot, points in the travel direction, grows
# with speed, and disappears when the rover is stopped.

import math

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point


class VelocityMarker(Node):
    def __init__(self):
        super().__init__('velocity_marker')

        # metres of arrow per m/s of speed
        self.declare_parameter('scale', 1.0)
        # below this speed (m/s) the arrow is hidden
        self.declare_parameter('min_speed', 0.02)
        # frame the arrow is drawn in (moves with the robot)
        self.declare_parameter('frame_id', 'base_link')
        # height of the arrow above the base, so it reads clearly in RViz
        self.declare_parameter('z_offset', 0.35)

        self.scale = self.get_parameter('scale').value
        self.min_speed = self.get_parameter('min_speed').value
        self.frame_id = self.get_parameter('frame_id').value
        self.z_offset = self.get_parameter('z_offset').value

        self.pub = self.create_publisher(Marker, 'velocity_marker', 1)
        self.create_subscription(
            Odometry, 'diff_drive_controller/odom', self.cb_odom, 10)

    def cb_odom(self, msg):
        # Body-frame velocity (base_link). For a diff-drive rover vy ~ 0, so the
        # arrow mostly points forward/backward along +x.
        vx = msg.twist.twist.linear.x
        vy = msg.twist.twist.linear.y
        speed = math.hypot(vx, vy)

        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'velocity'
        marker.id = 0
        marker.type = Marker.ARROW

        if speed < self.min_speed:
            # Hide the arrow when essentially stopped.
            marker.action = Marker.DELETE
            self.pub.publish(marker)
            return

        marker.action = Marker.ADD
        # Two-point arrow: start at the base, end scaled by the velocity vector.
        start = Point(x=0.0, y=0.0, z=self.z_offset)
        end = Point(x=vx * self.scale, y=vy * self.scale, z=self.z_offset)
        marker.points = [start, end]

        # scale.x = shaft diameter, scale.y = head diameter, scale.z = head length
        marker.scale.x = 0.04
        marker.scale.y = 0.10
        marker.scale.z = 0.15

        # Green, fully opaque.
        marker.color.r = 0.1
        marker.color.g = 0.9
        marker.color.b = 0.2
        marker.color.a = 1.0

        self.pub.publish(marker)


def main(args=None):
    rclpy.init(args=args)
    node = VelocityMarker()
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
