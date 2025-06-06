# Minecraft PyGame Controller - Quick Reference

## Overview
Touchscreen-friendly GUI for Minecraft web client via WebSocket (localhost:8081). Window: 1600x900px.

## Controls

### Movement
- **Virtual Joystick**: Bottom-left (150,700), 100px radius - WASD movement
- **WASD Keys**: W=forward, A=left, S=back, D=right
- **Camera Area**: Center (400,50), 800x500px - mouse look with 2x sensitivity

### Action Buttons (Right Panel)
- **Left Click**: Red - Attack/break blocks
- **Right Click**: Blue - Place blocks/use items  
- **Jump**: Green - Character jump
- **Sneak**: Orange - Toggle crouch
- **Sprint**: Purple - Toggle sprint
- **Inventory**: Gray - Open inventory (E key)
- **Drop Item**: Yellow - Drop 1 item
- **Swap Hands**: Pink - Swap main/off-hand items

### Hotbar
- **Slots 1-9**: Bottom row, yellow border shows active slot
- **Number Keys 1-9**: Select hotbar slots

### Keyboard Shortcuts
- **Ctrl/Z**: Left click
- **Tab/X**: Right click  
- **Spacebar**: Jump
- **Q**: Drop item
- **F**: Swap hands
- **C**: Clear look path
- **R**: Reconnect WebSocket
- **ESC**: Quit

## Features

### Look Path Visualization
- **Location**: Top-right panel
- **Function**: Tracks camera movements with real-time analysis
- **Stats**: Movement count, direction, efficiency, compass bearing
- **Auto-reset**: After 2 seconds of inactivity

### Status Display
- **Connection**: Top-left (Green=connected, Red=disconnected)
- **Movement**: Current X/Z coordinates
- **Active Keys**: Shows pressed WASD keys
- **Hotbar Slot**: Current selection number

## WebSocket Commands
- `move`: Character movement (x, z)
- `look`: Camera movement (movementX, movementY)
- `documentMouseEvent`: Mouse clicks
- `rightDown`/`rightUp`: Right click actions
- `control`: Jump, sneak, sprint, inventory
- `setHotbarSlot`: Hotbar selection (0-8)
- `dropItem`: Drop items (amount)
- `swapHands`: Hand swapping

## File Structure
- `controller.py`: Main controller and game loop
- `ui_elements.py`: Buttons, joystick, touch areas
- `look_path.py`: Camera movement tracking
- `constants.py`: Colors and configuration
- `__init__.py`: Module initialization

## Usage
1. Start Minecraft web client
2. Run `python controller.py`
3. Use touch/mouse controls or keyboard shortcuts
4. F5/F6 for recording (if implemented) 