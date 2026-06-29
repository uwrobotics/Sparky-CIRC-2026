# Copyright 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License").
#
# Sparky drivetrain low-level control against real ODrive hardware over CAN.
#
# This runs on the rover (Jetson). It is the on-robot, low-level half of the
# stack: ros2_control + ODrive hardware + diff_drive_controller +
# robot_state_publisher. It is headless by default -- RViz lives on the
# groundstation (see groundstation_bringup/groundstation.launch.py), which pulls
# the robot model (/robot_description, latched) and TF from here over the network.
#
# This is the "real hardware" variant of drivetrain_rviz.launch.py: instead of
# mock_components it talks to the ODrive backend on a real SocketCAN interface
# (default can2).
#
# Note: this launch does NOT bring up the PS4/joystick teleop or RViz. Teleop and
# visualization both run on the groundstation; this file just listens for /cmd_vel.
#
# Composes:
#   - sparky_description/control.launch.py   -> ros2_control + ODrive hardware
#                                               (can2) + diff_drive_controller
#                                               + robot_state_publisher
#                                               + velocity_marker
#
# Prerequisite: the CAN interface must be up before launching, e.g.
#   sudo ip link set can2 up type can bitrate 250000
#
# Usage:
#   # Real ODrive on can2 (headless low-level control -- the default)
#   ros2 launch drivetrain_bringup drivetrain_can_ps4_rviz.launch.py
#
#   # Use a different CAN interface
#   ros2 launch drivetrain_bringup drivetrain_can_ps4_rviz.launch.py can_interface:=can0
#
#   # Bring up a local RViz too (e.g. debugging directly on the rover)
#   ros2 launch drivetrain_bringup drivetrain_can_ps4_rviz.launch.py rviz:=true

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_mock_hardware = LaunchConfiguration('use_mock_hardware')
    can_interface = LaunchConfiguration('can_interface')
    use_rviz = LaunchConfiguration('rviz')

    declared_args = [
        DeclareLaunchArgument(
            'use_mock_hardware', default_value='false',
            description='false: real ODrive over CAN. true: mock_components (RViz only).'),
        DeclareLaunchArgument(
            'can_interface', default_value='can2',
            description='SocketCAN interface for the ODrive backend (must be up beforehand).'),
        DeclareLaunchArgument(
            'rviz', default_value='false',
            description='Launch a local RViz on the rover. Off by default -- the '
                        'groundstation runs RViz. Enable for on-rover debugging.'),
    ]

    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('sparky_description'), 'launch', 'control.launch.py'])),
        launch_arguments={
            'use_mock_hardware': use_mock_hardware,
            'can_interface': can_interface,
            'rviz': use_rviz,
        }.items(),
    )

    return LaunchDescription(declared_args + [
        control_launch,
    ])
