# Sparky CIRC 2026 -- groundstation_bringup 
#
# Copyright 2026 UWRobotics

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    joy_config = LaunchConfiguration('joy_config')
    use_camera = LaunchConfiguration('use_camera')
    camera_host = LaunchConfiguration('camera_host')
    use_gimbal_teleop = LaunchConfiguration('use_gimbal_teleop')

    declared_args = [
        DeclareLaunchArgument(
            'joy_config', default_value='ps4',
            description='Controller option: ps4(default), stadia, sn30pro, steamdeck.'),
        DeclareLaunchArgument(
            'use_camera', default_value='true',
            description='Decode the SIYI RTSP feed into ROS image topics.'),
        DeclareLaunchArgument(
            'use_gimbal_teleop', default_value='true',
            description='Drive the SIYI gimbal with the controller D-pad.'),
        DeclareLaunchArgument(
            'camera_host', default_value='192.168.144.25',
            description='SIYI camera IP as reachable from the groundstation.'),
    ]

    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('groundstation_bringup'), 'launch', 'teleop_launch.py'])),
        launch_arguments={'joy_config': joy_config}.items(),
    )

    siyi_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('groundstation_bringup'), 'launch', 'siyi_camera_launch.py'])),
        launch_arguments={'host': camera_host}.items(),
        condition=IfCondition(use_camera),
    )

    gimbal_teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('gimbal_teleop'), 'launch', 'gimbal_teleop.launch.py'])),
        launch_arguments={'joy_config': joy_config}.items(),
        condition=IfCondition(use_gimbal_teleop),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', PathJoinSubstitution(
            [FindPackageShare('groundstation_bringup'), 'rviz', 'groundstation.rviz'])],
        output='log',
    )

    return LaunchDescription(declared_args + [
        teleop_launch,
        siyi_camera_launch,
        gimbal_teleop_launch,
        rviz_node,
    ])
