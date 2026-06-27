import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    arm_teleop_pkg = get_package_share_directory('arm_teleop')

    ps4_mapping     = os.path.join(arm_teleop_pkg, 'config', 'ps4_mapping.yaml')
    ps4_vel_config  = os.path.join(arm_teleop_pkg, 'config', 'ps4_velocity_config.yaml')

    return LaunchDescription([
        Node(
            package='joy_linux',
            executable='joy_linux_node',
            name='joy_linux',
            parameters=[{
                'dev': '/dev/input/js0',
                'deadzone': 0.05,
                'autorepeat_rate': 20.0,
            }]
        ),
        Node(
            package='arm_teleop',
            executable='arm_teleop_node',
            name='arm_teleop_node',
            output='screen',
            parameters=[ps4_mapping, ps4_vel_config],
        ),
    ])