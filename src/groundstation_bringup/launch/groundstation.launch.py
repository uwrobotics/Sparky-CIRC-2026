# Copyright 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License").
#
# Sparky ground station bringup -- the operator-side half of the stack.
#
# Runs on the ground station laptop and provides everything the operator needs:
#   - PS4/joystick teleop (teleop_launch.py) -> publishes /cmd_vel
#   - RViz visualization of the rover
#
# The rover (drivetrain_bringup/drivetrain_can_ps4_rviz.launch.py) runs the
# low-level control headless and publishes the robot model (/robot_description,
# latched) and TF. This RViz pulls those over the network, so no
# robot_state_publisher runs here -- the rover is the single source of truth.
# Multi-machine DDS discovery must be working (see scripts/setup.sh, ROS_NET_IFACE).
#
# Usage:
#   # Teleop + RViz (defaults)
#   ros2 launch groundstation_bringup groundstation.launch.py
#
#   # A different controller profile
#   ros2 launch groundstation_bringup groundstation.launch.py joy_config:=stadia
#
#   # Teleop only, no RViz
#   ros2 launch groundstation_bringup groundstation.launch.py rviz:=false
#
#   # Also open the ROS network visualizer (live per-topic Hz/bandwidth/QoS)
#   ros2 launch groundstation_bringup groundstation.launch.py network_viz:=true

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    joy_config = LaunchConfiguration('joy_config')
    use_rviz = LaunchConfiguration('rviz')
    use_network_viz = LaunchConfiguration('network_viz')

    declared_args = [
        DeclareLaunchArgument(
            'joy_config', default_value='ps4',
            description='Controller profile for teleop: ps4, stadia, sn30pro, steamdeck.'),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='Open RViz to visualize the rover.'),
        DeclareLaunchArgument(
            'network_viz', default_value='false',
            description='Open ros_network_viz to monitor link quality '
                        '(live per-topic rate, bandwidth and QoS over DDS).'),
    ]

    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('groundstation_bringup'), 'launch', 'teleop_launch.py'])),
        launch_arguments={'joy_config': joy_config}.items(),
    )

    # RViz reads the robot model from the /robot_description topic (latched) and
    # TF, both published by the rover's robot_state_publisher over DDS -- see the
    # control.rviz RobotModel display (Description Source: Topic). No local
    # robot_state_publisher is started here.
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', PathJoinSubstitution(
            [FindPackageShare('sparky_description'), 'rviz', 'control.rviz'])],
        condition=IfCondition(use_rviz),
        output='log',
    )

    # ros_network_viz: GUI that walks the ROS graph and shows, per topic, the
    # live publish rate (Hz), bandwidth and QoS settings -- a quick read on how
    # healthy the wireless link to the rover is. Off by default; enable with
    # network_viz:=true. Vendored as a submodule under src/ros_network_viz.
    network_viz_node = Node(
        package='ros_network_viz',
        executable='ros_network_viz',
        name='ros_network_viz',
        condition=IfCondition(use_network_viz),
        output='log',
    )

    return LaunchDescription(declared_args + [
        teleop_launch,
        rviz_node,
        network_viz_node,
    ])
