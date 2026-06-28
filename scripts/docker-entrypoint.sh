#!/bin/bash
set -e

# Ensure a ROS 2 DDS domain is always set so multi-machine discovery behaves the
# same on every target (amd64 desktop and the arm64 rover). docker-compose passes
# ROS_DOMAIN_ID via its environment; this default covers containers started
# without it (e.g. a plain `docker run` on the robot). Override by exporting
# ROS_DOMAIN_ID in the environment before launch.
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-47}"

# Pin Fast DDS to the robot network interface so DDS discovery multicast leaves
# the correct NIC. On a multi-homed host (e.g. groundstation with campus WiFi +
# robot/AP link) discovery would otherwise egress the default-route (WiFi)
# interface and the other machine would never hear it — you can ping but ROS
# topics never appear.
#
# ROS_NET_IFACE (the interface NAME, auto-detected by setup.sh) is stable across
# reboots; we resolve its CURRENT IPv4 here at every start, so a new DHCP lease
# is picked up by simply restarting the container — no hardcoded addresses.
SPARKY_DDS_PROFILE=/tmp/sparky_fastdds_profiles.xml
if [ -n "${ROS_NET_IFACE:-}" ]; then
    ROBOT_IP="$(ip -o -4 addr show dev "$ROS_NET_IFACE" 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -n1)"
    if [ -n "$ROBOT_IP" ]; then
        cat > "$SPARKY_DDS_PROFILE" <<XML
<?xml version="1.0" encoding="UTF-8" ?>
<dds xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
  <profiles>
    <transport_descriptors>
      <transport_descriptor>
        <transport_id>sparky_udp_transport</transport_id>
        <type>UDPv4</type>
        <interfaceWhiteList>
          <address>${ROBOT_IP}</address>
        </interfaceWhiteList>
      </transport_descriptor>
    </transport_descriptors>
    <participant profile_name="sparky_participant_profile" is_default_profile="true">
      <rtps>
        <userTransports>
          <transport_id>sparky_udp_transport</transport_id>
        </userTransports>
        <useBuiltinTransports>false</useBuiltinTransports>
      </rtps>
    </participant>
  </profiles>
</dds>
XML
        export FASTRTPS_DEFAULT_PROFILES_FILE="$SPARKY_DDS_PROFILE"
        echo "[entrypoint] Fast DDS pinned to ${ROS_NET_IFACE} (${ROBOT_IP})"
    else
        echo "[entrypoint] WARN: ROS_NET_IFACE='${ROS_NET_IFACE}' has no IPv4 yet; DDS using all interfaces"
        rm -f "$SPARKY_DDS_PROFILE"
    fi
else
    # No interface pinned (single-homed machine): let DDS use all interfaces.
    rm -f "$SPARKY_DDS_PROFILE"
fi

# Source ROS2 setup
source /opt/ros/humble/setup.bash

# If workspace has been built, source it
if [ -f /ros2_ws/install/setup.bash ]; then
    source /ros2_ws/install/setup.bash
fi

# Execute the command
exec "$@"