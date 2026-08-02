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

    declared_args = [
        DeclareLaunchArgument(
            'joy_config', default_value='ps4',
            description='Controller option: ps4(default), stadia, sn30pro, steamdeck.'),
    ]

    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('groundstation_bringup'), 'launch', 'teleop_launch.py'])),
        launch_arguments={'joy_config': joy_config}.items(),
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
        rviz_node,
    ])
