# Pygame Controller for Minecraft Web Client

A comprehensive visual controller interface for the Minecraft Web Client using pygame. This provides an intuitive way to control movement, camera, and all common Minecraft actions with virtual joysticks, touch areas, and action buttons.

## Features

- **Virtual Movement Joystick**: Drag to move your character (W/A/S/D equivalent)
- **Camera Look Area**: Drag to look around (mouse look equivalent)
- **Action Buttons**: Left/Right click, Jump, Sneak, Sprint, Inventory
- **Real-time Connection Status**: See if you're connected to the game
- **Visual Feedback**: UI elements change color when active
- **Toggle Buttons**: Sneak and Sprint stay on/off
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
┌─────────────────────────────────────────────────────────────────────────────┐
│  Minecraft Web Client Controller                           Status: ●        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    ┌─────────────────────┐     ┌─────────┬─────────┐      │
│                    │                     │     │Left Click│Right Click│     │
│                    │   Camera Look Area  │     │  (Red)   │ (Blue)  │      │
│                    │   (drag to look)    │     ├─────────┼─────────┤      │
│                    │                     │     │  Jump   │ Sneak   │      │
│                    └─────────────────────┘     │ (Green) │(Orange) │      │
│                                                ├─────────┼─────────┤      │
│                                Movement: X=0 Z=0│ Sprint  │Inventory│      │
│    ●                                            │(Purple) │ (Gray)  │      │
│   ╱ ╲    Movement                              └─────────┴─────────┘      │
│  ╱   ╲   Joystick                                                          │
│ ╱  ●  ╲  (drag to move)                                                    │
│ ╲     ╱                                                                    │
│  ╲   ╱                                                                     │
│   ╲ ╱                                                                      │
│    ●                                                                        │
│                                                                             │
│ Controls:                                                                   │
│ • Left joystick: Move character                                            │
│ • Camera area: Look around (drag)                                          │
│ • Buttons: Click actions                                                    │
│ • ESC: Quit | R: Reconnect                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Controls

#### **Movement Joystick** (bottom left):
- Click and drag to move
- Up = forward, Down = backward, Left/Right = strafe
- Returns to center when released
- Sends `move` commands with x/z coordinates

#### **Camera Look Area** (center):
- Click and drag to look around
- Mouse movement is translated to camera rotation
- Sends `look` commands with movement deltas
- Works like dragging the mouse in the game

#### **Action Buttons** (right side):

**Row 1:**
- **🔴 Left Click** - Attack/Break blocks (hold to continue attacking)
- **🔵 Right Click** - Use/Place blocks (hold to continue using)

**Row 2:**
- **🟢 Jump** - Jump/swim up (space key equivalent)
- **🟠 Sneak** - Toggle sneak mode (shift key, stays on/off)

**Row 3:**
- **🟣 Sprint** - Toggle sprint mode (ctrl key, stays on/off)
- **⚪ Inventory** - Open inventory (E key equivalent)

#### **Keyboard Shortcuts**:
- `ESC`: Quit the controller
- `R`: Reconnect to the WebSocket server

### Status Indicators

- **Green "Connected"**: Successfully connected to game
- **Red "Disconnected"**: Connection failed or lost
- **Blue Joystick**: Currently being used
- **Green Look Area**: Currently being dragged
- **Highlighted Buttons**: Currently being pressed
- **Green Toggle Buttons**: Sneak/Sprint are active
- **Movement Values**: Real-time X/Z movement coordinates

## Button Behavior

### **Standard Buttons** (Left Click, Right Click, Jump, Inventory):
- Press and hold for continuous action
- Release to stop the action
- Visual feedback while pressed

### **Toggle Buttons** (Sneak, Sprint):
- Click once to turn ON (button turns green)
- Click again to turn OFF (button returns to normal color)
- State persists until toggled again

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

Run the enhanced connection test to verify everything is working:
```bash
python test_connection.py
```

This will test all command types including the new action buttons.

## Customization

You can modify the controller by editing `pygame_controller.py`:

- **Sensitivity**: Change the scaling factors in `handle_camera_look()`
- **Button Layout**: Modify positions in the button initialization
- **Colors**: Update the color constants at the top of the file
- **Button Sizes**: Adjust `button_width` and `button_height`
- **Add More Buttons**: Create new Button instances and handle them in the main loop

## Commands Sent

The controller sends these WebSocket commands:

### **Movement & Camera:**
- **Movement**: `{"type": "move", "x": <float>, "z": <float>}`
- **Camera Look**: `{"type": "look", "movementX": <int>, "movementY": <int>}`
- **Raw Touch**: `{"type": "lookTouch", "currentX": <int>, "lastX": <int>, "currentY": <int>, "lastY": <int>}`

### **Click Actions:**
- **Left Click Down**: `{"type": "documentMouseEvent", "button": 0, "action": "down", "updateMouse": true}`
- **Left Click Up**: `{"type": "documentMouseEvent", "button": 0, "action": "up"}`
- **Right Click Down**: `{"type": "documentMouseEvent", "button": 2, "action": "down", "updateMouse": true}`
- **Right Click Up**: `{"type": "documentMouseEvent", "button": 2, "action": "up"}`

### **Legacy Click Actions** (still supported):
- **Left Click Down**: `{"type": "leftDown"}`
- **Left Click Up**: `{"type": "leftUp"}`
- **Right Click Down**: `{"type": "rightDown"}`
- **Right Click Up**: `{"type": "rightUp"}`

### **DOM Element Clicking:**
- **Generic Click**: `{"type": "clickElement", "selector": "<css-selector>", "action": "click|down|up"}`

### **Control Actions:**
- **Jump**: `{"type": "control", "control": "jump", "state": <bool>}`
- **Sneak**: `{"type": "control", "control": "sneak", "state": <bool>}`
- **Sprint**: `{"type": "control", "control": "sprint", "state": <bool>}`
- **Inventory**: `{"type": "control", "control": "inventory", "state": <bool>}`

All commands correspond to the WebSocket API documented in the main README.

## Technical Notes

### **Document Mouse Event Approach**

The controller now dispatches synthetic mouse events directly to the document, mirroring how the in-browser touch controls trigger clicks. This keeps the standard mouse plugin logic intact and ensures reliable breaking/placing behavior.

**Validation Bypass**: The synthetic events are marked with an `isWebSocketEvent` property that allows them to bypass the normal validation checks in the mouse plugin (such as `isTrusted` and pointer lock requirements). This ensures our WebSocket-generated events work reliably regardless of browser state.

## Requirements

- Python 3.7+
- pygame >= 2.5.0
- websockets >= 12.0
- Minecraft Web Client with WebSocket support enabled

## Advanced Usage

### Adding Custom Buttons

To add a new button (e.g., for dropping items):

1. **Add the button in `__init__`**:
```python
self.drop_btn = Button(start_x, start_y + spacing * 3, button_width, button_height, "Drop", YELLOW)
```

2. **Handle it in the main loop**:
```python
if self.drop_btn.handle_mouse(mouse_pos, mouse_pressed):
    self.handle_control_button("drop", True)
elif not self.drop_btn.is_pressed:
    self.handle_control_button("drop", False)
```

3. **Draw it**:
```python
self.drop_btn.draw(self.screen)
```

### Adding Custom DOM Element Clicks

To trigger other interface elements:

```python
# Example: Click a hotbar slot
self.send_command_sync({
    "type": "clickElement", 
    "selector": ".hotbar-slot:nth-child(1)", 
    "action": "click"
})
```

The controller is designed to be easily extensible for any Minecraft action!