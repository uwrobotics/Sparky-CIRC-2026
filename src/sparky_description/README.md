# Noetic Validation

```BASH
# Setup Noetic and X11 display
docker pull ros:noetic-robot

xhost +local:docker

docker run -it \
--name testing_ros_urdf \
--net=host \
-e DISPLAY=$DISPLAY \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-v /home/yuchen/codespace/Sparky-CIRC-2026/src/sparky_description/:/root/ws/src/sparky_description \
ros:noetic-robot \
bash

# Build Package
apt-get update
source ros_entrypoint.sh

cd /root/ws
rosdep install --from-paths src --ignore-src -r -y

catkin_make
source /root/ws/devel/setup.bash
export LIBGL_ALWAYS_SOFTWARE=1
export LIBGL_ALWAYS_INDIRECT=0
roslaunch sparky_description display.launch
```

This Noetic version will be stored under /archive