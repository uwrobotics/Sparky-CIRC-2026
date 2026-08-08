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
| `can_interface`     | `can0`  | SocketCAN interface for the ODrive backend.  |