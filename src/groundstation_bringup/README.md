# groundstation_bringup

## TODO

- [ ] Validate Controller Mapping

## Launch

```bash
ros2 launch groundstation_bringup groundstation.launch.py
ros2 launch groundstation_bringup groundstation.launch.py joy_config:=stadia
```

### Arguments

| Arg | Default | Values |
|---|---|---|
| `joy_config` | `ps4` | `ps4`, `stadia`, `sn30pro`, `steamdeck`, `none` |
| `use_gimbal_teleop` | `true` | Drive the SIYI gimbal with the controller D-pad. |
| `use_camera` | `false` | Decode the SIYI RTSP feed into ROS image topics. |
| `camera_host` | `192.168.144.25` | SIYI camera IP from the groundstation. |

The camera feed is no longer displayed in RViz, so `use_camera` is off by
default; set it to `true` if you want the image topics for another viewer.

## Configs

`config/<controller>_twist_config.yaml` — stick axes/scales (drive speeds, turbo).
`config/<controller>_mode_config.yaml` — e-stop / auto button mapping.
`config/<controller>_mapping.md` — reference button/axis numbers.

Edit the `ps4_*.yaml` files to tune Sparky's drive behaviour.