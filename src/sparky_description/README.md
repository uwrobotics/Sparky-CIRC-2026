# sparky_description

URDF description package for the UWRobotics **Sparky 2026**
robot (exported from SolidWorks). Ported to **ROS 2 Humble**
(`ament_cmake`). Currently support RViZ Rover visualization
and `ros2_control` `diff_drive_controller` mapped to 6 wheel
rocker-bogie configuration. Currently Gazebo support is
incomplete.

## GUI Visualization Demo 

```bash
./build.sh

source install/setup.bash

ros2 launch sparky_description display.launch.py
ros2 launch sparky_description gazebo.launch.py
```

### Drive control (cmd_vel → ros2_control → RViz)

```bash
ros2 launch sparky_description control.launch.py
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.3}, angular: {z: 0.4}}'
```

## Legacy ROS 1 (Noetic)

The original catkin/Noetic version of this package is preserved under
[`archive/`](archive/). See [`archive/README.md`](archive/README.md) for the
ROS 1 build and validation steps.