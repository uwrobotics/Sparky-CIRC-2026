This package contains a lifecycle node that publishes RGB values to the `/led_colour` topic and changes behaviour depending on the node's current lifecycle state:

- **on_configure() -** Initializes node's publisher and timer, and publishes the colour yellow once to `/led_colour`
- **on_activate() -** Publishes a random colour every second to the `/led_colour`
- **on_deactivate() -** Publishes the colour red once to `/led_colour`
- **on_cleanup() and on_shutdown() -** Cleans up node's publisher and timer

## Instructions
### Build and Run Package
To build the package, run:
```bash
colcon build --packages-select led_controller
```
Then, source the workspace:
```bash
source install/setup.bash
```
Then, run the LED Colour Controller:
```bash
ros2 run led_controller led_colour_controller
```
### Node Commands
To change the state of the node, run the commands below:
```bash
ros2 lifecycle set led_colour_controller_node configure
ros2 lifecycle set led_colour_controller_node activate
ros2 lifecycle set led_colour_controller_node deactivate
ros2 lifecycle set led_colour_controller_node cleanup
ros2 lifecycle set led_colour_controller_node shutdown
```
To view the output of the node, run:
```bash
ros2 topic echo /led_colour
```