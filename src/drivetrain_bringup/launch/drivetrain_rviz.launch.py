# Copyright 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License").
#
# Top-level Sparky drivetrain bringup.
#
# Composes:
#   - sparky_description/control.launch.py  -> ros2_control + diff_drive_controller
#                                              + robot_state_publisher + RViz
#                                              + velocity_marker
#   - groundstation_bringup/teleop_launch.py (optional) -> PS4 teleop on /cmd_vel
#
# Usage:
#   # Mock hardware + RViz (visualization only)
#   ros2 launch drivetrain_bringup drivetrain_rviz.launch.py
#
#   # Add PS4 teleop so a controller drives the rover
#   ros2 launch drivetrain_bringup drivetrain_rviz.launch.py teleop:=true
#
#   # Real ODrive hardware over CAN (later)
#   ros2 launch drivetrain_bringup drivetrain_rviz.launch.py use_mock_hardware:=false can_interface:=can0

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
            'use_mock_hardware', default_value='true',
            description='true: mock_components (RViz only). false: real ODrive over CAN.'),
        DeclareLaunchArgument(
            'can_interface', default_value='can0',
            description='SocketCAN interface for the ODrive backend.'),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='Launch RViz drivetrain visualization.'),
        DeclareLaunchArgument(
            'teleop', default_value='false',
            description='Also launch the PS4/joystick teleop (publishes /cmd_vel).'),
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
