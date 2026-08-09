### Drivetrain pipeline

## Documentation

- ![Teleop Node Architecture](images/Teleop-Diagram.drawio.png)

**joy_node_drive** — `joy` / `joy_node`. Reads the PS4 controller.
- Publishes: `/joy_drive` [`sensor_msgs/msg/Joy`]
- Parameters: `device_name: "Wireless Controller"` (unverified on
  hardware yet), `deadzone: 0.1`, `autorepeat_rate: 20.0`,
  `coalesce_interval: 0.01`

**joy_teleop** — `teleop_twist_joy` / `teleop_node`. Converts joystick
axes into a velocity command.
- Subscribes: `/joy_drive` [`sensor_msgs/msg/Joy`]
- Publishes: `/joy_vel` [`geometry_msgs/msg/Twist`]
- Parameters: `config/<joy_config>_twist_config.yaml` (axis mapping,
  scale_linear, scale_angular, turbo)

**teleop_node** — `akros2_teleop` / `teleop_node`. Mixes teleop input
into the final drive command.
- Subscribes: `/joy_vel` [`geometry_msgs/msg/Twist`]
- Publishes: `/cmd_vel` [`geometry_msgs/msg/Twist`]
- Parameters: `timer_period: 0.02`, `config/<joy_config>_mode_config.yaml`

**diff_drive_controller** — ros2_control controller consuming
`/cmd_vel`, drives the 6 wheels. Configured in
`sparky_description/config/sparky_controllers.yaml`.

### Arm pipeline

**joy_node_arm** — `joy` / `joy_node`. Reads the Xbox controller.
- Publishes: `/joy_arm` [`sensor_msgs/msg/Joy`]
- Parameters: `device_name: "Generic X-Box pad"` (verified),
  `deadzone: 0.1`, `autorepeat_rate: 20.0`, `coalesce_interval: 0.01`

**arm_teleop_node** — `arm_teleop` / `arm_teleop_node`. Maps joystick
input to arm joint velocities, with an e-stop safety cutoff.
- Subscribes:
  - `/joy_arm` [`sensor_msgs/msg/Joy`] (code subscribes to `/joy`,
    remapped at launch)
  - `/estopped` [`arm_teleop_messages/msg/EstopStatus`] — latched
    (transient-local), so the node always has the current e-stop state.
    Publishes zero velocities when e-stopped.
- Publishes: `/forward_velocity_controller/commands`
  [`std_msgs/msg/Float64MultiArray`]

**forward_velocity_controller** — ros2_control controller consuming
the joint velocity commands, drives the arm.

Note: `joy_node_drive` and `joy_node_arm` run simultaneously,
distinguished by `device_name` (not index), so two physical
controllers can be used at once.