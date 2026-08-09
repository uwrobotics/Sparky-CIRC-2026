# uart_arduino_communicator

Sends UART messages to an Arduino Nano ESP32 over its USB-C cable.

The node forwards every `std_msgs/String` it receives on `uart_tx` to the
Arduino as ASCII text terminated by `\n`. It sends nothing on its own — every
byte on the wire comes from a message published on that topic.

On the rover, `drivetrain_bringup` remaps `uart_tx` to `/antenna/uart_tx`, where
`antenna_teleop` publishes the groundstation button commands.

## Parameters

| Parameter       | Type   | Default        | Description                                   |
|-----------------|--------|----------------|-----------------------------------------------|
| `port`          | string | `/dev/ttyACM0` | Serial device the board enumerates as         |
| `baudrate`      | int    | `115200`       | Must match `Serial.begin()` in the sketch     |
| `startup_delay` | double | `2.0`          | Pause after opening the port, before the first send |

## Build and run

```bash
colcon build --packages-select uart_arduino_communicator
source install/setup.bash

ros2 run uart_arduino_communicator UAC_node
ros2 run uart_arduino_communicator UAC_node --ros-args -p port:=/dev/ttyUSB0
```

Send a command by hand to check the link:

```bash
ros2 topic pub --once /uart_tx std_msgs/String "{data: 'pd6,25'}"
```

## Notes

- **The Nano ESP32 reboots when the USB CDC port is opened**, and anything sent
  during that window is lost. `startup_delay` covers the reboot; raise it if the
  first command published after startup does not arrive.
- **Permissions:** the user must be in the `dialout` group
  (`sudo usermod -aG dialout $USER`, then log out and back in). In Docker, pass
  the device through with `--device=/dev/ttyACM0`.
- **Port name:** the Nano ESP32 usually appears as `/dev/ttyACM0`. If the node
  fails to open it, it logs every serial port it can see — check that list.
