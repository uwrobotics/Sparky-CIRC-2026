# Testing the Sparky drive control (cmd_vel → ros2_control → RViz)

This guide walks through testing the `control.launch.py` pipeline that turns a
`/cmd_vel` twist into per-wheel velocity commands and visualizes the rover
driving in RViz.

```
/cmd_vel ──▶ diff_drive_controller ──▶ 6 wheel velocity commands
                    │                          │
                    │                          ▼
                    │                  mock hardware (mirrors cmd → state)
                    ▼                          │
            odom → base_link TF        joint_state_broadcaster
                    │                          │
                    └──────────┬───────────────┘
                               ▼
                    robot_state_publisher → RViz (wheels spin + rover drives)
```

The default backend is **mock hardware** — no Gazebo, no physics, no real
motors. It mirrors each velocity command to the joint state so RViz shows the
wheels spinning and the rover moving via odometry. (The ODrive/CAN backend is
already stubbed in for later — see the last section.)

---

## 1. Prerequisites

Start the container and allow GUI apps (for RViz), from the **repo root on the host**:

```bash
xhost +local:docker      # let Docker draw to your X server
./run.sh build           # first time / after Dockerfile changes
./run.sh up -d
./run.sh exec ros2-dev bash
```

You should now have a shell **inside the container**, at `/ros2_ws`.

## 2. Build the workspace

Inside the container:

```bash
cd /ros2_ws
./build.sh                       # or: colcon build --packages-select sparky_description
source install/setup.bash
```

## 3. Launch the control stack + RViz

```bash
ros2 launch sparky_description control.launch.py
```

RViz opens with the fixed frame set to `odom`. You'll see the Sparky model,
its TF tree, and a green velocity arrow. The rover is stationary (and the arrow
hidden) until you send a `/cmd_vel`.

> Running headless / no display? Add `rviz:=false` and use the verification
> commands in section 6 to confirm it works.

## 4. Drive it

Pick **one** of the methods below (run in a **second** container shell:
`./run.sh exec ros2-dev bash`, then `source install/setup.bash`).

### A. Quick sanity test — publish a twist directly

```bash
# Forward + left turn
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.3}, angular: {z: 0.4}}'
```

Stop with `Ctrl-C`, then optionally send zeros to halt:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{}'
```

### B. Keyboard teleop

```bash
sudo apt-get install -y ros-humble-teleop-twist-keyboard   # if not present
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Use `i/j/k/l/,` keys to drive. It publishes on `/cmd_vel` by default — no remap
needed.

### C. PS4 / DualShock4 controller

Plug in the controller, then in a second shell:

```bash
ros2 launch akros2_teleop teleop_launch.py joy_config:=ps4
```

This publishes `/cmd_vel` from the left/right sticks (hold **R1** for turbo).
Left stick = linear, right stick X = yaw. See
`src/dualshock4_teleop/config/ps4_mapping.md` for the full button map.

## 5. What you should see

- **In RViz:** all six wheels spin, and the whole rover translates/rotates
  across the grid (driven by the `odom → base_link` transform).
- **Velocity arrow:** a green arrow anchored at the rover points in the travel
  direction, and its **length grows with speed** (≈1 m of arrow per 1 m/s, set
  by the node's `scale` param). It **disappears when the rover stops**.
- Forward-only (`angular.z: 0`) → all wheels spin the same speed, straight line.
- Turning (`angular.z != 0`) → outer wheels spin faster than inner wheels.

## 6. Verify from the command line

```bash
# Both controllers should be "active"
ros2 control list_controllers
#   joint_state_broadcaster ... active
#   diff_drive_controller   ... active

# Wheel joint states update while a cmd_vel is being sent
ros2 topic echo /joint_states --once

# Odometry advances
ros2 topic echo /diff_drive_controller/odom --once

# The drive transform exists and moves
ros2 run tf2_ros tf2_echo odom base_link
```

Expected with `{linear.x: 0.3, angular.z: 0.4}`: left wheels turn slower than
right wheels (left turn), odom `position.x/y` grows, and `tf2_echo` shows a
non-zero translation and yaw.

## 7. Launch options

| Argument            | Default | Purpose                                              |
|---------------------|---------|------------------------------------------------------|
| `use_mock_hardware` | `true`  | `true`: mock (RViz only). `false`: real ODrive/CAN.  |
| `can_interface`     | `can0`  | SocketCAN interface for the ODrive backend.          |
| `rviz`              | `true`  | Launch RViz. Set `false` for headless testing.       |

```bash
# Headless
ros2 launch sparky_description control.launch.py rviz:=false

# Real hardware (later — needs ODrive axes on CAN)
ros2 launch sparky_description control.launch.py use_mock_hardware:=false can_interface:=can0
```

## 8. Tuning the geometry (`config/sparky_controllers.yaml`)

Measured Tasi values are already set:

| Parameter           | Value     | Notes                                          |
|---------------------|-----------|------------------------------------------------|
| `wheel_radius`      | `0.099 m` | Scales odometry distance.                      |
| `wheel_separation`  | `0.969 m` | Front/center axle width. Rear is 0.877 m.      |

`diff_drive_controller` models a single track width; we use the front/center
value. If the rover's reported heading drifts during turns, adjust
`wheel_separation_multiplier`.

## 9. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| RViz window never appears | `xhost +local:docker` on host; check `echo $DISPLAY`. |
| `diff_drive_controller` stuck in `unconfigured`/`inactive` | Check `control_node` output; usually a joint-name mismatch between `sparky_controllers.yaml` and the URDF. |
| Wheels don't move on `/cmd_vel` | Confirm you're publishing to `/cmd_vel` (`ros2 topic info /cmd_vel`); confirm both controllers are `active`. |
| Rover spins/reverses wrong way | Flip `left_wheel_radius_multiplier` / `right_wheel_radius_multiplier` in the yaml. |
| Robot doesn't translate in RViz, only wheels spin | Fixed frame must be `odom` (the provided `control.rviz` sets this); confirm the `odom → base_link` TF exists. |
| No controllers listed | `ros2_control_node` failed to load the URDF/hardware — check the launch terminal for the plugin load error. |

## 10. Real hardware (ODrive over CAN) — later

`urdf/sparky.ros2_control.xacro` already contains the ODrive backend, selected
with `use_mock_hardware:=false`. Each wheel maps to one ODrive axis by
`node_id` (currently placeholders 1–6). Before driving real motors:

1. Confirm the CAN `node_id` per wheel matches the drivetrain wiring.
2. Bring up the CAN interface on the host (`can0`, etc.).
3. Launch with `use_mock_hardware:=false can_interface:=can0`.

Everything downstream (`diff_drive_controller`, teleop, RViz) is unchanged.
