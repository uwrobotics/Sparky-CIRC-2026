# groundstation_bringup

## Launch

```bash
ros2 launch groundstation_bringup teleop_launch.py            # defaults to ps4
ros2 launch groundstation_bringup teleop_launch.py joy_config:=stadia

# Full ground station (teleop + RViz); add network_viz:=true for the link monitor
ros2 launch groundstation_bringup groundstation.launch.py
```

### Arguments

| Arg | Default | Values |
|---|---|---|
| `joy_config` | `ps4` | `ps4`, `stadia`, `sn30pro`, `steamdeck`, `none` |
| `executor` | `True` | `True` = combined `teleop_node`; `False` = `twist_mixer` + `joy_mode_handler` separately |

## Network quality monitor

`ros_network_viz` is a GUI that walks the ROS 2 graph and shows, per topic, the
live publish rate (Hz), bandwidth and QoS — a quick read on the wireless link to
the rover. Bring it up alongside teleop + RViz:

```bash
ros2 launch groundstation_bringup groundstation.launch.py network_viz:=true
```

Or run it standalone (any sourced shell on the ground station):

```bash
ros2 run ros_network_viz ros_network_viz
```

Needs an X display (same as RViz) and multi-machine DDS discovery working so it
can see the rover's nodes/topics.

## Configs

`config/<controller>_twist_config.yaml` — stick axes/scales (drive speeds, turbo).
`config/<controller>_mode_config.yaml` — e-stop / auto button mapping.
`config/<controller>_mapping.md` — reference button/axis numbers.

Edit the `ps4_*.yaml` files to tune Sparky's drive behaviour.