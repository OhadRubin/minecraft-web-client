# Minecraft PyGame Controller - Control Scheme Documentation

This document explains the complete control scheme implemented in the `mc_pygame_controller/` module for the Minecraft Web Client.

## Overview

The Minecraft PyGame Controller provides a touchscreen-friendly graphical interface for controlling a Minecraft web client through WebSocket communication. It features both mouse/touch controls and keyboard shortcuts.

## Window Layout

- **Window Size**: 1600x900 pixels
- **Connection Status**: Top-left corner shows WebSocket connection status
- **Movement Joystick**: Bottom-left virtual joystick for character movement
- **Camera Look Area**: Large central area (800x500) for camera control
- **Action Buttons**: Right side panel with various action buttons
- **Hotbar Slots**: Bottom row showing slots 1-9
- **Look Path Visualization**: Top-right area showing camera movement tracking
- **Instructions Panel**: Bottom-left showing control help

## Movement Controls

### Virtual Joystick
- **Location**: Bottom-left of screen (150, 700 position)
- **Size**: 100px radius
- **Function**: Character movement in X/Z plane
- **Usage**: 
  - Drag from center to move character
  - Up = Forward (negative Z)
  - Down = Backward (positive Z)
  - Left = Strafe Left (negative X)
  - Right = Strafe Right (positive X)

### WASD Keyboard Movement
- **W**: Move forward (negative Z)
- **A**: Strafe left (negative X)
- **S**: Move backward (positive Z)
- **D**: Strafe right (positive X)
- **Behavior**: Normalized diagonal movement for consistent speed
- **Priority**: Keyboard input is used when joystick is centered

## Camera/Look Controls

### Touch/Mouse Camera Area
- **Location**: Center of screen (400, 50 position)
- **Size**: 800x500 pixels
- **Function**: Camera look control (mouse look)
- **Usage**:
  - Drag within area to look around
  - Movement is scaled 2x for better sensitivity
  - Delta movements are sent as look commands
  - All movements are tracked in the Look Path Visualization

### Look Path Tracking
- **Real-time Analysis**: Tracks all camera movements with angle analysis
- **Inactivity Reset**: Automatically resets after 2 seconds of no movement
- **Statistics**: Shows overall angle, efficiency, compass direction
- **Visualization**: Graphical representation in top-right panel

## Action Buttons

### Primary Actions
- **Left Click Button**: 
  - Color: Red
  - Function: Primary attack/break blocks
  - WebSocket: `documentMouseEvent` with button 0
- **Right Click Button**:
  - Color: Blue  
  - Function: Place blocks/use items
  - WebSocket: `rightDown`/`rightUp`

### Movement Actions
- **Jump Button**:
  - Color: Green
  - Function: Character jump
  - WebSocket: `control` with "jump"
- **Sneak Button** (Toggle):
  - Color: Orange
  - Function: Crouch/sneak
  - Type: Toggle button (stays pressed)
  - WebSocket: `control` with "sneak"
- **Sprint Button** (Toggle):
  - Color: Purple
  - Function: Sprint mode
  - Type: Toggle button (stays pressed)
  - WebSocket: `control` with "sprint"

### Inventory & Items
- **Inventory Button**:
  - Color: Gray
  - Function: Open inventory (E key equivalent)
  - WebSocket: `control` with "inventory"
- **Drop Item Button**:
  - Color: Yellow
  - Function: Drop 1 item from current hotbar slot
  - WebSocket: `dropItem` with amount 1
- **Swap Hands Button**:
  - Color: Pink/Magenta
  - Function: Swap main hand and off-hand items
  - WebSocket: `swapHands`

### Hotbar Slots
- **Slot Buttons**: 9 buttons numbered 1-9
- **Location**: Bottom of screen
- **Colors**: Dark gray with white text
- **Current Slot**: Highlighted with yellow border
- **Function**: Select active hotbar slot (0-8 internally)
- **WebSocket**: `setHotbarSlot`

## Keyboard Shortcuts

### Click Actions
- **Ctrl** or **Z**: Left click (alternative to button)
- **Tab** or **X**: Right click (alternative to button)

### Movement Actions
- **Spacebar**: Jump (alternative to button)

### Item Management
- **Q**: Drop item (standard Minecraft key)
- **F**: Swap hands (standard Minecraft key)

### Hotbar Selection
- **1-9 Number Keys**: Select corresponding hotbar slots

### Utility
- **C**: Clear look path visualization
- **R**: Reconnect WebSocket
- **ESC**: Quit application

## Look Path Visualization

### Features
- **Real-time Tracking**: Shows accumulated camera movement as a path
- **Grid Display**: 20px grid for reference
- **Origin Marker**: Red circle showing starting point
- **Current Position**: Purple circle showing current camera position
- **Path Line**: Cyan line connecting all movements
- **Statistics Panel**: Live analysis of movement patterns

### Analysis Metrics
- **Movement Count**: Total number of camera movements
- **Overall Angle**: Primary direction of camera movement
- **Compass Direction**: N/S/E/W direction interpretation
- **X/Y Components**: Horizontal and vertical movement analysis
- **Path Efficiency**: Straight-line distance vs. actual path length
- **Movement Types**: Count of X-only, Y-only, and mixed movements
- **Idle Timer**: Time since last movement with color coding

### Auto-Reset
- **Timeout**: 2 seconds of inactivity
- **Manual Clear**: C key or Clear button
- **Final Stats**: Printed to console before reset

## WebSocket Communication

### Connection
- **Server**: localhost:8081
- **Protocol**: WebSocket with JSON messages
- **Registration**: Identifies as "pygame" client
- **Status**: Visual indicator in top-left

### Command Types
- `move`: Character movement (x, z coordinates)
- `look`: Camera movement (movementX, movementY)
- `documentMouseEvent`: Mouse clicks with button and action
- `rightDown`/`rightUp`: Right click actions
- `control`: Various controls (jump, sneak, sprint, inventory)
- `setHotbarSlot`: Hotbar slot selection
- `dropItem`: Item dropping
- `swapHands`: Hand swapping

## UI Status Indicators

### Real-time Display
- **Connection Status**: Green (Connected) / Red (Disconnected)
- **Movement Values**: Current X/Z movement coordinates
- **Keyboard Status**: Shows if WASD keys are active
- **Active Shortcuts**: Lists currently pressed shortcut keys
- **Current Hotbar Slot**: Shows selected slot number
- **Look Path Stats**: Live camera movement analysis

### Visual Feedback
- **Button States**: Pressed buttons show lighter colors
- **Toggle States**: Toggle buttons show green when active
- **Hotbar Selection**: Yellow border around active slot
- **Camera Area**: Green border when actively dragging
- **Joystick**: Yellow knob when actively moving

## Technical Implementation

### File Structure
- `controller.py`: Main controller class and game loop
- `ui_elements.py`: Button, joystick, and touch area classes
- `look_path.py`: Camera movement tracking and analysis
- `constants.py`: Colors, dimensions, and configuration
- `__init__.py`: Module initialization

### Key Classes
- `MinecraftController`: Main application controller
- `VirtualJoystick`: Touch-friendly movement control
- `TouchArea`: Camera look control area
- `Button`/`ToggleButton`: Action buttons
- `LookPathTracker`: Camera movement analysis
- `KeyboardMovement`: WASD input handler

This control scheme provides comprehensive input methods suitable for both desktop and touch-screen environments, with extensive visual feedback and real-time analysis capabilities. 