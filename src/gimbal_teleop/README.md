# gimbal_teleop

D-pad control of the SIYI gimbal for the Sparky rover.

`gimbal_joy_node` subscribes to `/joy` and publishes `siyi_msgs/GimbalRateCmd`
on `/siyi/cmd/rate`, the rate-command path that `siyi_node` (launched on the
rover by `drivetrain_bringup`) already listens on. Holding a D-pad direction
slews the gimbal at a constant rate; releasing it stops.

| Input | Action |
|-------|--------|
| D-pad left / right | Yaw at `yaw_rate_dps` |
| D-pad up / down | Pitch at `pitch_rate_dps` |

## Run

It comes up with the ground station by default:

```bash
ros2 launch groundstation_bringup groundstation.launch.py
ros2 launch groundstation_bringup groundstation.launch.py use_gimbal_teleop:=false
```

Standalone (anywhere on the same `ROS_DOMAIN_ID` as `siyi_node` and `joy_node`):

```bash
ros2 launch gimbal_teleop gimbal_teleop.launch.py
```

## Parameters

Defaults live in [config/ps4_gimbal_config.yaml](config/ps4_gimbal_config.yaml).

| Parameter | Default | Description |
|-----------|---------|-------------|
| `yaw_axis` | `6` | Joy axis for D-pad left/right |
| `pitch_axis` | `7` | Joy axis for D-pad up/down |
| `yaw_rate_dps` | `30.0` | Yaw slew rate while held (deg/s) |
| `pitch_rate_dps` | `30.0` | Pitch slew rate while held (deg/s) |
| `invert_yaw` | `false` | Flip if yaw goes the wrong way |
| `invert_pitch` | `false` | Flip if pitch goes the wrong way |
| `axis_threshold` | `0.5` | Magnitude counted as "pressed" |
| `publish_rate_hz` | `20.0` | Rate the held command is repeated at |
| `zero_hold_s` | `0.5` | Zero-rate commands sent after release |
| `joy_timeout_s` | `0.5` | Stop the gimbal if `/joy` goes quiet |
| `enable_button` | `-1` | Deadman button; `-1` disables the check |

The axis indices match the Linux joystick layout the PS4 pad reports here —
8 axes, D-pad last. If `ros2 topic echo /joy` shows the D-pad as *buttons*
(the SDL layout, buttons 11–14), this node needs the axis form; check the
`joy_node` device and driver rather than re-mapping.

## Notes

- `siyi_node` runs its own 200 ms watchdog on `/siyi/cmd/rate`, and clamps
  motion at the gimbal's mechanical limits, so a lost command stream stops
  the gimbal on the rover side too.
- Rate commands are ignored while tracking is disabled:
  `ros2 service call /siyi/tracking/enable std_srvs/srv/SetBool "{data: true}"`.
