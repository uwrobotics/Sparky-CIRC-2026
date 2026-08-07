# groundstation_bringup

## TODO

- [ ] Validate Controller Mapping
- [ ] Update RViz Config

## Launch

```bash
ros2 launch groundstation_bringup groundstation.launch.py
```

### Arguments

| Arg | Default | Values |
|---|---|---|
| `joy_config` | `ps4` | `ps4`, `stadia`, `sn30pro`, `steamdeck`, `none` |

## Satellite map (rviz_satellite)

`rviz/groundstation.rviz` carries an `AerialMap` display that draws OSM tiles
under the rover, anchored on `/vectornav/gnss` from the VN-300.

Two requirements, both easy to miss:

1. **TF.** The display looks up a transform from the Fixed Frame (`odom`) to the
   NavSatFix frame_id (`vectornav`). That link lives in
   `sparky_description/urdf/sparky.sensors.xacro`, so `robot_state_publisher`
   must be running — i.e. the rover's `drivetrain.launch.py` is up.
2. **Tiles.** They download from the public OSM server and cache to
   `~/.cache/rviz_satellite`, which never expires on its own. **Pre-warm the
   cache at the competition site's coordinates while you still have internet** —
   without network and without cache you get an empty map plane.

### What a GNSS failure looks like

rviz_satellite validates every message, so bad GNSS degrades visibly instead of
silently lying:

| Situation | Display status | On screen |
|---|---|---|
| Driver down, nothing on topic | `Warn: No messages received` | No tiles |
| `STATUS_NO_FIX` (no satellites) | `Error: NavSatFix status NO_FIX` | Tiles freeze at last good fix, then fade out over `Timeout` (3 s) |
| lat/lon NaN (INS not converged) | `Error: ...invalid floating point values` | Same as above |
| `vectornav` frame missing from TF | `Error: <tf2 lookup exception>` | No tiles |
| No internet, empty cache | `Error` on tile request | Blank/partial plane, rest of RViz unaffected |

The important guarantee: a dead GNSS **never** drops the map at 0°/0°. Invalid
messages are rejected before they can move the tile origin.

> The saved view is `Distance: 4` because it is tuned for watching the rover
> drive. At 4 m the satellite imagery fills the screen as an unreadable blur —
> scroll out to ~100 m before deciding the map is broken.

### Testing without a VN-300

`scripts/fake_gnss.py` publishes a synthetic `/vectornav/gnss` plus the TF chain,
so you can watch each failure mode on the bench:

```bash
./scripts/fake_gnss.py --tf                             # healthy fix, circling
./scripts/fake_gnss.py --tf --mode nofix                # no satellites
./scripts/fake_gnss.py --tf --mode nan                  # INS not converged
./scripts/fake_gnss.py --tf --mode silent               # driver dead
./scripts/fake_gnss.py --tf --mode dropout              # fix drops/recovers
```

Drop `--tf` when the real drivetrain stack is running, or it will fight
`robot_state_publisher` for the same transforms.

## Configs

`config/<controller>_twist_config.yaml` — stick axes/scales (drive speeds, turbo).
`config/<controller>_mode_config.yaml` — e-stop / auto button mapping.
`config/<controller>_mapping.md` — reference button/axis numbers.

Edit the `ps4_*.yaml` files to tune Sparky's drive behaviour.