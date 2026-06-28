import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    bringup_pkg = get_package_share_directory('groundstation_bringup')

    arm_mapping    = os.path.join(bringup_pkg, 'config', 'ps4_arm_mapping.yaml')
    arm_vel_config = os.path.join(bringup_pkg, 'config', 'ps4_arm_velocity_config.yaml')

    return LaunchDescription([
        Node(
            package='arm_teleop',
            executable='arm_teleop_node',
            name='arm_teleop_node',
            output='screen',
            parameters=[arm_mapping, arm_vel_config],
        ),
    ])