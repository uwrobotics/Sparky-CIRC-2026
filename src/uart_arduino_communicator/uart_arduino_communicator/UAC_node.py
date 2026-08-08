#!/usr/bin/env python3
"""
ROS 2 node that sends UART messages to an Arduino Nano ESP32 over USB-C (serial).

Forwards every std_msgs/String received on `uart_tx` to the Arduino,
newline-terminated. On the rover, drivetrain_bringup remaps that to
/antenna/uart_tx, which antenna_teleop publishes from the groundstation
controller buttons.

A bench self-test cycle is also built in: INIT_MESSAGE once at startup, then
MESSAGES in a loop every `interval` seconds. It is on by default so
`ros2 run` still exercises the board on its own, and drivetrain_bringup turns
it off so it cannot fight the joystick commands.

Subscribes to: uart_tx (std_msgs/String)

Parameters:
  - port               (string) default: /dev/ttyACM0
  - baudrate           (int)    default: 115200
  - interval           (double) default: 2.5   seconds between cycle messages
  - startup_delay      (double) default: 2.0   pause after opening the port
  - enable_demo_cycle  (bool)   default: True  run the built-in test cycle
"""

import time

import rclpy
from rclpy.node import Node
import serial
import serial.tools.list_ports
from std_msgs.msg import String


class UartSenderNode(Node):
    """Forwards commands from ROS to the Arduino, with an optional bench test cycle."""

    INIT_MESSAGE = 'sc125,0,255'
    MESSAGES = ('sb50', 'sc255,0,0', 'sc0,255,0', 'sc125,0,255')

    def __init__(self):
        super().__init__('uart_sender_node')

        # Parameters
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('interval', 2.5)
        self.declare_parameter('startup_delay', 2.0)
        self.declare_parameter('enable_demo_cycle', True)

        port = self.get_parameter('port').get_parameter_value().string_value
        baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        interval = self.get_parameter('interval').get_parameter_value().double_value
        startup_delay = self.get_parameter('startup_delay').get_parameter_value().double_value
        enable_demo_cycle = self.get_parameter('enable_demo_cycle').value

        # Open serial port
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,
                write_timeout=1.0
            )
            self.get_logger().info(f'Opened {port} @ {baudrate} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port {port}: {e}')
            self.get_logger().info('Available ports:')
            for p in serial.tools.list_ports.comports():
                self.get_logger().info(f'  {p.device} - {p.description}')
            raise

        # The Nano ESP32 reboots when the USB CDC port is opened. Anything sent
        # during that window is lost, so give the board time to come back up.
        if startup_delay > 0.0:
            time.sleep(startup_delay)

        self._send(self.INIT_MESSAGE)

        # Commands from the groundstation. drivetrain_bringup remaps this to
        # /antenna/uart_tx, where antenna_teleop publishes button commands.
        self.subscription = self.create_subscription(
            String, 'uart_tx', self._cb_command, 10)
        self.get_logger().info('Forwarding uart_tx -> serial')

        # Bench self-test: start the cycle immediately, then switch every
        # `interval` seconds.
        if enable_demo_cycle:
            self._index = 0
            self._send_next()
            self.timer = self.create_timer(interval, self._send_next)
            self.get_logger().info(
                f'Demo cycle: {" -> ".join(self.MESSAGES)} every {interval:g} s')

    def _send(self, message):
        """Write a single message to the serial port, newline-terminated."""
        try:
            self.ser.write((message + '\n').encode('utf-8'))
            self.ser.flush()
            self.get_logger().info(f'Sent: "{message}"')
        except serial.SerialException as e:
            self.get_logger().error(f'Serial write failed: {e}')

    def _cb_command(self, msg):
        """Forward a command received from ROS straight to the Arduino."""
        self._send(msg.data)

    def _send_next(self):
        """Send the next message in the cycle and advance the cursor."""
        message = self.MESSAGES[self._index]
        self._index = (self._index + 1) % len(self.MESSAGES)
        self._send(message)

    def destroy_node(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
            self.get_logger().info('Serial port closed')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UartSenderNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
