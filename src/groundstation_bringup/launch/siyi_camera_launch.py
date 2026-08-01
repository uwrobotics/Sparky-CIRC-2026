# Sparky CIRC 2026 -- groundstation_bringup
#
# Copyright 2026 UWRobotics

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Defaults below intentionally mirror siyi_ros2/config/camera_params.yaml.
    # Launch arguments are applied *after* the YAML, so any default that differs
    # from the file silently wins -- keep the two in sync when editing.
    declared_args = [
        DeclareLaunchArgument(
            'rtsp_url', default_value='',
            description=(
                'Full RTSP URL. Empty = auto-build from host + camera_model. '
                'Set this to target a relay on the rover instead of the camera '
                'directly. An rtspt:// scheme forces RTSP-over-TCP.'),),
        DeclareLaunchArgument(
            'host', default_value='192.168.144.25',
            description='Camera IP, used when rtsp_url is empty.'),
        DeclareLaunchArgument(
            'camera_model', default_value='a8',
            description='zt30 | zt6 | zr30 | zr10 | a8 | a2 | r1m.'),
        DeclareLaunchArgument(
            'stream_index', default_value='0',
            description='0: main stream. 1: sub stream.'),
        DeclareLaunchArgument(
            'backend', default_value='gstreamer',
            description='gstreamer | opencv | aiortsp | auto.'),
        DeclareLaunchArgument(
            'publish_raw', default_value='true',
            description='Publish sensor_msgs/Image on /siyi/image_raw.'),
        DeclareLaunchArgument(
            'publish_compressed', default_value='true',
            description='Publish sensor_msgs/CompressedImage.'),
        DeclareLaunchArgument(
            'image_scale', default_value='1.0',
            description='Downscale factor (0.1 to 1.0) applied before publish.'),
        DeclareLaunchArgument(
            'jpeg_quality', default_value='80',
            description='JPEG quality for the compressed topic (1 to 100).'),
        DeclareLaunchArgument(
            'latency_ms', default_value='200',
            description=(
                'GStreamer rtspsrc jitter buffer. 0 disables it entirely, which '
                'makes rtpjitterbuffer discard any late/reordered packet -- over '
                'the AP link that costs reference frames and the decoder logs '
                '"Could not find ref with POC". 200 measured clean.'),),
        DeclareLaunchArgument(
            'frame_id', default_value='siyi_camera',
            description='TF frame stamped on published images.'),
        DeclareLaunchArgument(
            'camera_info_url', default_value='',
            description='Calibration YAML: file:///abs/path or package://pkg/path.'),
        DeclareLaunchArgument(
            'camera_name', default_value='siyi_camera',
            description='Camera name used by camera_info_manager.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Node namespace.'),
        DeclareLaunchArgument(
            'gst_debug', default_value='1',
            description=(
                'GStreamer log level. 1 keeps real errors visible; 0 hides them '
                'entirely, including the reason a stream never starts. Raise to '
                '3+ when debugging pipeline negotiation.'),),
        DeclareLaunchArgument(
            'use_watchdog', default_value='true',
            description=(
                'Restart the camera node when the stream stalls. The A8 drops '
                'its RTSP session ~30-50 s after sustained gimbal commands and '
                'the GStreamer backend never reconnects, so without this the '
                'feed stays frozen until the node is restarted by hand.'),),
        DeclareLaunchArgument(
            'stall_timeout_s', default_value='0.5',
            description=(
                'Seconds without a frame before the watchdog restarts. A '
                'healthy stream shows gaps up to ~190 ms, so lower values '
                'restart on jitter rather than on a real stall.'),),
    ]

    camera_params = PathJoinSubstitution(
        [FindPackageShare('siyi_ros2'), 'config', 'camera_params.yaml'])

    camera_node = Node(
        package='siyi_ros2',
        executable='siyi_camera_node',
        name='siyi_camera_node',
        namespace=LaunchConfiguration('namespace'),
        parameters=[
            camera_params,
            {
                'rtsp_url': LaunchConfiguration('rtsp_url'),
                'host': LaunchConfiguration('host'),
                'camera_model': LaunchConfiguration('camera_model'),
                'stream_index': LaunchConfiguration('stream_index'),
                'backend': LaunchConfiguration('backend'),
                'publish_raw': LaunchConfiguration('publish_raw'),
                'publish_compressed': LaunchConfiguration('publish_compressed'),
                'image_scale': LaunchConfiguration('image_scale'),
                'jpeg_quality': LaunchConfiguration('jpeg_quality'),
                'latency_ms': LaunchConfiguration('latency_ms'),
                'frame_id': LaunchConfiguration('frame_id'),
                'camera_info_url': LaunchConfiguration('camera_info_url'),
                'camera_name': LaunchConfiguration('camera_name'),
            },
        ],
        output='screen',
        emulate_tty=True,
        # LD_PRELOAD is load-bearing, not an optimisation. camera_node.py imports
        # cv2 before siyi_sdk pulls in PyGObject/Gst, and Ubuntu's python3-opencv
        # is built against GStreamer 1.19.90 while the system ships 1.20.3. In
        # that order the process dies with SIGABRT the moment the SDK's bus
        # thread calls timed_pop_filtered() -- no Python traceback, just
        # "process has died ... exit code -6". Forcing the system libgstreamer to
        # load first makes the import order irrelevant. The bare soname (no path)
        # is resolved by ld.so, so this stays correct on both amd64 and arm64.
        #
        # GSETTINGS_BACKEND silences the dconf-CRITICAL spam caused by
        # XDG_RUNTIME_DIR pointing at /run/user/1000, which docker-compose.yml
        # sets but never mounts. Cosmetic only -- it was not the crash.
        additional_env={
            'LD_PRELOAD': 'libgstreamer-1.0.so.0',
            'GSETTINGS_BACKEND': 'memory',
        },
        # Paired with siyi_watchdog: the watchdog signals this process to exit
        # when the stream stalls, and respawn brings it straight back.
        respawn=True,
        respawn_delay=0.5,
    )

    watchdog_node = Node(
        package='siyi_watchdog',
        executable='camera_watchdog',
        name='camera_watchdog',
        namespace=LaunchConfiguration('namespace'),
        parameters=[{
            'stall_timeout_s': LaunchConfiguration('stall_timeout_s'),
        }],
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_watchdog')),
    )

    # The SIYI SDK is extremely chatty at default log levels; GStreamer's level is
    # left overridable because setting it to 0 hides the cause of a failed stream.
    log_env = [
        SetEnvironmentVariable('GST_DEBUG', LaunchConfiguration('gst_debug')),
        SetEnvironmentVariable('SIYI_LOG_LEVEL', 'WARNING'),
        SetEnvironmentVariable('SIYI_PROTOCOL_TRACE', '0'),
    ]

    return LaunchDescription(declared_args + log_env + [
        camera_node,
        watchdog_node,
    ])
