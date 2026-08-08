# Sparky CIRC 2026 -- drivetrain_bringup 
#
# Copyright 2026 UWRobotics

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_mock_hardware = LaunchConfiguration('use_mock_hardware')
    can_interface = LaunchConfiguration('can_interface')
    use_imu = LaunchConfiguration('use_imu')
    use_gimbal = LaunchConfiguration('use_gimbal')
    gimbal_host = LaunchConfiguration('gimbal_host')
    use_antenna = LaunchConfiguration('use_antenna')
    antenna_port = LaunchConfiguration('antenna_port')

    declared_args = [
        DeclareLaunchArgument(
            'use_mock_hardware', default_value='false',
            description='true: DevHost. false: Load ODrive Plugin.'),
        DeclareLaunchArgument(
            'can_interface', default_value='can2',
            description='SocketCAN interface.'),
        DeclareLaunchArgument(
            'use_imu', default_value='true',
            description='Run the VectorNav VN-300 GNSS/INS driver on the rover.'),
        DeclareLaunchArgument(
            'use_gimbal', default_value='true',
            description='Run SIYI gimbal control/telemetry on the rover.'),
        DeclareLaunchArgument(
            'gimbal_host', default_value='192.168.144.25',
            description='SIYI gimbal IP on the rover-side network.'),
        DeclareLaunchArgument(
            'use_antenna', default_value='true',
            description='Run the UART bridge to the tracking antenna Arduino.'),
        DeclareLaunchArgument(
            'antenna_port', default_value='/dev/ttyACM0',
            description='Serial device the antenna Arduino enumerates as.'),
    ]

    drivetrain_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('sparky_description'), 'launch', 'control.launch.py'])),
        launch_arguments={
            'use_mock_hardware': use_mock_hardware,
            'can_interface': can_interface,
        }.items(),
    )

    vectornav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('vectornav'), 'launch', 'vectornav.launch.py'])),
        condition=IfCondition(use_imu),
    )

    # siyi_node holds the UDP:37260 control link to the gimbal and is the only
    # subscriber of /siyi/cmd/rate, which gimbal_teleop publishes from the
    # groundstation D-pad. Without it the D-pad commands go nowhere.
    siyi_gimbal_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('siyi_ros2'), 'launch', 'siyi.launch.py'])),
        launch_arguments={
            'host': gimbal_host,
            'auto_reconnect': 'true',
        }.items(),
        condition=IfCondition(use_gimbal),
    )

    # Holds the serial link to the antenna's Arduino and is the only subscriber
    # of /antenna/uart_tx, which antenna_teleop publishes from the
    # groundstation buttons. Without it those commands go nowhere. The bench
    # test cycle is off so it cannot fight the joystick commands.
    antenna_uart_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('uart_arduino_communicator'), 'launch', 'uart.launch.py'])),
        launch_arguments={
            'port': antenna_port,
            'enable_demo_cycle': 'false',
        }.items(),
        condition=IfCondition(use_antenna),
    )

    return LaunchDescription(declared_args + [
        drivetrain_launch,
        vectornav_launch,
        siyi_gimbal_launch,
        antenna_uart_launch,
    ])
