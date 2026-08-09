# Sparky CIRC 2026 -- antenna_teleop
#
# Copyright 2026 UWRobotics

"""Button teleoperation for the tracking antenna.

Maps two controller buttons onto the UART command strings that
``uart_arduino_communicator`` forwards to the antenna's Arduino, published as
``std_msgs/String`` on ``/antenna/uart_tx``.

One command is sent per press (rising edge), not repeatedly while the button
is held: ``joy_node`` runs with ``autorepeat_rate`` set, so ``/joy`` keeps
arriving at 20 Hz with the button still down and a level check would flood the
serial link.
"""

import sys

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import String

COMMAND_TOPIC = '/antenna/uart_tx'


class AntennaJoyNode(Node):
    """Turns button presses into antenna UART command strings."""

    def __init__(self, node_name='antenna_joy_node'):
        super().__init__(node_name)

        # Button indices into sensor_msgs/Joy.buttons. See the mapping table in
        # groundstation_bringup/config/ps4_mapping.md.
        self.declare_parameter('left_button', 3)
        self.declare_parameter('right_button', 1)

        # Command strings sent verbatim to the Arduino, newline-terminated by
        # the UART node.
        self.declare_parameter('left_command', 'pd6,25')
        self.declare_parameter('right_command', 'pd8,75')

        # Bindings are evaluated in order, so if both buttons are pressed in
        # the same Joy message, right wins by being sent last.
        self._bindings = [
            ('left', self.get_parameter('left_button').value,
             self.get_parameter('left_command').value),
            ('right', self.get_parameter('right_button').value,
             self.get_parameter('right_command').value),
        ]

        self._pressed = {index: False for _, index, _ in self._bindings}

        self._pub = self.create_publisher(String, COMMAND_TOPIC, 10)
        self.create_subscription(Joy, 'joy', self.cb_joy, 10)

        summary = ', '.join(
            f'button {index} ({label}) -> "{command}"'
            for label, index, command in self._bindings)
        self.get_logger().info(f'Antenna teleop ready: {summary} -> {COMMAND_TOPIC}')

    def cb_joy(self, msg):
        """
        :type msg: Joy
        """
        needed = max(index for _, index, _ in self._bindings)
        if len(msg.buttons) <= needed:
            self.get_logger().warning(
                f'Joy message has {len(msg.buttons)} buttons, need at least '
                f'{needed + 1} -- check the left_button/right_button parameters',
                throttle_duration_sec=5.0)
            return

        for label, index, command in self._bindings:
            pressed = bool(msg.buttons[index])
            if pressed and not self._pressed[index]:
                self._pub.publish(String(data=command))
                self.get_logger().info(f'{label}: sent "{command}"')
            self._pressed[index] = pressed


def main(args=None):
    rclpy.init(args=args)
    node = AntennaJoyNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except ExternalShutdownException:
        sys.exit(1)
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()
