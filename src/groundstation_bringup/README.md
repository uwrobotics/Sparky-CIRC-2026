# groundstation_bringup

## Launch

```bash
ros2 launch groundstation_bringup teleop_launch.py            # defaults to ps4
ros2 launch groundstation_bringup teleop_launch.py joy_config:=stadia
```

### Arguments

| Arg | Default | Values |
|---|---|---|
| `joy_config` | `ps4` | `ps4`, `stadia`, `sn30pro`, `steamdeck`, `none` |
| `executor` | `True` | `True` = combined `teleop_node`; `False` = `twist_mixer` + `joy_mode_handler` separately |

## Configs

`config/<controller>_twist_config.yaml` — stick axes/scales (drive speeds, turbo).
`config/<controller>_mode_config.yaml` — e-stop / auto button mapping.
`config/<controller>_mapping.md` — reference button/axis numbers.

Edit the `ps4_*.yaml` files to tune Sparky's drive behaviour.