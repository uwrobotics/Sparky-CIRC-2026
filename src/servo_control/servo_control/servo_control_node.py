#!/usr/bin/env python3
# Copyright (c) 2026 UWRobotics
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from akros2_msgs.msg import Mode
from rclpy.executors import ExternalShutdownException

import Jetson.GPIO as GPIO


class ServoControlNode(Node):
    """
    Drives a single RC servo/ESC pulse (Jetson hardware PWM) from the PS4
    controller d-pad: left -> pulse_left_us, right -> pulse_right_us,
    released (or both held) -> pulse_neutral_us. Forced to neutral whenever
    estop is active.
    """

    def __init__(self, node_name='servo_control'):
        super().__init__(node_name)

        self.declare_parameter('gpio_pin', 15)           # BOARD pin numbering
        self.declare_parameter('pwm_freq_hz', 50)
        self.declare_parameter('pulse_neutral_us', 1500)
        self.declare_parameter('pulse_left_us', 1560)
        self.declare_parameter('pulse_right_us', 1400)
        self.declare_parameter('dpad_axis', 6)            # PS4: d-pad left/right axis
        self.declare_parameter('dpad_axis_left_positive', True)

        self._freq_hz = self.get_parameter('pwm_freq_hz').value
        self._frame_us = 1_000_000 // self._freq_hz
        self._pulse_neutral = self.get_parameter('pulse_neutral_us').value
        self._pulse_left = self.get_parameter('pulse_left_us').value
        self._pulse_right = self.get_parameter('pulse_right_us').value
        self._dpad_axis = self.get_parameter('dpad_axis').value
        self._dpad_axis_left_positive = self.get_parameter('dpad_axis_left_positive').value

        self._estop = False
        self._current_us = self._pulse_neutral

        pin = self.get_parameter('gpio_pin').value
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
        self._pwm = GPIO.PWM(pin, self._freq_hz)
        self._pwm.start(self._us_to_duty(self._pulse_neutral))

        self.create_subscription(Joy, 'joy', self.cb_joy, 1)
        self.create_subscription(Mode, 'mode', self.cb_mode, 1)

        self.get_logger().info('Initialized')

    def _us_to_duty(self, us):
        return us / self._frame_us * 100.0

    def _set_pulse(self, us):
        if us == self._current_us:
            return
        self._pwm.ChangeDutyCycle(self._us_to_duty(us))
        self._current_us = us

    def cb_mode(self, msg):
        """
        :type msg: Mode
        """
        self._estop = msg.estop

    def cb_joy(self, msg):
        """
        :type msg: Joy
        """
        if self._estop:
            self._set_pulse(self._pulse_neutral)
            return

        left = False
        right = False

        if 0 <= self._dpad_axis < len(msg.axes):
            value = msg.axes[self._dpad_axis]
            if not self._dpad_axis_left_positive:
                value = -value
            left = value > 0.5
            right = value < -0.5

        if left and not right:
            self._set_pulse(self._pulse_left)
        elif right and not left:
            self._set_pulse(self._pulse_right)
        else:
            self._set_pulse(self._pulse_neutral)

    def destroy_node(self):
        try:
            self._set_pulse(self._pulse_neutral)
            self._pwm.stop()
            GPIO.cleanup()
        finally:
            super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ServoControlNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except ExternalShutdownException:
        sys.exit(1)
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
