# Sparky CIRC 2026 -- Sparky Description 
#
# Copyright 2026 UWRobotics

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


# TODO: Remove rviz args
def generate_launch_description():
    pkg = get_package_share_directory('sparky_description')

    use_mock_hardware = LaunchConfiguration('use_mock_hardware')
    can_interface = LaunchConfiguration('can_interface')

    declared_args = [
        DeclareLaunchArgument(
            'use_mock_hardware', default_value='true',
            description='true: DevHost. false: Load ODrive Plugin.'),
        DeclareLaunchArgument(
            'can_interface', default_value='can2',
            description='SocketCAN interface.'),
    ]

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]), ' ',
        PathJoinSubstitution([FindPackageShare('sparky_description'),
                              'urdf', 'sparky.control.urdf.xacro']), ' ',
        'use_mock_hardware:=', use_mock_hardware, ' ',
        'can_interface:=', can_interface,
    ])

    robot_description = {
        'robot_description': ParameterValue(robot_description_content,
                                            value_type=str)
    }

    controllers_yaml = os.path.join(pkg, 'config', 'sparky_controllers.yaml')

    # Launch Drivetrain URDF
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[robot_description],
        output='both',
    )

    # Launch ros2_control node
    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_description, controllers_yaml],
        remappings=[('/diff_drive_controller/cmd_vel_unstamped', '/cmd_vel')],
        output='both',
    )

    # ros2_control Spawner 
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    # diff_drive Spawner
    diff_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller', '--controller-manager', '/controller_manager'],
    )

    delay_diff_drive = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[diff_drive_controller_spawner],
        )
    )

    return LaunchDescription(declared_args + [
        robot_state_publisher,
        control_node,
        joint_state_broadcaster_spawner,
        delay_diff_drive,
    ])
