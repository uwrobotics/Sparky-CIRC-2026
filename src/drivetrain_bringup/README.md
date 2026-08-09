# drivetrain_bringup

## Usage

### RViz + optional teleop (`drivetrain_rviz.launch.py`)
```bash
# Mock hardware + RViz (visualization only)
ros2 launch drivetrain_bringup drivetrain_rviz.launch.py

# Add PS4 teleop so a controller drives the rover
ros2 launch drivetrain_bringup drivetrain_rviz.launch.py teleop:=true

# Real ODrive hardware over CAN (later)
ros2 launch drivetrain_bringup drivetrain_rviz.launch.py use_mock_hardware:=false can_interface:=can2
```

### Headless hardware bringup (`drivetrain.launch.py`)
```bash
# Launch ODrive Hardware
ros2 launch drivetrain_bringup drivetrain.launch.py

# Launch Mock Hardware
ros2 launch drivetrain_bringup drivetrain.launch.py use_mock_hardware:=true
```

## Arguments

### `drivetrain_rviz.launch.py`
| Argument            | Default | Purpose                                              |
|---------------------|---------|------------------------------------------------------|
| `use_mock_hardware` | `true`  | `true`: mock (RViz only). `false`: real ODrive/CAN.  |
| `can_interface`     | `can0`  | SocketCAN interface for the ODrive backend.          |
| `rviz`              | `true`  | Launch RViz.                                         |
| `teleop`            | `false` | Also launch PS4/joystick teleop (publishes `/cmd_vel`). |
| `joy_config`        | `ps4`   | Controller profile: `ps4`, `stadia`, `sn30pro`, `steamdeck`. |

### `drivetrain.launch.py`
| Argument            | Default | Purpose                                      |
|---------------------|---------|-----------------------------------------------|
| `use_mock_hardware` | `true`  | `true`: DevHost. `false`: real ODrive/CAN.   |
| `can_interface`     | `can2`  | SocketCAN interface for the ODrive backend.  |
| `use_imu`           | `true`  | Run the VectorNav VN-300 GNSS/INS driver.    |
| `use_gimbal`        | `true`  | Run SIYI gimbal control/telemetry (`siyi_node`). |
| `gimbal_host`       | `192.168.144.25` | SIYI gimbal IP on the rover-side network. |

`use_gimbal` starts `siyi_node`, which holds the UDP control link to the gimbal
and is the only subscriber of `/siyi/cmd/rate` — the topic `gimbal_teleop`
publishes from the groundstation D-pad. Without it the D-pad does nothing.

The RTSP camera stream is separate and lives on the groundstation:

```bash
ros2 launch groundstation_bringup siyi_camera_launch.py
```
