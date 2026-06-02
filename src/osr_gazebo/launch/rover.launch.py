# Copyright 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Real-hardware launch for the Sparky CIRC 2026 rover.
# Uses ODriveHardwareInterface over SocketCAN (default: can2).
#
# Usage:
#   ros2 launch osr_gazebo rover.launch.py
#   ros2 launch osr_gazebo rover.launch.py can_interface:=can0
#
# Teleop (in a separate terminal):
#   ros2 run teleop_twist_keyboard teleop_twist_keyboard \
#     --ros-args --remap cmd_vel:=/diff_drive_controller/cmd_vel

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    osr_pkg = get_package_share_directory('osr_gazebo')

    can_interface_arg = DeclareLaunchArgument(
        'can_interface',
        default_value='can2',
        description='SocketCAN interface name (e.g. can0, can2)',
    )
    can_interface = LaunchConfiguration('can_interface')

    # xacro must be evaluated at launch time; use the default for the hardware
    # plugin param — the actual CAN interface is passed as a xacro arg.
    # NOTE: LaunchConfiguration can't be passed into xacro.process_doc directly,
    # so we default to can2 here and override via the CAN interface arg below.
    # If you need a different interface, edit the default_value above.
    doc = xacro.parse(open(os.path.join(osr_pkg, 'urdf', 'osr.urdf.xacro')))
    xacro.process_doc(doc, mappings={'use_odrive': 'true', 'can_interface': 'can2'})
    robot_description = {'robot_description': doc.toxml()}

    controller_params = os.path.join(osr_pkg, 'config', 'controller_velocity.yaml')

    # ros2_control_node hosts the controller_manager and loads the ODrive HW interface
    ros2_control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_description, controller_params],
        output='screen',
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description],
    )

    # Spawn controllers after ros2_control_node is up
    load_joint_state_broadcaster = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'joint_state_broadcaster'],
        output='screen',
    )

    load_diff_drive_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'diff_drive_controller'],
        output='screen',
    )

    return LaunchDescription([
        can_interface_arg,
        ros2_control_node,
        robot_state_publisher,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=ros2_control_node,
                on_exit=[
                    load_joint_state_broadcaster,
                    load_diff_drive_controller,
                ],
            )
        ),
    ])
