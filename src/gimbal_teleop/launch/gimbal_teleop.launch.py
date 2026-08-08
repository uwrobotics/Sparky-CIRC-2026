# Sparky CIRC 2026 -- gimbal_teleop
#
# Copyright 2026 UWRobotics

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    config_dir = os.path.join(get_package_share_directory('gimbal_teleop'), 'config')
    joy_config = LaunchConfiguration('joy_config').perform(context)

    config_path = os.path.join(config_dir, f'{joy_config}_gimbal_config.yaml')
    if not os.path.exists(config_path):
        # Only the ps4 mapping is tuned so far; other pads report the D-pad
        # on the same axes, so fall back rather than failing to launch.
        config_path = os.path.join(config_dir, 'ps4_gimbal_config.yaml')

    return [
        Node(
            package='gimbal_teleop',
            executable='gimbal_joy_node',
            name='gimbal_joy_node',
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
