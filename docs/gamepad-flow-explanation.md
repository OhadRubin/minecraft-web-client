# Gamepad Flow in Minecraft Web Client

This document explains how gamepad input is handled in the Minecraft web client, from initial connection to in-game actions.

## Overview

The gamepad system uses the **ControMax** library to handle input mapping and provides a unified interface for both keyboard and gamepad controls. The system automatically detects gamepad connections and switches the UI to gamepad mode when appropriate.

## Core Components

### 1. ControMax Library (`src/controls.ts`)
- **Primary controller**: Handles all input management
- **Configuration**: Maps gamepad buttons to game actions
- **Polling**: Continuously checks gamepad state at 10ms intervals
- **Events**: Emits movement, trigger, and release events

### 2. Gamepad UI Cursor (`src/react/GamepadUiCursor.tsx`)
- **Visual cursor**: Displays a crosshair when using gamepad
- **Movement tracking**: Follows gamepad stick input
- **Context awareness**: Only shows in menus/modals, not during gameplay

### 3. Camera Controls (`src/cameraRotationControls.ts`)
- **Right stick**: Controls camera rotation during gameplay
- **Deadzone**: Prevents drift with 0.18 threshold
- **Sensitivity**: 10x multiplier for responsive camera movement

## Initialization Flow

### 1. System Startup
```
Application Start
↓
ControMax Instance Created (src/controls.ts line 42)
↓
Event Listeners Registered
↓
onControInit() Called (line 117)
↓
Camera Movement Events Bound
↓
Gamepad Polling Begins (10ms interval)
```

### 2. Gamepad Detection
```
Browser detects gamepad connection
↓
ControMax automatically detects via navigator.getGamepads()
↓
miscUiState.usingGamepadInput = true (set in event handlers)
↓
UI switches to gamepad mode
↓
Gamepad cursor becomes visible
```

## Input Mapping

### Movement Controls
```typescript
// Left stick - character movement
movementVector: '2d'  // Provides x/z coordinates
// Right stick - camera rotation  
stickMovement: { stick: 'right', vector: {x, z} }
```

### Button Mappings
```typescript
{
  // Face buttons
  jump: 'A',              // Bottom button (X on PlayStation)
  inventory: 'X',         // Left button (Square on PlayStation) 
  drop: 'B',              // Right button (Circle on PlayStation)
  // Triggers
  attackDestroy: 'Right Trigger',
  interactPlace: 'Left Trigger',
  // Bumpers
  nextHotbarSlot: 'Right Bumper',
  prevHotbarSlot: 'Left Bumper',
  // Sticks
  toggleSneakOrDown: 'Right Stick',  // Click
  sprint: 'Left Stick',              // Click
  // Menu/UI
  pauseMenu: 'Start',
  back: 'B',
  leftClick: 'A',         // For UI navigation
  rightClick: 'Y',        // Top button (Triangle on PlayStation)
}
```

## Event Flow

### 1. Movement Events
```
Gamepad stick input
↓
ControMax detects movement
↓
'movementUpdate' event fired (src/controls.ts line 132)
↓
If gamepad cursor visible: move cursor
↓ 
Else: update bot movement state
↓
Bot moves in Minecraft world
```

### 2. Camera Movement
```
Right stick input
↓
'stickMovement' event fired (src/cameraRotationControls.ts line 58)
↓
Deadzone check (0.18 threshold)
↓
onCameraMove() called with 10x sensitivity
↓
Camera rotates in game
```

### 3. Button Press Events
```
Gamepad button pressed
↓
ControMax detects button state
↓
'trigger' event fired (src/controls.ts line 512)
↓
Command mapped to game action
↓
Game action executed (jump, attack, etc.)
```

## UI State Management

### Gamepad Mode Detection
```typescript
miscUiState.usingGamepadInput = gamepadIndex !== undefined
```

### Cursor Visibility Logic
```typescript
// Gamepad cursor shows when:
const doDisplay = usingGamepadInput && (hasModals || !gameLoaded)

// Hide mouse cursor during gameplay:
document.body.style.cursor = gameLoaded && !hasModals && usingGamepadInput ? 'none' : 'auto'
```

## Special Features

### 1. PlayStation Controller Detection
```typescript
// Detects PlayStation controllers for correct button icons
const hasPsGamepad = [...(navigator.getGamepads?.() ?? [])]
  .some(gp => gp?.id.match(/playstation|dualsense|dualshock/i))
```

### 2. VR Controller Support
- VR controllers are mapped as virtual gamepads
- Only right-hand controller generates gamepad events
- Seamless integration with existing gamepad system

### 3. Deadzone Handling
- **Movement**: 0.3 threshold for character movement
- **Camera**: 0.18 threshold for camera rotation  
- **Cursor**: 0.1 threshold for UI cursor movement

### 4. Cursor Movement in Menus
```typescript
// Left stick controls cursor when in menus
if (gamepadIndex !== undefined && gamepadUiCursorState.display) {
  moveGamepadCursorByPx(soleVector.x, true)   // X movement
  moveGamepadCursorByPx(soleVector.z, false)  // Y movement
  emitMousemove()  // Trigger hover events
}
```

## Configuration

### Polling Rate
```typescript
gamepadPollingInterval: 10  // 10ms = 100fps polling rate
```

### Custom Keybindings
- Stored in `appStorage.keybindings`
- Can be customized via keybindings screen
- Supports both keyboard and gamepad remapping

## Touch Integration

The gamepad system also integrates with touch controls:
- Touch buttons trigger the same ControMax events
- Unified command system for all input methods
- Seamless switching between input modes

## Debug Features

### ControDebug Component
- Shows pressed keys and active actions
- Enabled via `options.debugContro`
- Useful for debugging input issues

### Console Access
```javascript
// Global access for debugging
window.controMax  // Access to ControMax instance
window.miscUiState  // UI state including gamepad mode
```

## Flow Summary

1. **Initialization**: ControMax starts polling for gamepad input
2. **Detection**: Browser gamepad API reports connected controllers
3. **Mode Switch**: UI automatically switches to gamepad mode
4. **Input Processing**: Gamepad events are mapped to game commands
5. **Visual Feedback**: Gamepad cursor appears in menus
6. **Game Actions**: Commands are executed in the Minecraft bot

This system provides a seamless gamepad experience that automatically adapts the UI and controls based on the input method being used. 