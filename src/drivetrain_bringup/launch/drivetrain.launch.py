# Sparky CIRC 2026 -- drivetrain_bringup 
#
# Copyright 2026 UWRobotics

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_mock_hardware = LaunchConfiguration('use_mock_hardware')
    can_interface = LaunchConfiguration('can_interface')
    use_gimbal = LaunchConfiguration('use_gimbal')
    gimbal_host = LaunchConfiguration('gimbal_host')

    declared_args = [
        DeclareLaunchArgument(
            'use_mock_hardware', default_value='false',
            description='true: DevHost. false: Load ODrive Plugin.'),
        DeclareLaunchArgument(
            'can_interface', default_value='can2',
            description='SocketCAN interface.'),
        DeclareLaunchArgument(
            'use_gimbal', default_value='true',
            description='Run SIYI gimbal control/telemetry on the rover.'),
        DeclareLaunchArgument(
            'gimbal_host', default_value='192.168.144.25',
            description='SIYI gimbal IP on the rover-side network.'),
    ]

    drivetrain_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('sparky_description'), 'launch', 'control.launch.py'])),
        launch_arguments={
            'use_mock_hardware': use_mock_hardware,
            'can_interface': can_interface,
        }.items(),
    )

    siyi_gimbal_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('siyi_ros2'), 'launch', 'siyi.launch.py'])),
        launch_arguments={
            'host': gimbal_host,
            'auto_reconnect': 'true',
        }.items(),
        condition=IfCondition(use_gimbal),
    )

    return LaunchDescription(declared_args + [
        drivetrain_launch,
        siyi_gimbal_launch,
    ])
