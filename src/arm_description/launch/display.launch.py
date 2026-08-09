import os
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, TimerAction, DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def launch_setup(context, *args, **kwargs):
    pkg = get_package_share_directory('arm_description')
    xacro_file  = os.path.join(pkg, 'urdf', 'arm.control.urdf.xacro')
    rviz_config = os.path.join(pkg, 'config', 'arm_display.rviz')
    controllers = os.path.join(pkg, 'config', 'arm_controllers.yaml')

    use_mock_hardware = LaunchConfiguration('use_mock_hardware').perform(context)

    robot_description = xacro.process_file(
        xacro_file,
        mappings={'use_mock_hardware': use_mock_hardware}
    ).toxml()

    return [
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_description}]
        ),
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[
                {'robot_description': robot_description},
                controllers,
            ],
            output='screen',
        ),
        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'joint_state_broadcaster'],
                    output='screen'
                ),
            ]
        ),
        TimerAction(
            period=3.0,
            actions=[
                ExecuteProcess(
                    cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'forward_position_controller'],
                    output='screen'
                ),
            ]
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_mock_hardware',
            default_value='true',
            description='Use mock hardware components (true) or real ODrive/CAN hardware (false)'
        ),
        OpaqueFunction(function=launch_setup),
    ])