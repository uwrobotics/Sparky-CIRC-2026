# ROS2 Humble Docker Demo

This is the template for setting up and using ROS2 Humble in a Docker container.
This template is required by all UWRobotics software project.

## Project Structure
```
docker_demo/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Container orchestration (base, works on Ubuntu)
├── docker-compose.wsl.yml  # WSL2-specific display overrides
├── run.sh                  # Platform-aware launcher (auto-detects WSL vs Ubuntu)
├── scripts/                # Shell scripts
│   ├── setup.sh            # Host-side: detects UID/GID, prepares .env
│   ├── docker-entrypoint.sh# Container startup script
│   └── build.sh            # Build script for ROS2 workspace
├── src/                    # ROS2 source code
└── README.md               # This file
```

## GUI / Display Setup (RViz2, Gazebo, Qt)

The container supports graphical applications on both **native Ubuntu** and **WSL2**. Use `run.sh` instead of `docker compose` directly — it auto-detects your platform and merges the correct compose files.

### Prerequisites (run on the host, outside Docker)

**Grant Docker access to your X server:**
```bash
xhost +local:docker
```

**Verify `DISPLAY` is set:**
```bash
echo $DISPLAY   # should print :0 or :1
```
If empty, set it manually:
```bash
export DISPLAY=:0
```

### Platform differences

| Setting | Native Ubuntu | WSL2 |
|---|---|---|
| Compose files | `docker-compose.yml` | `docker-compose.yml` + `docker-compose.wsl.yml` |
| `XDG_RUNTIME_DIR` | `/run/user/1000` | `/mnt/wslg/runtime-dir` |
| `/mnt/wslg` mount | not mounted | mounted |
| Wayland | disabled | enabled |

### Running with display support

```bash
# Use run.sh — it picks the right compose files automatically
./run.sh up -d
./run.sh exec ros2-dev bash

# Then inside the container, GUI apps like RViz2 should work:
ros2 launch <package> <launch_file>
```

---

## How to use UWRobotics Template

### 1. Build and run the Docker Container with Docker Compose 

**Step 1: Build and Run Container**
```bash
# Use run.sh to auto-detect platform (WSL2 or Ubuntu)
./run.sh build
./run.sh up -d

# Enter the container
./run.sh exec ros2-dev bash
```

**Step 2: Create New ROS2 Package Inside Container**
```bash
# Inside container - create new package
cd /ros2_ws/src
ros2 pkg create --build-type ament_cmake my_cpp_package \
   --dependencies rclcpp std_msgs \
   --license MIT

# Or create Python package
ros2 pkg create --build-type ament_python my_python_package \
   --dependencies rclpy std_msgs \
   --license MIT
```

**Step 3: Build and Test**
```bash
# Build the workspace
cd /ros2_ws
./build.sh

# Source the workspace
source install/setup.bash

# Run the node
ros2 run <package_name> <executable_name> <arg1> <arg2>

# Test the package
colcon test --packages-select <pkg1> <pkg2> <pkg3>

# View the test result
colcon test-result --verbose
```

#### Method 2: Direct Docker Commands

**Build Image:**
```bash
docker build -t ros2-humble-demo .
```

**Run Container:**
```bash
docker run -it --rm \
  --name ros2_container \
  -v $(pwd)/src:/ros2_ws/src:rw \
  -v $(pwd)/build:/ros2_ws/build:rw \
  -v $(pwd)/install:/ros2_ws/install:rw \
  --net=host \
  ros2-humble-demo
```

### 3. ROS2 Development Utils Available in Container

#### Package Creation
```bash
# C++ package
ros2 pkg create --build-type ament_cmake package_name --dependencies rclcpp std_msgs geometry_msgs

# Python package
ros2 pkg create --build-type ament_python package_name --dependencies rclpy std_msgs

# Generating executable packages
ros2 pkg create --build-type ament_cmake --license Apache-2.0 --node-name my_node my_package
```

#### Building and Dependencies
```bash
# Install dependencies
rosdep install --from-paths src --ignore-src -r -y

# Build specific packages
colcon build --packages-select package_name

# Build with debug info
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Debug
```

#### Testing and Quality
```bash
# Run tests
colcon test --packages-select package_name

# View test results
colcon test-result --verbose

# Lint code
ament_lint_auto package_name
```

#### Runtime Tools
```bash
# List nodes
ros2 node list

# Check topics
ros2 topic list
ros2 topic echo /topic_name

# Launch files
ros2 launch package_name launch_file.py

# Parameter management
ros2 param list
ros2 param get /node_name parameter_name
```

## Quick Start

1. **Clone and setup (automatic user detection):**
   ```bash
   git clone <this-repo>
   cd docker_demo
   ./scripts/setup.sh
   ```

2. **Start the development environment:**
   ```bash
   xhost +local:docker   # allow Docker to use your display
   ./run.sh build
   ./run.sh up -d
   ```

3. **Enter the container:**
   ```bash
   ./run.sh exec ros2-dev bash
   ```

4. **Build and test your ROS2 packages:**
   ```bash
   # Inside the container
   cd /ros2_ws
   ./build.sh

   # Source the workspace
   source install/setup.bash

   # Run the demo executable
   ros2 run hello_world test_exec
   ```

5. **Access files from VS Code:**
   - All files in `build/`, `install/`, and `log/` should be created your computer not docker user 
   - Edit source files in `src/` normally

## Stopping the Environment

```bash
# Stop container
docker-compose down

# Remove everything including volumes
docker-compose down -v
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 UWRobotics.

This repository bundles third-party components under their own licenses (see [NOTICE](NOTICE)):
- `src/ros_odrive` (submodule) — MIT, © ODrive Robotics (see `src/ros_odrive/LICENSE`).
- `src/osr_gazebo` — Apache-2.0, derived from the NASA JPL Open Source Rover (© 2018 California Institute of Technology) and dongjineee/rover_gazebo (see `src/osr_gazebo/LICENSE`).