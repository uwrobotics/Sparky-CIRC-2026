from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
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
            name='arm_teleop',
            output='screen',
            parameters=[{
                'max_velocity_slow': 0.5,
                'max_velocity_fast': 1.5,
                'deadband': 0.08,
                'dpad_velocity': 0.3,
                'gripper_velocity': 0.5,
            }]
        ),
    ])