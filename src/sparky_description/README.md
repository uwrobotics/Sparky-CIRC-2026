# sparky_description

URDF description package for the UWRobotics **Sparky 2026** robot (exported from
SolidWorks). Ported to **ROS 2 Humble** (`ament_cmake`).

## Humble Validation (ROS 2)

```bash
./build.sh

source install/setup.bash

ros2 launch sparky_description gazebo.launch.py
ros2 launch sparky_description display.launch.py
```

`display.launch.py` starts `robot_state_publisher`, `joint_state_publisher_gui`,
and `rviz2` (loading `urdf.rviz`).

### Gazebo Classic simulation

```bash
# Requires ros-humble-gazebo-ros-pkgs (pulled in by rosdep)
ros2 launch sparky_description gazebo.launch.py
```

`gazebo.launch.py` launches Gazebo Classic, publishes the robot description,
spawns the model from the `/robot_description` topic, and adds a
`base_link` → `base_footprint` static transform.

## Layout

| Path             | Contents                                        |
|------------------|-------------------------------------------------|
| `urdf/`          | `sparky_description.urdf` + export CSV          |
| `meshes/`        | STL meshes referenced via `package://`          |
| `launch/`        | `display.launch.py`, `gazebo.launch.py`         |
| `config/`        | joint name config                              |
| `rviz/`          | `urdf.rviz` (RViz2 config)                      |
| `archive/`       | Legacy ROS 1 (Noetic) version — see below       |

## Legacy ROS 1 (Noetic)

The original catkin/Noetic version of this package is preserved under
[`archive/`](archive/). See [`archive/README.md`](archive/README.md) for the
ROS 1 build and validation steps.
