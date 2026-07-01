# Copyright 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License").
#
# Sparky state estimation: robot_localization dual-EKF + navsat_transform.
#
# Runs on the rover alongside drivetrain_bringup. It consumes wheel odometry
# from diff_drive_controller and the VN-300 IMU/GNSS, and owns the REP-105 TF
# tree:
#
#   ekf_local   : /diff_drive_controller/odom + /vectornav/imu
#                 -> odom -> base_link   (continuous, NO GPS dependency)
#   navsat_transform + ekf_global : adds /vectornav/gnss
#                 -> map -> odom         (drift-corrected, needs a GPS fix)
#
# IMPORTANT: diff_drive_controller must NOT also publish odom->base_link, or it
# will fight ekf_local for that transform. Set enable_odom_tf: false in
# sparky_description/config/sparky_controllers.yaml (already done in this repo).
#
# Usage:
#   # Full stack (default): local + global EKF + GPS
#   ros2 launch sparky_localization localization.launch.py
#
#   # No GPS (indoors / sensor unplugged / vectornav not built): local EKF only.
#   # Drives and visualizes fine; just no map->odom correction.
#   ros2 launch sparky_localization localization.launch.py use_gps:=false

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_gps = LaunchConfiguration('use_gps')
    use_sim_time = LaunchConfiguration('use_sim_time')

    ekf_config = PathJoinSubstitution(
        [FindPackageShare('sparky_localization'), 'config', 'ekf.yaml'])

    declared_args = [
        DeclareLaunchArgument(
            'use_gps', default_value='true',
            description='true: full dual-EKF + GPS (map->odom). '
                        'false: local EKF only (odom->base_link, no GPS needed).'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock simulated time.'),
    ]

    # Static mount transform base_link -> vectornav (VN-300 sensor frame).
    # TODO: measure the real offset/orientation of the VN-300 on the rover and
    # update these values (meters / radians). Better: add a <link>/<joint> to
    # sparky_description and delete this, so the URDF is the single source.
    sensor_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_vectornav',
        arguments=['--x', '0.0', '--y', '0.0', '--z', '0.3',
                   '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                   '--frame-id', 'base_link', '--child-frame-id', 'vectornav'],
    )

    # LOCAL EKF: odom -> base_link. Always runs, never needs GPS.
    ekf_local = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_local',
        output='screen',
        parameters=[ekf_config, {'use_sim_time': use_sim_time}],
        remappings=[('odometry/filtered', '/odometry/filtered/local')],
    )

    # GPS half: navsat_transform + global EKF (map -> odom). Opt-in via use_gps.
    gps_group = GroupAction(
        condition=IfCondition(use_gps),
        actions=[
            Node(
                package='robot_localization',
                executable='navsat_transform_node',
                name='navsat_transform',
                output='screen',
                parameters=[ekf_config, {'use_sim_time': use_sim_time}],
                remappings=[
                    ('imu', '/vectornav/imu'),
                    ('gps/fix', '/vectornav/gnss'),
                    # Feed the GLOBAL (map-frame) estimate back in.
                    ('odometry/filtered', '/odometry/filtered/global'),
                    ('odometry/gps', '/odometry/gps'),
                    ('gps/filtered', '/gps/filtered'),
                ],
            ),
            Node(
                package='robot_localization',
                executable='ekf_node',
                name='ekf_global',
                output='screen',
                parameters=[ekf_config, {'use_sim_time': use_sim_time}],
                remappings=[('odometry/filtered', '/odometry/filtered/global')],
            ),
        ],
    )

    return LaunchDescription(declared_args + [sensor_tf, ekf_local, gps_group])
