# General information

If you want to use the Z-Edge Dashcam as a network camera, you can run this Python script to initialize a heartbeat connection between your Z-Edge Dashcam and your PC.

It only has been tested with Model "Z3G" but it should also work with "Z3D" and "Z3Pro"

# How
- enable the wifi on your Z-Edge Dashcam and connect to the Access Point.
- install Python via https://www.python.org/downloads/
- download the dashcam_connect.py and change the dashcam IP if nessessary
- open the console and type in "python dashcam_connect.py" (on Windows go to the folder where you downloaded it and type "cmd" in the adressbar)

> [!NOTE]
You should be able to access the network camera via rtsp://DASHCAM-IP/stream0/svc0//