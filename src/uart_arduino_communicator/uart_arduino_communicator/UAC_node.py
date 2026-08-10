#!/usr/bin/env python3
"""
ROS 2 node that sends UART messages to an Arduino Nano ESP32 over USB-C (serial).

Forwards every std_msgs/String received on `uart_tx` to the Arduino,
newline-terminated. On the rover, drivetrain_bringup remaps that to
/antenna/uart_tx, which antenna_teleop publishes from the groundstation
controller buttons.

The node sends nothing on its own; every byte on the wire comes from a message
published on the topic.

Anything the Arduino prints back is republished line by line on `uart_rx`. The
sketch echoes every command it decodes ("receieveUART: Received: ...") and
reports what it did with it, so this is the only view of whether the board is
actually alive and parsing. Both directions live in this one node because a
serial port has a single owner: a second process reading the same tty would
steal an arbitrary share of the bytes.

Subscribes to: uart_tx (std_msgs/String)
Publishes to:  uart_rx (std_msgs/String), one message per line received

Parameters:
  - port               (string) default: /dev/ttyACM0
  - baudrate           (int)    default: 115200
  - startup_delay      (double) default: 2.0   pause after opening the port
  - rx_poll_rate       (double) default: 50.0  Hz the input buffer is drained at
  - log_rx             (bool)   default: True  also log each received line
"""

import time

import rclpy
from rclpy.node import Node
import serial
import serial.tools.list_ports
from std_msgs.msg import String


class UartSenderNode(Node):
    """Bridges ROS and the Arduino in both directions over one serial port."""

    # Longest run of bytes tolerated without a line ending before it is dropped.
    MAX_LINE_BYTES = 4096

    def __init__(self):
        super().__init__('uart_sender_node')

        # Parameters
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('startup_delay', 2.0)
        self.declare_parameter('rx_poll_rate', 50.0)
        self.declare_parameter('log_rx', True)

        port = self.get_parameter('port').get_parameter_value().string_value
        baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        startup_delay = self.get_parameter('startup_delay').get_parameter_value().double_value
        rx_poll_rate = self.get_parameter('rx_poll_rate').get_parameter_value().double_value
        self._log_rx = self.get_parameter('log_rx').value

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

        # Commands from the groundstation. drivetrain_bringup remaps this to
        # /antenna/uart_tx, where antenna_teleop publishes button commands.
        self.subscription = self.create_subscription(
            String, 'uart_tx', self._cb_command, 10)

        # Everything the board prints back, one message per line. The board can
        # talk at any time, so this is polled rather than driven by the writes.
        self._rx_pub = self.create_publisher(String, 'uart_rx', 10)
        self._rx_buffer = bytearray()
        self._rx_timer = self.create_timer(1.0 / rx_poll_rate, self._poll_serial)

        self.get_logger().info('Bridging uart_tx -> serial -> uart_rx')

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

    def _poll_serial(self):
        """Drain the input buffer and publish each complete line as a String."""
        try:
            waiting = self.ser.in_waiting
            if not waiting:
                return
            self._rx_buffer.extend(self.ser.read(waiting))
        except (serial.SerialException, OSError) as e:
            self.get_logger().error(f'Serial read failed: {e}',
                                    throttle_duration_sec=5.0)
            return

        # The board terminates with \r\n; anything without a newline yet is a
        # partial line and stays buffered until the rest arrives.
        while b'\n' in self._rx_buffer:
            raw, _, rest = self._rx_buffer.partition(b'\n')
            self._rx_buffer = bytearray(rest)

            # Undecodable bytes are line noise, not a reason to drop the line.
            line = raw.decode('utf-8', errors='replace').strip()
            if not line:
                continue

            self._rx_pub.publish(String(data=line))
            if self._log_rx:
                self.get_logger().info(f'Received: "{line}"')

        # A board stuck mid-line (or spewing binary) must not grow the buffer
        # without bound.
        if len(self._rx_buffer) > self.MAX_LINE_BYTES:
            self.get_logger().warning(
                f'Discarding {len(self._rx_buffer)} bytes with no line ending')
            self._rx_buffer.clear()

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
