# Copyright 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License").
#
# SIYI A8 mini gimbal-camera bringup for the Sparky rover.
#
# This is a thin wrapper around the upstream siyi_ros2/siyi_full.launch.py. We
# cannot edit the siyi_ros2 submodule, and its launch file defaults camera_model
# to "zt30" and passes it as an explicit parameter, which OVERRIDES the "a8" set
# in the submodule's camera_params.yaml. For zt30 the SDK builds the new-gen RTSP
# URL rtsp://<host>:8554/video1, but the A8 mini is an old-gen camera and only
# serves rtsp://<host>:8554/main.264 — so /video1 returns RTSP 404 and the
# GStreamer pipeline fails to connect. This wrapper forces camera_model:=a8 so the
# correct /main.264 URL is built. Everything else passes through to the upstream
# launch (which also brings up the gimbal-control siyi_node).
#
# Runs on the rover (the camera is on the robot at 192.168.144.25). Prerequisite:
# the host/container must have an IP on the camera subnet, e.g. 192.168.144.100/24
# on the wired interface, and be able to reach 192.168.144.25.
#
# Usage:
#   ros2 launch drivetrain_bringup siyi_camera.launch.py
#   ros2 launch drivetrain_bringup siyi_camera.launch.py host:=192.168.144.25
#
# NOTE on debugging: the upstream launch forces GST_DEBUG=0, and because it sets
# that env var immediately before spawning its nodes, it cannot be overridden from
# this wrapper. To see GStreamer pipeline/connection errors, run the camera node
# standalone instead of via this launch, e.g.:
#   GST_DEBUG=3 ros2 run siyi_ros2 siyi_camera_node --ros-args -p camera_model:=a8

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    host = LaunchConfiguration('host')

    declared_args = [
        DeclareLaunchArgument(
            'host', default_value='192.168.144.25',
            description='SIYI camera/gimbal IP address.'),
    ]

    siyi_full = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('siyi_ros2'), 'launch', 'siyi_full.launch.py'])),
        launch_arguments={
            # The critical fix: A8 mini is old-gen -> /main.264, not /video1.
            'camera_model': 'a8',
            'host': host,
        }.items(),
    )

    return LaunchDescription(declared_args + [siyi_full])
