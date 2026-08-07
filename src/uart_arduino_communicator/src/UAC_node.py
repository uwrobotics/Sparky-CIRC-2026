#!/usr/bin/env python3
"""
ROS 2 node that sends UART messages to an Arduino over USB-C (serial).

Subscribes to: /uart_tx  (std_msgs/String)
Parameters:
  - port      (string)  default: /dev/ttyACM0
  - baudrate  (int)     default: 115200
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import serial.tools.list_ports


class UartSenderNode(Node):
    def __init__(self):
        super().__init__('uart_sender_node')

        # Parameters
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)

        port = self.get_parameter('port').get_parameter_value().string_value
        baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value

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

        # Subscriber
        self.subscription = self.create_subscription(
            String,
            'uart_tx',
            self.tx_callback,
            10
        )

        self.get_logger().info('UART sender ready. Publish to /uart_tx')

    def tx_callback(self, msg: String):
        """Send the received string over UART (appends newline)."""
        try:
            data = (msg.data + '\n').encode('utf-8')
            self.ser.write(data)
            self.ser.flush()
            self.get_logger().info(f'Sent: "{msg.data}"')
        except serial.SerialException as e:
            self.get_logger().error(f'Serial write failed: {e}')

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