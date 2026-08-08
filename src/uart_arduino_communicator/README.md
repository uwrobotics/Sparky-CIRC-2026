# uart_arduino_communicator

Sends UART messages to an Arduino Nano ESP32 over its USB-C cable.

The node sends `pt10000` once at startup, then cycles through four commands,
switching every 5 seconds:

```
pt10000 -> pd100,0 -> pd75,0 -> pd50,0 -> pd25,0 -> pd100,0 -> ...
```

Each message is sent as ASCII text terminated by `\n`.

## Parameters

| Parameter       | Type   | Default        | Description                                   |
|-----------------|--------|----------------|-----------------------------------------------|
| `port`          | string | `/dev/ttyACM0` | Serial device the board enumerates as         |
| `baudrate`      | int    | `115200`       | Must match `Serial.begin()` in the sketch     |
| `interval`      | double | `5.0`          | Seconds between messages                      |
| `startup_delay` | double | `2.0`          | Pause after opening the port, before the first send |

## Build and run

```bash
colcon build --packages-select uart_arduino_communicator
source install/setup.bash

ros2 run uart_arduino_communicator UAC_node
ros2 run uart_arduino_communicator UAC_node --ros-args -p port:=/dev/ttyUSB0 -p interval:=2.0
```

## Notes

- **The Nano ESP32 reboots when the USB CDC port is opened**, and anything sent
  during that window is lost. `startup_delay` covers the reboot; raise it if the
  first `pt10000` does not arrive.
- **Permissions:** the user must be in the `dialout` group
  (`sudo usermod -aG dialout $USER`, then log out and back in). In Docker, pass
  the device through with `--device=/dev/ttyACM0`.
- **Port name:** the Nano ESP32 usually appears as `/dev/ttyACM0`. If the node
  fails to open it, it logs every serial port it can see — check that list.
