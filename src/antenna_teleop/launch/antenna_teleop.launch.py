# Sparky CIRC 2026 -- antenna_teleop
#
# Copyright 2026 UWRobotics

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    config_dir = os.path.join(get_package_share_directory('antenna_teleop'), 'config')
    joy_config = LaunchConfiguration('joy_config').perform(context)

    config_path = os.path.join(config_dir, f'{joy_config}_antenna_config.yaml')
    if not os.path.exists(config_path):
        # Only the ps4 mapping is tuned so far; fall back rather than failing
        # to launch on a different pad.
        config_path = os.path.join(config_dir, 'ps4_antenna_config.yaml')

    return [
        Node(
            package='antenna_teleop',
            executable='antenna_joy_node',
            name='antenna_joy_node',
            output='screen',
            parameters=[config_path]),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            name='joy_config',
            default_value='ps4',
            description='Controller mapping to load. Falls back to ps4 if absent.'),

        OpaqueFunction(function=launch_setup),
    ])
