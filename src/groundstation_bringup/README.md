# groundstation_bringup

Ground station bringup for the UWRobotics **Sparky** rover. This package owns the
teleop **launch files** and **controller configs**, while the actual teleop node
executables (`teleop_node`, `twist_mixer`, `joy_mode_handler`) come from the
[`akros2_teleop`](../dualshock4_teleop) submodule.

Keeping launch + config here means we can tune controller mappings, scales, and
defaults **without modifying the upstream `akros2_teleop` submodule**.

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

## Topics

```
controller -> joy_node -> /joy -> joy_teleop -> /joy_vel ┐
                       joy_mode_handler -> /mode          ┤-> teleop_node -> /cmd_vel
                                       (autonomy) -> /nav_vel ┘
```
