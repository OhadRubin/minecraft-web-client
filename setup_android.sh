#!/bin/bash

# Android controller setup script
# Installs dependencies and copies documentation for offline use

set -e

if [ ! -f "android_controller.py" ]; then
  echo "Run this script from the repository root" >&2
  exit 1
fi

echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements_kivy.txt

if ! command -v buildozer >/dev/null 2>&1; then
  echo "Installing Buildozer..."
  python3 -m pip install buildozer
fi

DOCS_DIR="docs/android"
mkdir -p "$DOCS_DIR"
cp PYGAME_CONTROLLER.md "$DOCS_DIR/README.md"

cat > "$DOCS_DIR/USAGE.md" <<'DOC'
# Android Controller Usage

The Kivy-based Android controller provides touch controls and a persistent WebSocket connection.

```bash
python android_controller.py
```

To build an APK using Buildozer:

```bash
buildozer -v android debug
```

You can override the WebSocket URI with the `MINECRAFT_WS_URI` environment variable or the `--uri` command line option.
The layout will automatically adapt if you rotate your device.
DOC


echo "Android controller setup complete." 
