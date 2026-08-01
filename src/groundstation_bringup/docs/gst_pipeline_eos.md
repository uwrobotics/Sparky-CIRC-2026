# `gst_pipeline_eos` — Diagnosis and Proposed Fix

**Status:** proposed, not implemented
**Component:** `siyi_camera_node` (`src/siyi_ros2` submodule) launched by `launch/siyi_camera_launch.py`
**Date:** 2026-08-01

---

## Symptom

```
[siyi_camera_node] gst_pipeline_eos
```

After this line, `/siyi/image_raw` and `/siyi/image_compressed` stop updating
**permanently**. The node does not crash, does not exit, and keeps answering
`ros2 node list`. RViz shows a frozen last frame; `ros2 topic hz /siyi/image_raw`
reports nothing.

The failure is silent by design of the current code path — there is no error, no
traceback, and no exit code. Only that one `WARNING` line marks the moment the
stream died.

---

## Root cause

`gst_pipeline_eos` is logged by the SDK's GStreamer bus poller when the pipeline
posts an End-Of-Stream message. EOS is treated as terminal:

`siyi_sdk/stream/gstreamer_backend.py:234`
```python
elif msg.type == Gst.MessageType.EOS:
    _log.warning("gst_pipeline_eos")
    self._stop_event.set()          # <-- latches; never cleared while running
```

The chain from there:

| Step | Location | Effect |
|---|---|---|
| 1 | `gstreamer_backend.py:236` | `_stop_event.set()` |
| 2 | `gstreamer_backend.py:208` | `frame_generator()`'s `while not self._stop_event.is_set()` exits |
| 3 | `stream.py:240` | `_frame_loop`'s `async for` sees a **normal** generator exhaustion — not an exception — and the task returns cleanly |
| 4 | — | `SIYIStream._running` stays `True`; `rclpy.spin()` keeps running; publishers stay registered but nothing ever publishes again |

Because step 3 is an ordinary return rather than a raised exception, nothing in
the SDK or in `camera_node.py` notices. `_frame_loop`'s `except Exception`
handler (`stream.py:246`) is never reached.

### The GStreamer backend has no reconnect logic at all

`StreamConfig` advertises reconnection support:

`siyi_sdk/stream/models.py:76-77`
```python
reconnect_delay: float = 2.0
max_reconnect_attempts: int = 0   # 0 = unlimited
```

and `SIYIStream`'s class docstring states it "handles reconnection". **Neither is
true for the GStreamer backend.** Grepping the SDK at the pinned revision
(`89c34b1`), those two fields are read only by:

- `siyi_sdk/stream/opencv_backend.py:143,176-198`
- `siyi_sdk/stream/aiortsp_backend.py:114,126,173-178`

`gstreamer_backend.py` never references either field. It defines
`_RECONNECT_DELAY_CAP` at module level (line 45) and then never uses it.

We run `backend: "gstreamer"` (`src/siyi_ros2/siyi_ros2/config/camera_params.yaml:7`,
default also `gstreamer` in `siyi_camera_launch.py:33`), so we get the fast
hardware-decode path and zero recovery.

---

## What triggers the EOS in the first place

EOS on `rtspsrc` means the RTSP session ended — the far side tore it down or the
source gave up. Plausible triggers here, roughly in order of likelihood:

1. **Link stall on the WiFi/AP hop.** We use RTSP-over-TCP
   (`StreamConfig.transport` defaults to `"tcp"`, and `camera_node.py:233` does
   not override it). When the TCP connection stalls longer than `rtspsrc`'s
   `tcp-timeout` (default 20 s), `rtspsrc` gives up and posts EOS. A rover
   driving out of good coverage for ~20 s produces exactly this.
2. **Camera-side teardown** — power blip, camera reboot, or the camera dropping
   our session when another client (the SIYI phone app, QGC, a second laptop)
   connects. SIYI cameras serve a limited number of concurrent RTSP clients.
3. **`latency=0` with `buffer-mode=slave`** (`siyi_camera_launch.py:48`,
   `camera_params.yaml:13`) leaves no jitter buffer at all. This mainly causes
   stutter and frame drops rather than EOS, but it removes all tolerance for
   the bursty delivery a marginal link produces.

A useful discriminator when this next happens:

| Timing of the EOS | Most likely cause |
|---|---|
| Immediately at startup, before any frame is published | Pipeline/negotiation problem — see the latent Jetson issue below |
| After seconds-to-minutes of good video | Session teardown (1 or 2 above) — the reconnect gap is the real bug |

---

## Latent issue: the codec is hardcoded to H.264 on Jetson

Not the cause of today's failure on the groundstation, but it will bite the
moment the camera node is moved to the rover.

`StreamConfig.codec` defaults to `"h264"` (`siyi_sdk/stream/models.py:79`), and
`camera_node.py:233` constructs the config **without** setting it:

```python
config = StreamConfig(rtsp_url=url, backend=backend, latency_ms=latency_ms)
```

`camera_node.py` exposes no `codec` ROS parameter, so there is no way to change
it from a launch file or YAML. What that config produces depends on the host:

- **Non-Jetson (our groundstation, amd64):** `_AUTO_PIPELINE`
  (`gstreamer_backend.py:49`) uses `decodebin`, which auto-negotiates H.264 or
  H.265 from the RTSP SDP. The hardcoded `codec` value is unused. **No problem.**
- **Jetson (`/etc/nv_tegra_release` present, `gstreamer_backend.py:27`):**
  `_JETSON_PIPELINE` (line 63) hardcodes `rtp{codec}depay ! {codec}parse`, which
  resolves to `rtph264depay ! h264parse`.

Our A8 mini streams **H.265** — this repo's own README documents the working
manual pipeline as `rtph265depay ! h265parse ! avdec_h265` against
`rtsp://192.168.144.25:8554/main.264` (the `.264` in the path is just SIYI's URL
naming, not the codec). Feeding an H.265 payload to `rtph264depay` fails to
negotiate, and the pipeline dies at startup.

**Implication:** running `siyi_camera_launch.py` on the Jetson today would fail
immediately, and no launch argument can fix it. Any fork we make should expose
`codec` as a ROS parameter.

---

## Proposed fix

The correct fix requires changing `camera_node.py`, which lives in the
`src/siyi_ros2` submodule pointing at upstream `mzahana/siyi_ros2`. That means
forking to `uwrobotics`, exactly as we already did for `ros_odrive`.

### Fix 1 — Frame watchdog in `camera_node.py` (recommended)

Fork `mzahana/siyi_ros2` → `uwrobotics/siyi_ros2`, repoint the submodule, and add
a watchdog that detects the stall and restarts the stream. Keeps GStreamer
hardware decode.

Sketch, against the existing node structure:

```python
# _declare_parameters()
self.declare_parameter("watchdog_timeout_s", 5.0)   # 0 disables
self.declare_parameter("watchdog_startup_grace_s", 15.0)

# __init__, after _start_stream()
self._last_frame_mono = time.monotonic()
self._restart_inflight = False
timeout = self.get_parameter("watchdog_timeout_s").value
if timeout > 0.0:
    self.create_timer(1.0, self._watchdog_tick)

# _on_frame(), first line — hot path, single float store
self._last_frame_mono = time.monotonic()

def _watchdog_tick(self) -> None:
    """Restart the stream when frames stop arriving (e.g. gst_pipeline_eos)."""
    if self._restart_inflight or self._stream is None:
        return
    timeout = self.get_parameter("watchdog_timeout_s").value
    grace = self.get_parameter("watchdog_startup_grace_s").value
    age = time.monotonic() - self._last_frame_mono
    if age < max(timeout, grace if self._never_had_frame else 0.0):
        return
    self.get_logger().warning(f"No frames for {age:.1f}s — restarting stream")
    self._restart_inflight = True
    asyncio.run_coroutine_threadsafe(self._restart_stream(), self._loop)

async def _restart_stream(self) -> None:
    try:
        await self._stream.stop()
        await asyncio.sleep(2.0)          # back-off; camera may still be down
        await self._stream.start()
        self._last_frame_mono = time.monotonic()
    except Exception as exc:
        self.get_logger().error(f"Stream restart failed: {exc}")
    finally:
        self._restart_inflight = False
```

Why `stop()` + `start()` is sufficient and safe:

- `SIYIStream.stop()` (`stream.py:148`) cancels `_frame_loop`, calls
  `backend.disconnect()` (which sets the pipeline to `Gst.State.NULL` and joins
  the bus thread), and sets `_backend = None`.
- `SIYIStream.start()` (`stream.py:134`) then builds a **new** backend via
  `_select_backend()`, so the latched `_stop_event` on the dead backend is
  irrelevant — and `GStreamerBackend.connect()` clears it anyway
  (`gstreamer_backend.py:145`).
- Frame callbacks live on `SIYIStream._callbacks`, not on the backend, so our
  `_on_frame` subscription survives the restart. No re-subscription needed.
- The restart runs on the SDK's asyncio thread via `run_coroutine_threadsafe`,
  matching how `_start_stream()` and `destroy_node()` already dispatch. The
  `_restart_inflight` flag stops the 1 Hz timer from queuing overlapping
  restarts while a reconnect is in progress.

Ship two more parameters in the same fork, both currently unreachable:

- `codec` (`"h264"` / `"h265"`) — required for Jetson, see above.
- `transport` (`"tcp"` / `"udp"`) — currently pinned to the `StreamConfig`
  default with no way to test the alternative.

### Fix 2 — Switch backend (no fork, works today)

`opencv` and `aiortsp` already implement reconnect-with-backoff and honour
`reconnect_delay` / `max_reconnect_attempts`. `backend` is already a launch
argument and a YAML key, so this is a one-line change:

```bash
ros2 launch groundstation_bringup siyi_camera_launch.py backend:=aiortsp
```

**Cost:** on the Jetson this abandons the `nvv4l2decoder` hardware path, so CPU
use and latency both rise. On the amd64 groundstation the generic pipeline is
already CPU `decodebin` + `videoconvert`, so the penalty is much smaller — this
is a reasonable stopgap for groundstation-side testing specifically.

### Fix 3 — Property injection via `rtsp_url` (stopgap, hacky)

The pipeline is assembled by string formatting and handed to `Gst.parse_launch`
(`gstreamer_backend.py:136-141`), with `{url}` substituted verbatim into
`location={url}`. Extra `rtspsrc` properties can therefore be smuggled in
through the `rtsp_url` parameter:

```bash
ros2 launch groundstation_bringup siyi_camera_launch.py \
  rtsp_url:='rtsp://192.168.144.25:8554/main.264 tcp-timeout=0 retry=10'
```

This raises the stall tolerance that triggers cause 1 above, without touching
the submodule. It is a string-injection hack against an implementation detail —
it will break silently if upstream ever quotes the URL. Field workaround only;
do not commit it as a default.

### Rejected: `respawn=True` on the node

Worth stating explicitly since it is the obvious first instinct. It does not
work here: the node never exits on EOS. `_frame_loop` returns normally, `rclpy`
keeps spinning, and the process stays healthy from launch's point of view.
Nothing triggers a respawn. It would only help if the node were also changed to
call `rclpy.shutdown()` on stall — which is a strictly worse version of Fix 1,
since it drops the gimbal control connection along with the video.

---

## Recommendation

1. **Now:** run with `backend:=aiortsp` on the groundstation so testing is not
   blocked (Fix 2).
2. **Next:** fork `mzahana/siyi_ros2` → `uwrobotics/siyi_ros2`, repoint the
   submodule, implement Fix 1 (watchdog + `codec` + `transport` parameters),
   revert to `backend:=gstreamer`.
3. Consider raising `latency_ms` from `0` to `100–200` for the WiFi hop. Costs
   100–200 ms of glass-to-glass latency, buys tolerance for a bursty link. Test
   both before CIRC and pick deliberately.

Fix 1 is worth doing properly before the competition: a stream that silently
dies with no recovery and no visible error is the kind of failure that costs a
run, and the operator's only cue today is one `WARNING` line scrolling past.

---

## Verification plan

Reproduce the EOS deliberately rather than waiting for it:

```bash
# Terminal 1 — run the camera node
ros2 launch groundstation_bringup siyi_camera_launch.py

# Terminal 2 — confirm frames are flowing
ros2 topic hz /siyi/image_raw

# Terminal 3 — force a session teardown, then restore
sudo ip link set <iface> down && sleep 25 && sudo ip link set <iface> up
```

Expected results:

- **Today:** `gst_pipeline_eos` appears, `ros2 topic hz` goes silent and never
  recovers, even after the link returns.
- **With Fix 1:** `gst_pipeline_eos`, then `No frames for 5.0s — restarting
  stream`, then `stream_started` and `ros2 topic hz` resumes within a few
  seconds of the link returning.

Also verify the restart path does not leak: run five link-down cycles and check
that thread count and RSS return to baseline (`ps -o rss,nlwp -p $(pgrep -f
siyi_camera_node)`). The concern is the GStreamer bus thread — `disconnect()`
joins it with a 5 s timeout (`gstreamer_backend.py:180`), and a thread that
outlives its timeout would accumulate across restarts.

---

## References

- `siyi_sdk` pinned at `89c34b15a6660cdbf59578ea9053b761f67b186a`
  (`Dockerfile`, `SIYI_SDK_REF`)
- Launch file: `src/groundstation_bringup/launch/siyi_camera_launch.py`
- Params: `src/siyi_ros2/siyi_ros2/config/camera_params.yaml`
- Node: `src/siyi_ros2/siyi_ros2/siyi_ros2/camera_node.py`
- Working manual pipeline: root `README.md`, "Gimbal Camera Direct Connection"
