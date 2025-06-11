# Gamepad Controller V3

A TypeScript-based gamepad controller interface for the Minecraft web client. This controller provides both visual UI controls and physical gamepad support.

## Features

- Visual gamepad interface with clickable buttons and draggable joysticks
- Physical gamepad support (Xbox controller layout)
- WebSocket connection to Minecraft web client
- Trigger button continuous press support
- Configurable deadzone and trigger settings
- Real-time status display
- **Movement accumulation and reporting** - Tracks joystick movements and displays summary reports instead of individual commands

## Setup

1. Install dependencies:
```bash
npm install
```

2. Build the TypeScript files:
```bash
npm run build
```

3. Make sure the Minecraft web client WebSocket server is running on `ws://localhost:8081`

4. Open `index.html` in a web browser

## Usage

### Visual Controls
- Click on buttons to simulate button presses
- Drag joysticks to control movement and camera
- L2/R2 triggers support continuous pressing

### Physical Gamepad
- Connect an Xbox-compatible gamepad
- Press any button to activate
- All standard Xbox controller buttons are mapped

### Configuration
- Adjust trigger duration and interval using the controls below the gamepad
- Duration: How long a single trigger press lasts (1-1000ms)
- Interval: Time between continuous trigger presses (1-1000ms)

## Architecture

The controller consists of several TypeScript modules:

- `GamepadController.ts` - Main controller class
- `WebSocketManager.ts` - Handles WebSocket connection and communication
- `types.ts` - TypeScript type definitions
- `controller.ts` - Controller state and logic

## WebSocket Commands

The controller sends the following command types:
- `gamepadConnect` - Initial connection
- `gamepadButtonPressDown` - Button press start
- `gamepadButtonPressUp` - Button press end
- `gamepadJoystickMove` - Joystick position update
- `gamepadJoystickCenter` - Joystick centering
- `gamepadDestroy` - Cleanup on disconnect

## Movement Reporting

Instead of logging every individual `gamepadJoystickMove` command, the controller now accumulates movement data and generates summary reports when joystick sessions end. Reports include:

- Session duration
- Total number of movements
- Total distance traveled
- Maximum distance from center
- Final position
- Movement direction analysis

Example report:
```
🎮 Right Stick Movement Report:
   Duration: 1.2s
   Movements: 13
   Total Distance: 4.567
   Max Distance: 1.000
   Final Position: (0.000, 0.000)
   Summary: Up (13 moves, 4.57 total distance)
══════════════════════════════════════════════════
```