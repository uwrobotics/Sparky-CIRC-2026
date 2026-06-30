# Copyright 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License").
#
# cmd_vel -> ros2_control -> per-wheel velocity -> RViz, for the Sparky rover.
#
# Pipeline:
#   /cmd_vel (Twist)  ->  diff_drive_controller  ->  6 velocity command interfaces
#       ->  mock hardware (mirrors cmd to state)  ->  joint_state_broadcaster
#       ->  robot_state_publisher (wheel TF)      ->  RViz
#   diff_drive_controller also publishes odom -> base_link TF, so the whole
#   rover drives around in RViz.
#
# Usage:
#   ros2 launch sparky_description control.launch.py
#   ros2 launch sparky_description control.launch.py use_mock_hardware:=false can_interface:=can0   # real ODrive (later)
#
# Then drive it (PS4 teleop publishes /cmd_vel), or for a quick test:
#   ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.3}, angular: {z: 0.4}}'

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = get_package_share_directory('sparky_description')

    use_mock_hardware = LaunchConfiguration('use_mock_hardware')
    can_interface = LaunchConfiguration('can_interface')
    use_rviz = LaunchConfiguration('rviz')

    declared_args = [
        DeclareLaunchArgument(
            'use_mock_hardware', default_value='true',
            description='true: mock_components (RViz only). false: real ODrive over CAN.'),
        DeclareLaunchArgument(
            'can_interface', default_value='can0',
            description='SocketCAN interface for the ODrive backend.'),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='Launch RViz.'),
    ]

    # Build robot_description from the ros2_control-enabled xacro.
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]), ' ',
        PathJoinSubstitution([FindPackageShare('sparky_description'),
                              'urdf', 'sparky.control.urdf.xacro']), ' ',
        'use_mock_hardware:=', use_mock_hardware, ' ',
        'can_interface:=', can_interface,
    ])
    # Force the xacro output to be treated as a plain string. Without value_type=str
    # launch tries to YAML-parse the URDF and fails with "Unable to parse the value
    # of parameter robot_description as yaml".
    robot_description = {
        'robot_description': ParameterValue(robot_description_content, value_type=str)
    }

    controllers_yaml = os.path.join(pkg, 'config', 'sparky_controllers.yaml')

    # controller_manager + hardware interface.
    # Remap the controller's Twist input to the conventional /cmd_vel topic that
    # the PS4 teleop publishes on.
    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_description, controllers_yaml],
        remappings=[('/diff_drive_controller/cmd_vel_unstamped', '/cmd_vel')],
        output='both',
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[robot_description],
        output='both',
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    diff_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller', '--controller-manager', '/controller_manager'],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(pkg, 'rviz', 'control.rviz')],
        condition=IfCondition(use_rviz),
        output='log',
    )

    # Publishes an RViz arrow whose length tracks the rover's actual speed.
    velocity_marker_node = Node(
        package='sparky_description',
        executable='velocity_marker.py',
        name='velocity_marker',
        parameters=[{'scale': 1.0}],
        remappings=[('velocity_marker', '/sparky/velocity_marker')],
        output='screen',
    )

    # Start diff_drive only after joint_state_broadcaster is up.
    delay_diff_drive = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[diff_drive_controller_spawner],
        )
    )

    return LaunchDescription(declared_args + [
        control_node,
        robot_state_publisher,
        joint_state_broadcaster_spawner,
        delay_diff_drive,
        rviz_node,
        velocity_marker_node,
    ])
