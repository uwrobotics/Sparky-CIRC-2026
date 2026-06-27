# Copyright 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License").
#
# Sparky drivetrain bringup against real ODrive hardware over CAN, driven by a
# PS4 (DualShock4) controller, with RViz visualization.
#
# This is the "full stack on hardware" variant of drivetrain_rviz.launch.py:
# instead of mock_components it talks to the ODrive backend on a real SocketCAN
# interface (default can2), and it brings up the PS4 teleop by default.
#
# Composes:
#   - sparky_description/control.launch.py   -> ros2_control + ODrive hardware
#                                               (can2) + diff_drive_controller
#                                               + robot_state_publisher + RViz
#                                               + velocity_marker
#   - groundstation_bringup/teleop_launch.py -> PS4 teleop on /cmd_vel
#
# Prerequisite: the CAN interface must be up before launching, e.g.
#   sudo ip link set can2 up type can bitrate 250000
#
# Usage:
#   # Real ODrive on can2 + PS4 teleop + RViz (defaults)
#   ros2 launch drivetrain_bringup drivetrain_can_ps4_rviz.launch.py
#
#   # Use a different CAN interface
#   ros2 launch drivetrain_bringup drivetrain_can_ps4_rviz.launch.py can_interface:=can0
#
#   # Headless (no RViz)
#   ros2 launch drivetrain_bringup drivetrain_can_ps4_rviz.launch.py rviz:=false

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_mock_hardware = LaunchConfiguration('use_mock_hardware')
    can_interface = LaunchConfiguration('can_interface')
    use_rviz = LaunchConfiguration('rviz')
    teleop = LaunchConfiguration('teleop')
    joy_config = LaunchConfiguration('joy_config')

    declared_args = [
        DeclareLaunchArgument(
            'use_mock_hardware', default_value='false',
            description='false: real ODrive over CAN. true: mock_components (RViz only).'),
        DeclareLaunchArgument(
            'can_interface', default_value='can2',
            description='SocketCAN interface for the ODrive backend (must be up beforehand).'),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='Launch RViz drivetrain visualization.'),
        DeclareLaunchArgument(
            'teleop', default_value='true',
            description='Launch the PS4/joystick teleop (publishes /cmd_vel).'),
        DeclareLaunchArgument(
            'joy_config', default_value='ps4',
            description='Controller profile for teleop: ps4, stadia, sn30pro, steamdeck.'),
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

    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('groundstation_bringup'), 'launch', 'teleop_launch.py'])),
        launch_arguments={'joy_config': joy_config}.items(),
        condition=IfCondition(teleop),
    )

    return LaunchDescription(declared_args + [
        control_launch,
        teleop_launch,
    ])
