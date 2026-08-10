# uart_arduino_communicator

Two-way bridge between ROS and an Arduino Nano ESP32 over its USB-C cable.

| Direction | Topic | Behaviour |
|---|---|---|
| ROS → board | `uart_tx` (sub) | Each `std_msgs/String` is written as ASCII terminated by `\n` |
| board → ROS | `uart_rx` (pub) | Each line the board prints is republished as a `std_msgs/String` |

The node sends nothing on its own — every byte on the wire comes from a message
published on `uart_tx`. Both directions live in one node on purpose: a serial
port has a single owner, and a second process reading the same tty would steal
an arbitrary share of the bytes.

On the rover, `drivetrain_bringup` remaps these to `/antenna/uart_tx` (where
`antenna_teleop` publishes the groundstation button commands) and
`/antenna/uart_rx`.

`uart_rx` is the only view of whether the board is alive: the sketch echoes
every command it decodes and reports what it did with it, so a silent
`/antenna/uart_rx` while commands are being sent means the board is wedged, not
the link.

## Parameters

| Parameter       | Type   | Default        | Description                                   |
|-----------------|--------|----------------|-----------------------------------------------|
| `port`          | string | `/dev/ttyACM0` | Serial device the board enumerates as         |
| `baudrate`      | int    | `115200`       | Must match `Serial.begin()` in the sketch     |
| `startup_delay` | double | `2.0`          | Pause after opening the port, before the first send |
| `rx_poll_rate`  | double | `50.0`         | Hz the serial input buffer is drained at      |
| `log_rx`        | bool   | `true`         | Also log each received line at INFO           |

## Build and run

```bash
colcon build --packages-select uart_arduino_communicator
source install/setup.bash

ros2 run uart_arduino_communicator UAC_node
ros2 run uart_arduino_communicator UAC_node --ros-args -p port:=/dev/ttyUSB0
```

Send a command by hand and watch the board answer:

```bash
ros2 topic echo /uart_rx                                          # in one shell
ros2 topic pub --once /uart_tx std_msgs/String "{data: 'pd6,25'}" # in another
```

A healthy board echoes the command back and reports what it did, e.g.
`receieveUART: Received: pd6,25` followed by `setDutyCycle: ...`.

## Notes

- **The Nano ESP32 reboots when the USB CDC port is opened**, and anything sent
  during that window is lost. `startup_delay` covers the reboot; raise it if the
  first command published after startup does not arrive.
- **Permissions:** the user must be in the `dialout` group
  (`sudo usermod -aG dialout $USER`, then log out and back in). In Docker, pass
  the device through with `--device=/dev/ttyACM0`.
- **Port name:** the Nano ESP32 usually appears as `/dev/ttyACM0`. If the node
  fails to open it, it logs every serial port it can see — check that list.
