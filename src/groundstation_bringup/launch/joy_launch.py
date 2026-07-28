# Copyright (c) 2023 Aditya Kamath
# Copyright (c) 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Derived from adityakamath/akros2_teleop (launch/joy_launch.py).
# Modifications by UWRobotics: config sourced from groundstation_bringup,
# default joy_config is 'ps4'. Extended to run two controllers at once —
# PS4 for the drivetrain, Xbox for the arm — bound by device_name (not
# device_id) since that's what actually lets two different physical
# controllers be told apart reliably. See arm_teleop_launch.py for the
# node that consumes /joy_arm.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import LaunchConfigurationNotEquals
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    joy_twist_config_dynamic_path = [get_package_share_directory('groundstation_bringup'),
                                     '/config/',
                                     LaunchConfiguration('joy_config'),
                                     '_twist_config.yaml']

    return LaunchDescription([
        DeclareLaunchArgument(
            name='joy_config',
            default_value='ps4',
            description='Select drivetrain controller: ps4 (PS4/DS4), stadia (Google Stadia), sn30pro (8BitDo SN30 Pro), steamdeck (Valve Steam Deck), none (Disabled)'),

        DeclareLaunchArgument(
            name='arm_joy_config',
            default_value='xbox',
            description='Select arm controller: xbox (Xbox One pad), none (Disabled)'),

        # Drivetrain controller (PS4 by default) -> /joy_drive -> teleop_twist_joy -> /joy_vel
        GroupAction(
            condition=LaunchConfigurationNotEquals('joy_config', 'none'),
            actions = [
                Node(
                    package='joy',
                    executable='joy_node',
                    name='joy_node_drive',
                    parameters=[{
                        # TODO: verify this exact string with
                        # `ros2 run joy joy_enumerate_devices` while the PS4
                        # pad is connected — unlike the Xbox device_name
                        # below, this one hasn't been empirically confirmed.
                        'device_name': 'Wireless Controller',
                        'deadzone': 0.1,
                        'autorepeat_rate': 20.0,
                        'coalesce_interval': 0.01,
                    }],
                    remappings=[('joy', 'joy_drive')],
                    arguments=["--ros-args", "--log-level", "ERROR"]),

                Node(
                    package='teleop_twist_joy',
                    executable='teleop_node',
                    name='joy_teleop',
                    parameters=[joy_twist_config_dynamic_path],
                    remappings=[('joy', 'joy_drive'), ('/cmd_vel', '/joy_vel')]),
            ]),

        # Arm controller (Xbox) -> /joy_arm -> arm_teleop_node
        # (arm_teleop_node itself is launched separately, in arm_teleop_launch.py)
        GroupAction(
            condition=LaunchConfigurationNotEquals('arm_joy_config', 'none'),
            actions = [
                Node(
                    package='joy',
                    executable='joy_node',
                    name='joy_node_arm',
                    parameters=[{
                        # Confirmed via joy_enumerate_devices tonight.
                        'device_name': 'Generic X-Box pad',
                        'deadzone': 0.1,
                        'autorepeat_rate': 20.0,
                        'coalesce_interval': 0.01,
                    }],
                    remappings=[('joy', 'joy_arm')],
                    arguments=["--ros-args", "--log-level", "ERROR"]),
            ]),
    ])