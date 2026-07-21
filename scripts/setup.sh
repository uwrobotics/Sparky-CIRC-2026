#!/bin/bash

# Auto-setup script for Docker user permissions
# This script detects the current user's UID/GID and creates a .env file
# for docker-compose to use the correct user mapping

set -e

echo "🔧 Setting up Docker environment for user permissions..."

# Get current user info
CURRENT_USER=$(whoami)
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

echo "📋 Detected user: $CURRENT_USER (UID: $CURRENT_UID, GID: $CURRENT_GID)"

# Detect the host 'input' group GID so the container user can read
# /dev/input/event* (ROS2 joy_node / SDL reads evdev devices, not js0).
# Falls back to 994, the usual Ubuntu 'input' GID.
INPUT_GID=$(getent group input | cut -d: -f3)
INPUT_GID=${INPUT_GID:-994}
echo "📋 Detected input group GID: $INPUT_GID (for game controller access)"

# Detect the host 'gpio' group GID so the container user can read/write
# /dev/gpiochip* (Jetson.GPIO, used by the servo_control node).
GPIO_GID=$(getent group gpio | cut -d: -f3)
GPIO_GID=${GPIO_GID:-999}
echo "📋 Detected gpio group GID: $GPIO_GID (for servo/PWM access)"

# ROS 2 DDS domain ID. Every machine on the access point must use the SAME value
# to discover each other; a non-zero value also isolates us from other teams that
# leave the default (0). Override at setup time, e.g. ROS_DOMAIN_ID=12 ./scripts/setup.sh
ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-47}
echo "📋 Using ROS_DOMAIN_ID: $ROS_DOMAIN_ID (must match on all machines)"

# Detect the network interface that reaches the robot/ROS network.
#
# On a multi-homed machine (e.g. the groundstation has both campus WiFi and the
# robot/AP link) ROS 2 / Fast DDS must send DDS discovery multicast out the
# interface that actually reaches the other machine — NOT the default-route
# interface, which is usually the internet/WiFi one. Getting this wrong is the
# classic "I can ping but ROS topics never show up" failure.
#
# We detect the interface BY NAME (stable across reboots) so nothing depends on
# the DHCP-assigned IP. The container later binds Fast DDS to this interface's
# current IP at every start. Override with:  ROS_NET_IFACE=eth0 ./scripts/setup.sh
detect_robot_iface() {
    # 1. Explicit override always wins.
    if [ -n "${ROS_NET_IFACE:-}" ]; then
        echo "$ROS_NET_IFACE"; return
    fi

    # Candidate interfaces: UP, global-scope IPv4, excluding virtual/container ones.
    local candidates
    mapfile -t candidates < <(ip -o -4 addr show up scope global 2>/dev/null \
        | awk '{print $2}' \
        | grep -vE '^(lo|docker|veth|br-|virbr|tap|tun)' \
        | sort -u)

    # 2. Exactly one real interface -> unambiguous (typical single-homed Jetson).
    if [ "${#candidates[@]}" -eq 1 ]; then
        echo "${candidates[0]}"; return
    fi
    if [ "${#candidates[@]}" -eq 0 ]; then
        echo ""; return
    fi

    # 3. Multi-homed: drop the interface used to reach the internet (campus WiFi)
    #    and keep the remaining robot-facing one.
    local inet_iface remaining=() c
    inet_iface="$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'dev \K\S+' | head -n1)"
    for c in "${candidates[@]}"; do
        [ "$c" = "$inet_iface" ] && continue
        remaining+=("$c")
    done
    if [ "${#remaining[@]}" -eq 1 ]; then
        echo "${remaining[0]}"; return
    fi

    # 4. Still ambiguous: try an optional subnet hint, otherwise give up.
    if [ -n "${ROBOT_SUBNET_PREFIX:-}" ]; then
        for c in "${candidates[@]}"; do
            if ip -o -4 addr show dev "$c" 2>/dev/null | grep -q "inet ${ROBOT_SUBNET_PREFIX}"; then
                echo "$c"; return
            fi
        done
    fi
    echo ""
}

ROS_NET_IFACE="$(detect_robot_iface)"
if [ -n "$ROS_NET_IFACE" ]; then
    DETECTED_IP="$(ip -o -4 addr show dev "$ROS_NET_IFACE" 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -n1)"
    echo "📋 Robot/ROS network interface: $ROS_NET_IFACE (${DETECTED_IP:-no IPv4 yet})"
else
    echo "⚠️  Could not auto-detect the robot network interface (ambiguous)."
    echo "   Pick it explicitly, e.g.:  ROS_NET_IFACE=eth0 ./scripts/setup.sh"
    echo "   (list interfaces with:  ip -br -4 addr)"
fi

# Detect CPU architecture and select the appropriate ROS base image + platform
ARCH=$(uname -m)
if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    DOCKER_PLATFORM="linux/arm64"
    ROS_BASE_IMAGE="arm64v8/ros:humble"
    echo "📋 Detected ARM64 architecture — using $ROS_BASE_IMAGE"
else
    DOCKER_PLATFORM="linux/amd64"
    ROS_BASE_IMAGE="osrf/ros:humble-desktop"
    echo "📋 Detected AMD64 architecture — using $ROS_BASE_IMAGE"
fi

# Create .env file with current user's info
cat > .env << EOF
# Auto-generated environment variables for Docker user mapping
# This file is created by setup.sh and should not be edited manually

USER_ID=$CURRENT_UID
GROUP_ID=$CURRENT_GID
USERNAME=$CURRENT_USER
INPUT_GID=$INPUT_GID
GPIO_GID=$GPIO_GID
DOCKER_PLATFORM=$DOCKER_PLATFORM
ROS_BASE_IMAGE=$ROS_BASE_IMAGE
# ROS 2 DDS domain — must match on every machine on the access point so the
# containers discover each other (and stay isolated from other teams' default 0).
ROS_DOMAIN_ID=$ROS_DOMAIN_ID
# Interface (by name) that reaches the robot network. The container pins Fast DDS
# to this interface so discovery multicast goes to the right NIC, not WiFi.
# Empty = let DDS use all interfaces. Override: ROS_NET_IFACE=eth0 ./scripts/setup.sh
ROS_NET_IFACE=$ROS_NET_IFACE
EOF

echo "✅ Created .env file with your user settings"

# Pre-create workspace directories so Docker doesn't create them as root
mkdir -p build install log
echo "✅ Created workspace directories (build, install, log)"

# Install recommended VS Code extensions (e.g. the URDF visualizer) if the
# `code` CLI is available. The .vscode/settings.json is already portable, this
# just makes sure the extension that reads it is present.
if command -v code >/dev/null 2>&1; then
    while IFS= read -r ext; do
        echo "🧩 Installing VS Code extension: $ext"
        code --install-extension "$ext" --force >/dev/null
    done < <(grep -oE '"[a-z0-9_-]+\.[a-z0-9_-]+"' .vscode/extensions.json | tr -d '"')
    echo "✅ VS Code extensions installed"
else
    echo "ℹ️  'code' CLI not found — open the project in VS Code and accept the"
    echo "   recommended-extensions prompt to install the URDF visualizer."
fi

# Handle directories that may have been previously created by Docker as root
if [ "$(stat -c '%U' build)" != "$CURRENT_USER" ] || \
   [ "$(stat -c '%U' install)" != "$CURRENT_USER" ] || \
   [ "$(stat -c '%U' log)" != "$CURRENT_USER" ]; then
    echo ""
    echo "⚠️  Some directories are not owned by you (likely created by Docker as root)."
    echo "   Fix with: sudo chown -R \$USER:\$USER build install log"
fi

echo ""
echo "🚀 Setup complete! You can now run:"
echo "   docker-compose up -d"
echo ""
echo "📝 This setup will work for any user on any machine."