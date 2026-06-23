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
DOCKER_PLATFORM=$DOCKER_PLATFORM
ROS_BASE_IMAGE=$ROS_BASE_IMAGE
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