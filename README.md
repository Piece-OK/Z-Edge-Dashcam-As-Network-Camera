# Z-Edge Dashcam as a Network Camera

Keep a Z-Edge dashcam awake so a player such as VLC can access its RTSP stream.
The script initializes the camera, synchronizes its clock with your computer's
local time, and maintains the camera's TCP heartbeat connection.

The original version was tested with **Z3G**. **Z3D** and **Z3Pro** may work but
are unverified. The changes in v1.0.0 have automated tests, but have not been
retested with a physical dashcam.

## Quick start

1. Install [Python](https://www.python.org/downloads/) **3.10 or newer**.
2. Enable Wi-Fi on the dashcam and connect your computer to its access point.
3. Download `dashcam_connect.py` from the [latest release](https://github.com/Piece-OK/Z-Edge-Dashcam-As-Network-Camera/releases/latest).
4. Open a terminal in the download folder and run:

   ```console
   python dashcam_connect.py
   ```

   On Windows, you can use `py` instead of `python`; on Linux/macOS, use `python3`.
   No additional Python packages are required.

5. Wait for **Heartbeat responding**, then open VLC's **Open Network Stream**
   dialog and enter:

   ```text
   rtsp://192.168.42.1/stream0/svc0//
   ```

Leave the terminal open while streaming. Press **Ctrl+C** to stop.
A responding heartbeat confirms the control connection; video playback still
needs to be checked in your player.

## Settings

No source-code editing is needed to change the camera address:

```console
python dashcam_connect.py --ip 192.168.42.1 --verbose
python dashcam_connect.py --http-port 8080 --timeout 10 --retry-delay 5
python dashcam_connect.py --help
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--ip` | `192.168.42.1` | Camera IPv4 address |
| `--http-port` | `80` | Initialization HTTP port |
| `--heartbeat-port` | `3333` | TCP heartbeat port |
| `--interval` | `3` | Seconds between heartbeat replies and the next send |
| `--timeout` | `5` | Timeout in seconds for network operations |
| `--retry-delay` | `3` | Seconds before retrying a failed connection |
| `--verbose` | Off | Log requests and heartbeat responses |
| `--version` | | Print the script version |

On a network error or closed heartbeat connection, the script waits and retries
initialization automatically, including clock synchronization. Local HTTP requests
bypass system proxy settings.

## Troubleshooting

- **Connection refused or timed out:** confirm dashcam Wi-Fi is enabled and your
  computer is connected to it. Check the camera IP; a VPN or firewall may block
  local network access.
- **HTTP error:** use `--verbose` to identify the failing command. Different
  models or firmware may not support the same initialization sequence.
- **Heartbeat responds but no video:** check the RTSP address in VLC, including
  `/stream0/svc0//`. Try closing the phone app or other camera viewers.
- **Connection drops:** keep the camera powered and within Wi-Fi range. The script
  reconnects automatically, but your video player may need to reopen the stream.

This script keeps an existing camera stream awake; it does not provide a virtual
webcam driver or record video.

## Development

Run the tests without a camera or additional packages:

```console
python -m unittest discover -s tests -v
```

Tests cover argument validation, HTTP command order and errors, heartbeat
responses and disconnects, reconnection, and shutdown. GitHub Actions runs them
on Windows, Linux, and macOS with Python 3.10 and 3.14. These checks do not replace
physical-camera compatibility testing.

## License

[MIT](LICENSE). Copyright (c) 2026 Piece-OK.
