# Android Controller Usage

The Kivy-based Android controller provides touch controls and maintains a persistent WebSocket connection to the server.

Run the app directly:
```bash
python android_controller.py
```

To package it as an APK using Buildozer:
```bash
buildozer -v android debug
```

Set `MINECRAFT_WS_URI` to override the WebSocket address or pass `--uri` on the command line.
The UI adapts automatically if you rotate your device.
