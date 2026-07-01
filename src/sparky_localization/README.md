# sparky_localization

State estimation for the Sparky rover using [`robot_localization`](https://github.com/cra-ros-pkg/robot_localization).
Fuses wheel odometry (`diff_drive_controller`) with the VN-300 IMU/GNSS to
produce the REP-105 TF tree `map -> odom -> base_link`.

## Architecture

Standard dual-EKF + navsat_transform pattern:

```
/diff_drive_controller/odom ─┐
/vectornav/imu ──────────────┼─► ekf_local  ─► odom→base_link + /odometry/filtered/local
                             │
/vectornav/gnss ─► navsat_transform ─► /odometry/gps ─┐
/vectornav/imu ──────────────────────────────────────┤
/odometry/filtered/global ───────────────────────────┘
/diff_drive_controller/odom ─┐
/vectornav/imu ──────────────┼─► ekf_global ─► map→odom + /odometry/filtered/global
/odometry/gps ───────────────┘
```

- **`ekf_local`** owns `odom → base_link` — continuous, smooth, **no GPS
  dependency**. This is what compensates wheel-odometry heading drift with the
  IMU. Used for control.
- **`navsat_transform`** converts `NavSatFix` (lat/lon) into map-frame XY.
- **`ekf_global`** owns `map → odom` — drift-corrected global pose for
  navigation (Nav2 GPS waypoints).

## Usage

```bash
# Full stack: local + global EKF + GPS
ros2 launch sparky_localization localization.launch.py

# Local EKF only — no GPS needed (indoors, sensor unplugged, vectornav not
# built). Still produces odom→base_link and drives/visualizes fine.
ros2 launch sparky_localization localization.launch.py use_gps:=false
```

Run alongside the drivetrain and the VN-300 driver:

```bash
ros2 launch drivetrain_bringup drivetrain_can_ps4_rviz.launch.py   # /diff_drive_controller/odom
ros2 launch vectornav vectornav.launch.py                          # /vectornav/imu, /vectornav/gnss
ros2 launch sparky_localization localization.launch.py
```

## Arguments

| Argument       | Default | Purpose                                                        |
|----------------|---------|----------------------------------------------------------------|
| `use_gps`      | `true`  | `true`: dual-EKF + GPS (`map→odom`). `false`: local EKF only.  |
| `use_sim_time` | `false` | Use `/clock` simulated time.                                   |

## Testing without the drivetrain (mock drivetrain + real VN-300)

You can validate plumbing and heading fusion at a desk: **mock** wheel odometry
(faked from `/cmd_vel`) + the **real** VN-300 IMU you move by hand + the EKF, in
RViz. No ODrive/CAN required.

```bash
# Terminal 1 — mock drivetrain + RViz (fixed frame is already 'odom')
ros2 launch drivetrain_bringup drivetrain_rviz.launch.py

# Terminal 2 — real VN-300 driver (needs /dev/ttyUSB0 + dialout access)
ros2 launch vectornav vectornav.launch.py

# Terminal 3 — localization. Indoors there is usually no GPS fix, so:
ros2 launch sparky_localization localization.launch.py use_gps:=false
```

> Because `enable_odom_tf: false`, the mock drivetrain alone no longer publishes
> `odom→base_link` — **the rover only appears in RViz once localization runs.**
> That is the EKF now owning the transform.

**Verify the plumbing:**

```bash
ros2 run tf2_tools view_frames              # odom -> base_link (+ map->odom if use_gps)
ros2 topic hz /vectornav/imu                # sensor flowing
ros2 topic hz /diff_drive_controller/odom   # ~50 Hz
ros2 topic echo /odometry/filtered/local --once
```

**Heading-compensation test (the whole point):**

1. RViz: Fixed Frame = `odom`, add a TF/Axes display for `base_link`.
2. Keep `/cmd_vel` at zero, then **physically rotate the VN-300** — `base_link`
   should rotate to match (yaw is IMU-driven). Confirm numerically:
   `ros2 topic echo /odometry/filtered/local --field pose.pose.orientation`
3. Drive in place — `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.3}}'`
   — `base_link` translates in `odom` (mock wheel odom) while heading still
   tracks the real IMU. That is the fusion working.

**GPS test** (outdoors / with a fix only): launch with `use_gps:=true`, confirm
`ros2 topic echo /vectornav/gnss` shows a fix, `/odometry/gps` appears, and
`view_frames` shows `map -> odom`. Set RViz Fixed Frame = `map`.

Caveat: mock odometry is "perfect" and integrates `/cmd_vel` only — it ignores
the IMU for translation, so the wheel path won't curve when you twist the
sensor. This test validates plumbing + heading, not full trajectory accuracy
(that needs the real rover moving).

## Topics

| Topic                        | Type                     | Direction | Notes                          |
|------------------------------|--------------------------|-----------|--------------------------------|
| `/diff_drive_controller/odom`| `nav_msgs/Odometry`      | in        | wheel odometry                 |
| `/vectornav/imu`             | `sensor_msgs/Imu`        | in        | VN-300 orientation + rates     |
| `/vectornav/gnss`            | `sensor_msgs/NavSatFix`  | in        | VN-300 GNSS (GPS half only)    |
| `/odometry/filtered/local`   | `nav_msgs/Odometry`      | out       | local EKF estimate             |
| `/odometry/filtered/global`  | `nav_msgs/Odometry`      | out       | global EKF estimate            |
| `/odometry/gps`              | `nav_msgs/Odometry`      | out       | GPS in map frame               |

## GPS availability

The stack degrades gracefully without GPS:

- `use_gps:=false` → only `ekf_local` runs. Full `odom→base_link`, zero GPS
  dependency, nothing crashes.
- `use_gps:=true` but no fix / GNSS node down → `ekf_global` dead-reckons from
  odom + IMU; `map→odom` simply stops being corrected. Still no crash.

## Configuration

All EKF and navsat parameters live in [`config/ekf.yaml`](config/ekf.yaml)
(`two_d_mode: true` — Sparky drives on flat ground).

### ⚠️ Must calibrate before trusting GPS waypoints

1. **VN-300 mount transform.** The launch publishes a placeholder static TF
   `base_link → vectornav` at `z=0.3`, no rotation. Measure the real sensor
   pose and update it in [`launch/localization.launch.py`](launch/localization.launch.py)
   — or add a link/joint to `sparky_description` and delete the static publisher.
2. **`yaw_offset` / `magnetic_declination_radians`** in `config/ekf.yaml`. These
   define which way "north" is for GPS. Wrong values make the rover drive off at
   an angle to every waypoint. Verify by driving straight with a fix and
   checking `/odometry/gps` heading matches reality.
3. **IMU frame must be ENU (REP-103)**, not NED — required by
   `robot_localization`. Confirm the VN-300 driver is configured for ENU output.

## Dependencies

Requires the `robot_localization` package (installed via the repo `Dockerfile`:
`ros-humble-robot-localization`).

## Related

- Wheel odometry / `odom→base_link` handoff: `sparky_description`
  (`sparky_controllers.yaml` has `enable_odom_tf: false` so the EKF owns that
  transform — two nodes publishing it is the #1 `robot_localization` bug).
- VN-300 driver: `sensor_vn300` (topics `/vectornav/imu`, `/vectornav/gnss`).
- Next layer: Nav2 GPS waypoint following, which consumes `map→odom` from here.
