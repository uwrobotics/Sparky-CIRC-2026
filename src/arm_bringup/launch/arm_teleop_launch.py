import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    arm_teleop_pkg = get_package_share_directory('arm_teleop')

    arm_mapping    = os.path.join(arm_teleop_pkg, 'config', 'ps4_mapping.yaml')
    arm_vel_config = os.path.join(arm_teleop_pkg, 'config', 'ps4_velocity_config.yaml')

    return LaunchDescription([
        # No joy node here, groundstation_bringup already publishes /joy
        Node(
            package='arm_teleop',
            executable='arm_teleop_node',
            name='arm_teleop_node',
            output='screen',
            parameters=[arm_mapping, arm_vel_config],
        ),

    ])