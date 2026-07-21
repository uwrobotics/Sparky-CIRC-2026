# drivetrain_bringup

## Usage

```bash
#  Launch ODrive Hardware
ros2 launch drivetrain_bringup drivetrain.launch.py

# Launch Mock Hardware 
ros2 launch drivetrain_bringup drivetrain.launch.py use_mock_hardware:=true
```

## Arguments

| Argument            | Default | Purpose                                      |
|---------------------|---------|----------------------------------------------|
| `use_mock_hardware` | `true`  | `true`: DevHost. `false`: real ODrive/CAN.   |
| `can_interface`     | `can0`  | SocketCAN interface for the ODrive backend.  |