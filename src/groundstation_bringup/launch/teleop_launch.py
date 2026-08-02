# Copyright (c) 2023 Aditya Kamath
# Copyright (c) 2026 UWRobotics

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    joy_launch_path = PathJoinSubstitution(
        [FindPackageShare('groundstation_bringup'), 'launch', 'joy_launch.py'])

    joy_mode_config_dynamic_path = [get_package_share_directory('groundstation_bringup'),
                                    '/config/',
                                    LaunchConfiguration('joy_config'),
                                    '_mode_config.yaml']

    return LaunchDescription([
        DeclareLaunchArgument(
            name='joy_config',
            default_value='ps4',
            description='Select Controller: ps4 (PS4/DS4), stadia (Google Stadia), sn30pro (8BitDo SN30 Pro), steamdeck (Valve Steam Deck), none (Disabled)'),

        DeclareLaunchArgument(
            name='executor',
            default_value='True',
            description='If True, run multi-threaded executor. If False, run both nodes separately'),

        Node(
            condition=IfCondition(LaunchConfiguration('executor')),
            package='akros2_teleop',
            executable='teleop_node',
            output='screen',
            parameters=[{'timer_period': 0.02}, joy_mode_config_dynamic_path],
            remappings=[
                ('/teleop_vel', '/joy_vel'),
                ('/auto_vel', '/nav_vel'),
                ('/mix_vel', '/cmd_vel'),
            ]),

        GroupAction(
            condition=UnlessCondition(LaunchConfiguration('executor')),
            actions = [
                Node(
                    package='akros2_teleop',
                    executable='twist_mixer',
                    name='twist_mixer',
                    output='screen',
                    parameters=[{'timer_period': 0.02}],
                    remappings=[('/teleop_vel', '/joy_vel'),
                                ('/auto_vel', '/nav_vel'),
                                ('/mix_vel', '/cmd_vel')]),

                Node(
                    package='akros2_teleop',
                    executable='joy_mode_handler',
                    name='joy_mode_handler',
                    output='screen',
                    parameters=[joy_mode_config_dynamic_path]),
            ]),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(joy_launch_path),
            launch_arguments={'joy_config': LaunchConfiguration('joy_config')}.items()),
    ])
