# Pygame Controller for Minecraft Web Client

A visual controller interface for the Minecraft Web Client using pygame. This provides an intuitive way to control movement and camera with virtual joysticks and touch areas.

## Features

- **Virtual Movement Joystick**: Drag to move your character (W/A/S/D equivalent)
- **Camera Look Area**: Drag to look around (mouse look equivalent)
- **Real-time Connection Status**: See if you're connected to the game
- **Visual Feedback**: UI elements change color when active
- **Keyboard Shortcuts**: ESC to quit, R to reconnect

## Prerequisites

1. **Minecraft Web Client running**: Make sure the server is running with WebSocket support
2. **Python 3.7+**: Required for asyncio support
3. **pygame**: For the GUI interface
4. **websockets**: For connecting to the game

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements_pygame.txt
   ```

2. **Start the Minecraft Web Client server**:
   ```bash
   node server.js
   ```

3. **Open the web client in your browser** and connect to a world/server

4. **Test the connection** (optional but recommended):
   ```bash
   python test_connection.py
   ```

5. **Start the pygame controller**:
   ```bash
   python pygame_controller.py
   ```

## Usage

### Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Minecraft Web Client Controller              Status: ●     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌─────────────────────┐                 │
│                    │                     │                 │
│                    │   Camera Look Area  │                 │
│                    │   (drag to look)    │                 │
│                    │                     │                 │
│                    └─────────────────────┘                 │
│                                                             │
│                                         Movement: X=0 Z=0   │
│    ●                                                        │
│   ╱ ╲    Movement                                          │
│  ╱   ╲   Joystick                                          │
│ ╱  ●  ╲  (drag to move)                                    │
│ ╲     ╱                                                    │
│  ╲   ╱                                                     │
│   ╲ ╱                                                      │
│    ●                                                        │
│                                                             │
│ Controls:                                                   │
│ • Left joystick: Move character                            │
│ • Right area: Look around (drag mouse)                     │
│ • ESC: Quit                                                │
│ • R: Reconnect                                             │
└─────────────────────────────────────────────────────────────┘
```

### Controls

- **Movement Joystick** (bottom left):
  - Click and drag to move
  - Up = forward, Down = backward, Left/Right = strafe
  - Returns to center when released
  - Sends `move` commands with x/z coordinates

- **Camera Look Area** (top right):
  - Click and drag to look around
  - Mouse movement is translated to camera rotation
  - Sends `look` commands with movement deltas
  - Works like dragging the mouse in the game

- **Keyboard Shortcuts**:
  - `ESC`: Quit the controller
  - `R`: Reconnect to the WebSocket server

### Status Indicators

- **Green "Connected"**: Successfully connected to game
- **Red "Disconnected"**: Connection failed or lost
- **Blue Joystick**: Currently being used
- **Green Look Area**: Currently being dragged
- **Movement Values**: Real-time X/Z movement coordinates

## Troubleshooting

### Connection Issues

1. **"Connection refused"**:
   - Make sure `node server.js` is running
   - Check that port 8081 is available
   - Verify the web client is accessible at localhost:8080

2. **Commands not working**:
   - Make sure you're connected to a world/server in the web client
   - Check the browser console for any errors
   - Try refreshing the web client page

3. **Pygame not found**:
   ```bash
   pip install pygame websockets
   ```

### Performance Issues

- If the controller feels laggy, try:
  - Closing other applications
  - Reducing the sensitivity by modifying the scaling factors in the code
  - Checking your WebSocket connection stability

### Testing

Run the connection test to verify everything is working:
```bash
python test_connection.py
```

This will test all command types and verify the WebSocket connection.

## Customization

You can modify the controller by editing `pygame_controller.py`:

- **Sensitivity**: Change the scaling factors in `handle_camera_look()`
- **Joystick size**: Modify the radius in `VirtualJoystick` initialization
- **Colors**: Update the color constants at the top of the file
- **Layout**: Adjust the positions of UI elements in `__init__()`

## Commands Sent

The controller sends these WebSocket commands:

- **Movement**: `{"type": "move", "x": <float>, "z": <float>}`
- **Camera Look**: `{"type": "look", "movementX": <int>, "movementY": <int>}`

These correspond to the WebSocket API documented in the main README.

## Requirements

- Python 3.7+
- pygame >= 2.5.0
- websockets >= 12.0
- Minecraft Web Client with WebSocket support enabled 