# antenna_teleop

Button control of the tracking antenna for the Sparky rover.

`antenna_joy_node` subscribes to `/joy` and publishes `std_msgs/String` commands
on `/antenna/uart_tx`. On the rover, `uart_arduino_communicator` (launched by
`drivetrain_bringup`) subscribes to that topic and writes each string to the
antenna's Arduino over USB serial.

| Input | Command sent | Meaning |
|-------|--------------|---------|
| Button 4 | `pd6,75` | Antenna left |
| Button 2 | `pd8,75` | Antenna right |

One command is sent per press, on the rising edge. `joy_node` runs with
`autorepeat_rate: 20.0`, so `/joy` keeps arriving while a button is held; a
level check instead of an edge check would send 20 commands a second.

## Run

It comes up with the ground station by default:

```bash
ros2 launch groundstation_bringup groundstation.launch.py
ros2 launch groundstation_bringup groundstation.launch.py use_antenna_teleop:=false
```

Standalone (anywhere on the same `ROS_DOMAIN_ID` as `joy_node` and the rover):

```bash
ros2 launch antenna_teleop antenna_teleop.launch.py
```

## Parameters

| Parameter       | Default  | Description                          |
|-----------------|----------|--------------------------------------|
| `left_button`   | `4`      | `Joy.buttons` index for left         |
| `right_button`  | `2`      | `Joy.buttons` index for right        |
| `left_command`  | `pd6,75` | String sent when left is pressed     |
| `right_command` | `pd8,75` | String sent when right is pressed    |

Defaults live in [config/ps4_antenna_config.yaml](config/ps4_antenna_config.yaml).

Per [ps4_mapping.md](../groundstation_bringup/config/ps4_mapping.md), button 4
is Share and button 2 is Square. If you meant the D-pad, those are 13 (left) and
14 (right) — change the two indices in the config.

## Checking it

```bash
ros2 topic echo /joy                 # confirm which index your buttons report
ros2 topic echo /antenna/uart_tx     # confirm commands are published
```
