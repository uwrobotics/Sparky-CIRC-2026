# Sparky CIRC 2026 

This is the CIRC competition ready repository for UWRobotics Season 2026. This
repository contains code needed for the groundstation, drivetrain and other
related modules.

## TODO

- [ ] VCAN ODrive Support
- [x] Ros_Odrive rover integration
- [ ] VN-300 Driver
- [ ] IMU Drift Compensation
- [ ] Camera Ethernet
- [ ] Back-up RF
- [ ] Unit test
- [ ] Application test

## Project Structure
```
./
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Container orchestration (base, works on Ubuntu)
├── scripts/                # Shell scripts
│   ├── setup.sh            # Host-side: detects UID/GID, prepares .env
│   ├── docker-entrypoint.sh# Container startup script
│   └── build.sh            # Build script for ROS2 workspace
├── src/                    # ROS2 source code
└── README.md               # This file
```

### Prerequisites

```bash
# Setup the ENV
./scripts/setup.sh
```

**Linux Only: Grant Docker access to your X server:**
```bash
xhost +local:docker
```

### Setup Docker

```bash
# In Project Root
docker compose build
docker compose up -d

# Enter the docker container
docker compose exec ros2-dev bash

# Remove the docker container
docker compose down
```

### ROS Package

```bash
# Build the ROS Package
./build.sh

# Source the ENV
source install/setup.bash

# Launch
ros2 launch <ROS_PKG> <ROS_LAUNCH> 
```

---

```
sudo ip addr add 192.168.144.100/24 dev enP8p1s0
ip addr
ip route get 192.168.144.25
ping 192.168.144.25
```

### SIYI Gimbal-Camera (A8 mini)

The SIYI A8 mini streams H.265 video over RTSP and is driven by the `siyi_ros2`
submodule + the `siyi_sdk` pip package (both installed in the Dockerfile).

**Network:** the camera is at `192.168.144.25`. The host/container must have an IP
on that subnet and be able to reach it. On a wired interface:
```bash
sudo ip addr add 192.168.144.100/24 dev <iface>   # e.g. enp0s31f6
ping 192.168.144.25                                # confirm reachability
gst-launch-1.0 rtspsrc location=rtsp://192.168.144.25:8554/main.264 latency=0 \
  ! rtph265depay ! h265parse ! avdec_h265 ! videoconvert \
  ! autovideosink sync=false

sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-{base,good,bad,ugly} gstreamer1.0-libav
```

**Launch (use the wrapper — do NOT call the upstream launch bare):**
```bash
ros2 launch drivetrain_bringup siyi_camera.launch.py
```
The wrapper forces `camera_model:=a8`. This matters: the upstream
`siyi_ros2/siyi_full.launch.py` defaults `camera_model` to `zt30`, which
overrides the `a8` in `camera_params.yaml` and builds the wrong RTSP URL
(`.../video1`, new-gen) instead of the A8's `rtsp://192.168.144.25:8554/main.264`
(old-gen) — the result is a silent 404 and no video.

**Published topics:**
- `/siyi/image_raw` (`sensor_msgs/Image`)
- `/siyi/image_compressed` (`sensor_msgs/CompressedImage`) — lighter over the robot↔groundstation link
- `/siyi/camera_info`

**Viewing in RViz2:**
1. `rviz2`, then **Add → Image**, set **Topic** to `/siyi/image_raw`.
2. **Important:** the publisher uses **BEST_EFFORT** QoS. Expand the display's
   **Topic → Reliability Policy** and set it to **Best Effort**, or RViz stays
   blank even though the topic exists.
3. Cross-machine (RViz on groundstation, node on robot): both must share
   `ROS_DOMAIN_ID` (47, from `.env`) and the Best-Effort QoS above.

Simpler quick-look alternatives:
```bash
ros2 run rqt_image_view rqt_image_view    # pick raw or compressed from the dropdown
ros2 run image_view image_view --ros-args -r image:=/siyi/image_raw -p reliability:=best_effort
```

**Decode backend:** on the generic `osrf/ros:humble-desktop` base the node uses
software H.265 decode (`decodebin` + libav) — no extra packages needed. Hardware
decode (`nvv4l2decoder`) would require an L4T/JetPack base image + the NVIDIA
container runtime, and an upstream codec fix (the SDK's Jetson pipeline is
hardcoded to H.264 while the A8 streams H.265).

**Known issue:** if `siyi_camera_node` aborts at startup on the `gstreamer`
backend (a `python3-opencv`↔PyGObject-GStreamer library conflict), fall back to
the OpenCV backend, which needs no code changes:
```bash
ros2 launch siyi_ros2 siyi_full.launch.py camera_model:=a8 backend:=opencv
```

---

### Debug Info

#### No Gui issue

**Verify `DISPLAY` is set:**
```bash
echo $DISPLAY   # should print :0 or :1
```
If empty, set it manually:
```bash
export DISPLAY=:0
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 UWRobotics.

This repository bundles third-party components under their own licenses (see [NOTICE](NOTICE)):
- `src/ros_odrive` (submodule) — MIT, © ODrive Robotics (see `src/ros_odrive/LICENSE`).
- `src/dualshock4_teleop` (akros2_teleop, submodule) — Apache-2.0, © 2023 Aditya Kamath (see `src/dualshock4_teleop/LICENSE`).
- `src/akros2_msgs` (submodule) — Apache-2.0, © 2023 Aditya Kamath (see `src/akros2_msgs/LICENSE`).
- `src/siyi_ros2` (submodule) — MIT, © Mohamed Abdelkader (declared in `package.xml`; no upstream LICENSE file).
- `src/siyi_msgs` (submodule) — MIT, © Mohamed Abdelkader (declared in `package.xml`; no upstream LICENSE file).
- `siyi_sdk` (pip dependency, installed in the Dockerfile) — MIT, © Mohamed Abdelkader (https://github.com/mzahana/siyi_sdk).
