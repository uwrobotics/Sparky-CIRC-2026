from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='arm_teleop',
            executable='arm_reach_game_node',
            name='arm_reach_game_node',
            output='screen',
        ),
    ])