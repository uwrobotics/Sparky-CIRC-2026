#!/bin/bash
set -e

# Source ROS2 setup
source /opt/ros/humble/setup.bash

# If workspace has been built, source it
if [ -f /ros2_ws/install/setup.bash ]; then
    source /ros2_ws/install/setup.bash
fi

# Execute the command
exec "$@"