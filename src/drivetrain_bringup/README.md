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
| `use_mock_hardware` | `false` | `true`: DevHost. `false`: real ODrive/CAN.   |
| `can_interface`     | `can2`  | SocketCAN interface for the ODrive backend.  |
| `use_imu`           | `true`  | Run the VectorNav VN-300 GNSS/INS driver.    |

The SIYI gimbal/camera is **not** part of this bringup. Launch it separately:

```bash
# Gimbal control + telemetry
ros2 launch siyi_ros2 siyi.launch.py host:=192.168.144.25

# Camera stream (also included by groundstation.launch.py)
ros2 launch groundstation_bringup siyi_camera_launch.py
```