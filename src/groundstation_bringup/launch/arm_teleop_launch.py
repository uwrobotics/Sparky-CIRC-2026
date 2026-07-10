import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    arm_teleop_pkg = get_package_share_directory('arm_teleop')
    arm_mapping    = os.path.join(arm_teleop_pkg, 'config', 'xbox_mapping.yaml')
    arm_vel_config = os.path.join(arm_teleop_pkg, 'config', 'xbox_velocity_config.yaml')

    return LaunchDescription([
           # No joy node here this launch file expects joy_launch.py (this package) to already be running and publishing /joy.
        Node(
            package='arm_teleop',
            executable='arm_teleop_node',
            name='arm_teleop_node',
            output='screen',
            parameters=[arm_mapping, arm_vel_config],
            remappings=[('/joy', '/joy_arm')]
        ),

        Node(
            package='arm_teleop',
            executable='arm_safety_node',
            name='arm_safety_node',
            output='screen',
            parameters=[{'sim_mode': True}]
        )

    ])