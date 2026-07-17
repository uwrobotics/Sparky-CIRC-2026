ARG ROS_BASE_IMAGE=osrf/ros:humble-desktop
FROM ${ROS_BASE_IMAGE}

RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    build-essential \
    git \
    vim \
    nano \
    sudo \
    iproute2 \
    python3-pip \
    python3-ament-cmake-test \
    ros-humble-ament-cmake-gtest \
    ros-humble-ament-lint-auto \
    ros-humble-ament-lint-common \
    ros-humble-ament-copyright \
    ros-humble-ament-cppcheck \
    ros-humble-ament-cpplint \
    ros-humble-ament-flake8 \
    ros-humble-ament-lint-cmake \
    ros-humble-ament-pep257 \
    ros-humble-ament-uncrustify \
    ros-humble-ament-xmllint \
    ros-humble-xacro \
    ros-humble-hardware-interface \
    ros-humble-ros2-controllers \
    ros-humble-controller-manager \
    ros-humble-ros2controlcli \
    ros-humble-joint-state-broadcaster \
    ros-humble-joint-state-publisher \
    ros-humble-joint-state-publisher-gui \
    ros-humble-trajectory-msgs \
    ros-humble-velocity-controllers \
    ros-humble-diff-drive-controller \
    ros-humble-joint-trajectory-controller \
    ros-humble-joy \
    ros-humble-teleop-twist-joy \
    ros-humble-rviz2 \
    cppcheck \
    uncrustify \
    && if [ "$(dpkg --print-architecture)" != "arm64" ]; then \
        apt-get install -y \
            ros-humble-gazebo-ros-pkgs \
            ros-humble-gazebo-ros2-control-demos; \
    fi \
    && rm -rf /var/lib/apt/lists/*

# Create user with same UID/GID as host user (dynamic)
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG USERNAME=devuser
# Host 'input' group GID, for reading /dev/input/event* (game controllers).
ARG INPUT_GID=994

RUN groupadd -g $GROUP_ID -o $USERNAME 2>/dev/null || true && \
    useradd -m -u $USER_ID -g $GROUP_ID -o -s /bin/bash $USERNAME 2>/dev/null || true && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

RUN groupadd -g $INPUT_GID -o hostinput 2>/dev/null || true && \
    usermod -aG $INPUT_GID $USERNAME 2>/dev/null || true

RUN echo 'export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-47}"' >> /home/$USERNAME/.bashrc && \
    echo '[ -f /tmp/sparky_fastdds_profiles.xml ] && export FASTRTPS_DEFAULT_PROFILES_FILE=/tmp/sparky_fastdds_profiles.xml' >> /home/$USERNAME/.bashrc && \
    echo 'source /opt/ros/humble/setup.bash' >> /home/$USERNAME/.bashrc && \
    echo '[ -f /ros2_ws/install/setup.bash ] && source /ros2_ws/install/setup.bash' >> /home/$USERNAME/.bashrc

# Create workspace
WORKDIR /ros2_ws
RUN chown -R $USERNAME:$USERNAME /ros2_ws

COPY scripts/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

RUN rosdep update && \
    rosdep fix-permissions

USER $USERNAME

# Set the entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["bash"]
