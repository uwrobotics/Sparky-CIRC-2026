import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg = get_package_share_directory("arm_description")
    urdf_file = os.path.join(pkg, "urdf", "dummy_urdf.urdf")
    rviz_config = os.path.join(pkg, 'config', 'arm_display.rviz')

    with open(urdf_file, "r") as f:
        robot_description = f.read()

    return LaunchDescription(
        [
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                arguments=['-d', rviz_config]
            ),
        ]
    )
