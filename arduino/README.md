# Arduino LED Controller
# Prerequisites
The NeoDriver Testing Sketch and LED Controller Sketch both use the Adafruit seesaw Library v1.7.9 by Adafruit.

Using the Adafruit seesaw Library as is does not work with the Arduino ESP32 Nano. To fix the compilation issues, the `Adafruit_seesaw.h` file in the library must be edited (On macOS, the location of the library is `~/Documents/Arduino/libraries/Adafruit_seesaw_Library/Adafruit_seesaw.h`). After opening the file, locate these `#includes` near the top of the file:
```cpp
#include "Adafruit_I2CDevice.h"
#include <Arduino.h>
#include <Wire.h>
```
Directly after these `#includes`, add the following code:
```cpp
#ifdef pinMode
#undef pinMode
#endif
#ifdef digitalWrite
#undef digitalWrite
#endif
#ifdef digitalRead
#undef digitalRead
#endif
#ifdef analogRead
#undef analogRead
#endif
#ifdef analogWrite
#undef analogWrite
#endif
#ifdef touchRead
#undef touchRead
#endif
```
Alternatively, replace the currently used `Adafruit_seesaw.h` file with the `Adafruit_seesaw.h` file located in this directory.

# NeoDriver Testing Sketch
The `arduino_neodriver_test.ino` file in this directory is the NeoDriver Testing Sketch. It can be used to check if Arduino, NeoDriver, and LED strip are working properly.

To run the tests, simply upload the code to the Arduino and monitor the Serial Monitor. Test instructions will appear in the Serial Monitor.

Additionally, the following `#define`s can be changed:
- `BOARD_ADDRESS`: Address of the NeoDriver to be tested, usually `0x60`
- `NUM_PIXELS`: Number of pixels to be controlled on the LED strip
- `WAIT`: Wait time between each test in milliseconds

# LED Controller Sketch
The `arduino_led_controller.ino` file in this directory is the LED Controller Sketch, used to control the NeoDriver via UART.

To use the LED controller, upload the sketch to the Arduino and enter commands that comply with the protocol format mentioned below. Ensure Arduino and NeoDriver pins are correctly connected (see **Pins** section below.)

Additionally, the following `#define`s can be changed:
- `BOARD_ADDRESS`: Address of the NeoDriver to be tested, usually `0x60`
- `NUM_PIXELS`: Number of pixels to be controlled on the LED strip
- `MAX_LINE_READS`: 
- `MIN_PIXELS`:

## Pins
Arduino -> NeoDriver:
- 3V3 -> VIN
- GND -> GND
- A4 -> SDA
- A5 -> SCL

Additionally, the Arduino must be connected to a computer via USB-C cable to facilitate communication via UART.

## Controlling the LED Controller
The LED Controller can be controlled using UART via USB-C cable. The following protocol format must be used to enter valid commands.

### Format
The protocol format for the LED controller is as follows:
```
[fid][arg1],[arg2],...,[argn]\n
```
where
- `[fid]`: Function Identifier
- `[argi]`: ith argument to be passed into the function identified by `[fid]`
- `\n`: Terminating character; signifies the end of a command

### `[fid]`
`[fid]`, the Function Identifier parameter, consists of 2 alphabetic characters. Functions to control the LED controller correspond to unique function identifiers.

**e.g.** The Function Identifier `sc` corresponds with the setColour function, which sets the colour of the pixels on the LED strip.

### `[argi]`
Some functions need arguments to execute. Arguments can be passed to functions by appending a comma-separated list of arguments directly after the `fid`. Argument order matters.

**e.g.** The setColour function takes 3 arguments: `r` for the red value (0 - 255), `g` for the green value (0 - 255), and `b` for the blue value (0 - 255). To set the LED strip to a colour with the values `r = 52`, `g = 196`, and `b = 237`, the command is `sc52,196,237` (with the `\n` at the end being implicit).

See the **Commands** section for a list of implemented commands.

A command with insufficient arguments will not execute. A command with more arguments than needed will execute, using only the first `n` arguments, where `n` is the amount of arguments needed for a given command.

Argument type matters. If an argument is signified as an `Int`, then the argument must only be digits, otherwise the command will not execute. For `Int` arguments with bounded values (e.g. 0 - 255), numbers outside the specified range will be clamped and the command will still execute.

### Commands
The following is a list of implemented commands:

#### `sc` - setColour
**Description:** Sets the colour of the LED pixels.

**Arguments (3):**
- `r` (Int, 0 - 255): The red value of the colour
- `g` (Int, 0 - 255): The green value of the colour
- `b` (Int, 0 - 255): The blue value of the colour

**Examples:**
- `sc255,255,255`: Sets the LED pixels to the colour WHITE
- `sc0,0,0`: Turns the LED pixels OFF

#### `sb` - setBrightness
**Description:** Sets the brightness of the LED pixels.

**Arguments (1):**
- `b` (Int, 0 - 255): The new brightness value

**Examples:**
- `sb20`: Dims to brightness of the LED pixels

#### `sl` - setLength
**Description:** Sets the number of pixels that the NeoDriver controls, starting with the pixel directly connected to the NeoDriver. When setting a new length less than the current length, pixels no longer controlled by the NeoDriver will retain their most recent state.

**Arguments (1):**
- `n` (Int, min: 0): Number of pixels to control on the LED strip, starting from the pixel directly connected to the NeoDriver

**Examples:**
- `sl6`: Control the first 6 pixels
- `sl1`: Control only the first pixel