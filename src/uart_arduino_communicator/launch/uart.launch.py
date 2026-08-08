# Sparky CIRC 2026 -- uart_arduino_communicator
#
# Copyright 2026 UWRobotics

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            name='port',
            default_value='/dev/ttyACM0',
            description='Serial device the antenna Arduino enumerates as.'),

        DeclareLaunchArgument(
            name='baudrate',
            default_value='115200',
            description='UART baud rate, must match the Arduino sketch.'),

        DeclareLaunchArgument(
            name='enable_demo_cycle',
            default_value='false',
            description=(
                'Run the built-in bench test cycle. Off here so it cannot '
                'fight the commands coming from antenna_teleop.'),),

        DeclareLaunchArgument(
            name='command_topic',
            default_value='/antenna/uart_tx',
            description='Topic carrying std_msgs/String commands for the Arduino.'),

        Node(
            package='uart_arduino_communicator',
            executable='UAC_node',
            name='uart_sender_node',
            output='screen',
            # Launch substitutions resolve to strings; the node declares
            # baudrate as an int and enable_demo_cycle as a bool, so both need
            # an explicit value_type or the node rejects them at startup.
            parameters=[{
                'port': LaunchConfiguration('port'),
                'baudrate': ParameterValue(
                    LaunchConfiguration('baudrate'), value_type=int),
                'enable_demo_cycle': ParameterValue(
                    LaunchConfiguration('enable_demo_cycle'), value_type=bool),
            }],
            remappings=[('uart_tx', LaunchConfiguration('command_topic'))]),
    ])
