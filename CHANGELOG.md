# Changelog

## 1.0.0

- Add command-line IP, ports, timeout, heartbeat interval, and retry delay settings.
- Remove the third-party `requests` dependency.
- Honor the HTTP port and bypass system proxies for local camera requests.
- Detect HTTP errors and closed heartbeat sockets; retry the full initialization sequence.
- Show the stream URL only after a heartbeat response; support clean Ctrl+C shutdown.
- Add optional diagnostic logging, regression tests, and Windows/Linux/macOS CI.
- Document setup, troubleshooting, compatibility limits, and clock synchronization.
- License the project under MIT.

The original camera command order and heartbeat payload are preserved. Changes
were tested with a local HTTP server and simulated TCP sessions; physical-camera
streaming has not been revalidated for this release.
