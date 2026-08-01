# Sparky CIRC 2026 

This is the CIRC competition ready repository for UWRobotics Season 2026. This
repository contains code needed for the groundstation, drivetrain and other
related modules.

## TODO

### CIRC 2026 Before Departure Checklist

- [ ] Check Right Rear ODrive Motor Connection Reliability (Record Incident)
- [ ] Sign-off Drivetrain Functionality (981f76ecb99a64d04853bbb91b574ff5180fc544)
- [x] Gimbal Camera GStreamer to RViz
- [ ] Gimbal Camera Control (NOT SUPPORTED for CIRC 2026)
- [ ] VN-300 IMU Sensor Fusion
- [ ] VN-300 GPS Tracking
- [ ] Aux Board Tracking Antenna Yaw Testing
- [ ] GroundStation Manual Yaw Alignment
- [ ] Aux Board LED Strip Control + Fusing
- [ ] Aux Board Arm SSR Control
- [ ] Arm Main Power Rail Fusing
- [ ] Arm CAN Connectivity Testing
- [ ] Arm ODrive Scale Configuration
- [ ] Arm Ros2 Control Support

### CIRC 2026 Nice to Have

- [ ] Nav2 Waypoint tracking using GPS

### Feature Support
- [ ] VCAN ODrive Support
- [ ] Unit test
- [ ] Application test

<!--
TODO: Add System Requirements
-->

# Architecture Design

```mermaid
flowchart TB

  subgraph BOARD1["Nvidia Jetson Nano(Drivetrain Host)"]
    B1_S1[Driver: ODrive - CAN]
    B1_S2[Driver: VectorNav 300 - USB]
    B1_S3[Driver: Siyi Gimbal Control - Eth]
    B1_S4[Driver: Aux Board - USB]
    B1_S5[Controller: Differential Drive Controller]
    B1_S6[Broadcaster: Joint State Broadcaster]
    B1_S7[Broadcaster: IMU Sensor Broadcaster]
    B1_S8[Localization: Robot Localization]
    %% Planner: NAV 2
  end

  subgraph BOARD2["ESP Arduino Nano(Aux Control)"]
    B2_S1[Driver: Velocity Servo PWM]
    B2_S2[Driver: Adafruit i2c Neopixel EVM]
    B2_S3[Driver: Arm Relay - GPIO]
    B2_S4[Interface: Serial Host Bridge]
  end

  subgraph BOARD3["NVidia Jetson Nano(Arm Host)"]
    B3_S1[Driver: ODrive - CAN]
    B3_S2[Driver: Teledyne Gripper Camera - USB]
    %% Current Implementation (verified in RViz/mock, not yet on hardware)
    B3_S3[Controller: Forward Command Controller]
    B3_S6[Broadcaster: Joint State Broadcaster]
    %% Ideal Implementation
    B3_S4[Controller: Joint Trajectory Controller]
    B3_S5[Controller: Gripper Controller]
    B3_S7[Broadcaster: Pose Broadcaster]
    B3_S8[Planner: MoveIt2] 
  end

  subgraph BOARD4["Generic Linux Device(Ground Station Host)"]
    B4_S1[Driver: Joy - USB/Bluetooth]
    B4_S2[Adapter: Joy Teleoperation]
    B4_S3[Display: TF]
    B4_S4[Display: Sensor Image]
    B4_S5[GUI: RViz]
  end

  %% Network Infra 
  DRV_ETH_BUS[Router]
  Gim_CAM[Siyi A8 Mini Gimbal Camera]
  BOARD1 <--> DRV_ETH_BUS
  BOARD3 <--> DRV_ETH_BUS
  DRV_ETH_BUS <--> Gim_CAM 
  
  WIRELESS_BUS[Access Point]
  DRV_ETH_BUS <--> WIRELESS_BUS

  GS_ETH_BUS[Wired Ethernet]
  BOARD4 <--> GS_ETH_BUS
  WIRELESS_BUS <--> GS_ETH_BUS

  %% Drivetrain Jetson 
  DRV_CAN_BUS[CAN Adapter 1]
  BOARD1 <--> DRV_CAN_BUS

  DRV_USB_INS[VectorNav 300 INS Module]
  BOARD1 <--> DRV_USB_INS 
  BOARD2 <--> BOARD1 
  
  %% Arm Jetson
  ARM_CAN_BUS[CAN Adapter 2]
  ARM_CAN_BUS <--> BOARD3

  ARM_CAM[Teledyne Camera]
  ARM_CAM <--> BOARD3

  %% Arduino Board
  VEL_SERVO[Velocity Servo]
  VEL_SERVO <--> BOARD2

  Neo_EVM[Adafruit I2C NeoPixel Driver]
  Neo_EVM <--> BOARD2

  SSR[Arm Solid State Relay]
  SSR <--> BOARD2

  DRV_CTL[DualShock4 Controller]
  DRV_CTL <--> BOARD4

  ARM_CTL[XBOX Controller]
  ARM_CTL <--> BOARD4

  %%RM_LEROBOT[LeRobot Arm Controller]
```

<!--
TODO: Add Detailed Design for each Module 
  Notes:
    - One D.D. for a ground E.g Controller Group
-->

<!--
TODO: Add Unit Tests List
  Notes:
    - Only Testing Custom Feature
-->

<!--
TODO: Add Qualification Tests Lists
  Feature: 
    - Manual Testing
    - Automated Testing
    - Checklists
    - SOPs
-->

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

**Setup Gimbal Camera Connection**
```bash
sudo ip addr add 192.168.144.100/24 dev <iface>   # e.g. enp0s31f6
ping 192.168.144.25        
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

### Gimbal Camera Direct Connection

```bash
sudo ip addr add 192.168.144.100/24 dev <iface>   # e.g. enp0s31f6
ping 192.168.144.25                                # confirm reachability
gst-launch-1.0 rtspsrc location=rtsp://192.168.144.25:8554/main.264 latency=0 \
  ! rtph265depay ! h265parse ! avdec_h265 ! videoconvert \
  ! autovideosink sync=false

sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-{base,good,bad,ugly} gstreamer1.0-libav
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
- `src/siyi_msgs` (submodule) — MIT, © Mohamed Abdelkader (declared in `package.xml`; upstream ships no LICENSE file).
- `src/siyi_ros2` (submodule) — MIT, © Mohamed Abdelkader (declared in `package.xml`; upstream ships no LICENSE file).
- `siyi_sdk` (not vendored; installed into the Docker image by `Dockerfile`) — MIT, © SIYI SDK Contributors.
- `utils/ros2-migration-tools` (submodule, dev utility) — Apache-2.0, © 2018 Amazon.com, Inc. (see `utils/ros2-migration-tools/LICENSE` and its `NOTICE`).

The Docker image also installs ROS 2 Humble and a GStreamer video stack (LGPL-2.1-or-later,
including `gstreamer1.0-libav`/FFmpeg as packaged by Ubuntu) from upstream archives.
`gstreamer1.0-plugins-ugly` is intentionally excluded — see [NOTICE](NOTICE) before adding it.
