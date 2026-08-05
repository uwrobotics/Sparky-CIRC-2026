import os
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_move_group_launch


def generate_launch_description():
    urdf_path = os.path.join(
        get_package_share_directory("arm_description"),
        "urdf",
        "dummy_urdf.urdf",
    )

    moveit_config = (
        MoveItConfigsBuilder("dummy_urdf", package_name="arm_moveit_config")
        .robot_description(file_path=urdf_path)
        .robot_description_semantic(file_path="srdf/dummy_urdf.srdf")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .planning_pipelines(pipelines=["ompl"])
        .to_moveit_configs()
    )

    return generate_move_group_launch(moveit_config)