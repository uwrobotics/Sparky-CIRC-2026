# drivetrain_bringup

Top-level bringup for the UWRobotics **Sparky** drivetrain. One launch file
starts the `ros2_control` stack (`diff_drive_controller`), `robot_state_publisher`,
the velocity-arrow marker, and RViz — and optionally the PS4 teleop — so a
`/cmd_vel` drives the rover in RViz.

It composes the launch files that already live in:
- `sparky_description/control.launch.py` — control stack + RViz visualization
- `groundstation_bringup/teleop_launch.py` — PS4/joystick teleop

## Usage

```bash
# Mock hardware + RViz (visualization only)
ros2 launch drivetrain_bringup drivetrain_rviz.launch.py

# Add PS4 teleop so a controller drives the rover
ros2 launch drivetrain_bringup drivetrain_rviz.launch.py teleop:=true

# Real ODrive hardware over CAN (later)
ros2 launch drivetrain_bringup drivetrain_rviz.launch.py use_mock_hardware:=false can_interface:=can0
```

Without teleop, drive it from a second shell:

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.3}, angular: {z: 0.4}}'
```

## Arguments

| Argument            | Default | Purpose                                              |
|---------------------|---------|------------------------------------------------------|
| `use_mock_hardware` | `true`  | `true`: mock (RViz only). `false`: real ODrive/CAN.  |
| `can_interface`     | `can0`  | SocketCAN interface for the ODrive backend.          |
| `rviz`              | `true`  | Launch RViz.                                         |
| `teleop`            | `false` | Also launch PS4/joystick teleop (publishes `/cmd_vel`). |
| `joy_config`        | `ps4`   | Controller profile: `ps4`, `stadia`, `sn30pro`, `steamdeck`. |

See `sparky_description/TESTING_CONTROL.md` for the full test walkthrough,
verification commands, and troubleshooting.
