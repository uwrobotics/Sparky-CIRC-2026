#!/bin/bash
set -e

# Ensure a ROS 2 DDS domain is always set so multi-machine discovery behaves the
# same on every target (amd64 desktop and the arm64 rover). docker-compose passes
# ROS_DOMAIN_ID via its environment; this default covers containers started
# without it (e.g. a plain `docker run` on the robot). Override by exporting
# ROS_DOMAIN_ID in the environment before launch.
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-47}"

# Source ROS2 setup
source /opt/ros/humble/setup.bash

# If workspace has been built, source it
if [ -f /ros2_ws/install/setup.bash ]; then
    source /ros2_ws/install/setup.bash
fi

# Execute the command
exec "$@"