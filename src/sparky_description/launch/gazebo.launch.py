import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg = get_package_share_directory('sparky_description')

    # Process the Gazebo overlay xacro: it includes the pristine SolidWorks URDF
    # and adds sim-only tags (e.g. <static>). xacro emits a clean document, so no
    # XML encoding-declaration stripping is needed for spawn_entity.
    xacro_file = os.path.join(pkg, 'urdf', 'sparky.gazebo.xacro')
    robot_description = xacro.process_file(xacro_file).toxml()

    # Gazebo Classic needs the install share dir on its resource path to resolve the
    # `package://sparky_description/meshes/...` mesh URIs. Without this the model
    # spawns but renders empty (RViz2 has its own resolver, so RViz works regardless).
    install_share = os.path.dirname(pkg)  # <prefix>/share
    set_gazebo_model_path = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH',
        value=install_share + os.pathsep + os.environ.get('GAZEBO_MODEL_PATH', ''),
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')
        )
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}],
    )

    # Spawn the robot in Gazebo from the /robot_description topic.
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'sparky'],
        output='screen',
    )

    return LaunchDescription([
        set_gazebo_model_path,
        gazebo,
        robot_state_publisher,
        spawn_entity,
    ])
