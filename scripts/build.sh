#!/bin/bash

echo "Building ROS2 workspace..."

# Source ROS2 environment
source /opt/ros/humble/setup.bash

# Initialize rosdep for current user if needed
if [ ! -f ~/.ros/rosdep/sources.cache ]; then
    echo "Initializing rosdep for user..."
    rosdep update
fi

# Install dependencies.
# Gazebo Classic has no arm64 binaries for ROS Humble (that's why the Dockerfile
# skips the gazebo apt packages on arm64). The only gazebo dependency is
# gazebo_ros in sparky_description (used solely by launch/gazebo.launch.py, which
# isn't run on the robot), so on arm64 we tell rosdep to skip that key instead of
# failing. The package still builds — nothing compiles against gazebo.
ROSDEP_SKIP_KEYS=""
if [ "$(dpkg --print-architecture)" = "arm64" ]; then
    ROSDEP_SKIP_KEYS="--skip-keys gazebo_ros"
    echo "Detected arm64 — skipping Gazebo dependencies: gazebo_ros"
fi
rosdep install --from-paths src --ignore-src -r -y $ROSDEP_SKIP_KEYS

# Build the workspace
colcon build

echo "Build completed!"
echo "To source the workspace, run: source install/setup.bash"