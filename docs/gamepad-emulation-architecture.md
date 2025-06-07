# Gamepad Emulation Architecture for Unified Command Input

## Overview

This document explains how to use **gamepad emulation** to unify all command input sources (WebSocket, pygame controller, touch, MCP) into a single code path, eliminating the current duplication and complexity in the command system.

## Current Problem

The Minecraft web client currently has multiple disconnected command paths:

```
┌─ Gamepad Input ──→ ControMax ──→ Bot Commands
├─ Touch Input ────→ Touch Controls ──→ Bot Commands  
├─ Keyboard Input ─→ ControMax ──→ Bot Commands
├─ WebSocket Input ─→ wsCommandClient ──→ Bot Commands
└─ MCP Commands ───→ (future: should also unify)
```

This leads to:
- **Code duplication** across input handlers
- **Inconsistent behavior** between input methods  
- **Maintenance burden** when adding new commands
- **Testing complexity** with multiple code paths

## Solution: Gamepad Emulation Pattern

The VR system already demonstrates the perfect solution. Instead of creating separate command paths, **emulate a virtual gamepad** and let the existing ControMax system handle everything.

### How VR Controllers Work (Existing Implementation)

The VR system in `renderer/viewer/three/world/vr.ts` shows the pattern:

```typescript
// 1. Create virtual gamepad events
const virtualGamepadIndex = 4
const manageXrInputSource = ({ gamepad, handedness }, defaultHandedness, removeAction = false) => {
  if (handedness === 'right') {
    const event: any = new Event(removeAction ? 'gamepaddisconnected' : 'gamepadconnected')
    event.gamepad = removeAction ? connectedVirtualGamepad : { 
      ...gamepad, 
      mapping: 'standard', 
      index: virtualGamepadIndex 
    }
    connectedVirtualGamepad = event.gamepad
    window.dispatchEvent(event) // Let ControMax detect this "gamepad"
  }
}

// 2. Override navigator.getGamepads() to inject virtual gamepad
const originalGetGamepads = navigator.getGamepads.bind(navigator)
navigator.getGamepads = () => {
  const originalGamepads = originalGetGamepads()
  if (!hand1.xrInputSource || !hand2.xrInputSource) return originalGamepads
  return [
    ...originalGamepads,
    {
      axes: remapAxes(hand2.xrInputSource.gamepad.axes, hand1.xrInputSource.gamepad.axes),
      buttons: remapButtons(hand2.xrInputSource.gamepad.buttons, hand1.xrInputSource.gamepad.buttons),
      connected: true,
      mapping: 'standard',
      id: 'VR Virtual Gamepad',
      index: virtualGamepadIndex
    }
  ]
}
```

### Result: Perfect Integration

VR controllers get:
- ✅ Automatic gamepad cursor in menus
- ✅ All gamepad UI hints and behaviors  
- ✅ Consistent button mapping via ControMax
- ✅ Zero duplicate command logic
- ✅ Same behavior as real gamepads

## Proposed Unified Architecture

```
┌─ Real Gamepad ────┐
├─ Touch Input ─────┤
├─ WebSocket Input ─┤──→ Virtual Gamepad Emulator ──→ navigator.getGamepads() ──→ ControMax ──→ Bot Commands
├─ Pygame Input ────┤
└─ MCP Commands ────┘
```

### Implementation Strategy

#### 1. Create Virtual Gamepad Manager

```typescript
// src/virtualGamepadManager.ts
class VirtualGamepadManager {
  private virtualGamepadIndex = 5 // Use index 5 to avoid conflicts
  private virtualGamepad: Gamepad | null = null
  private buttonStates = new Array(17).fill(false) // Standard gamepad has 17 buttons
  private axesStates = [0, 0, 0, 0] // Left stick X/Y, Right stick X/Y
  
  constructor() {
    this.overrideGetGamepads()
  }
  
  // Convert WebSocket/pygame commands to gamepad state
  setButtonState(buttonIndex: number, pressed: boolean) {
    this.buttonStates[buttonIndex] = pressed
    this.updateVirtualGamepad()
  }
  
  setAxisState(axisIndex: number, value: number) {
    this.axesStates[axisIndex] = value  
    this.updateVirtualGamepad()
  }
  
  private updateVirtualGamepad() {
    this.virtualGamepad = {
      axes: [...this.axesStates],
      buttons: this.buttonStates.map(pressed => ({ pressed, touched: pressed, value: pressed ? 1 : 0 })),
      connected: true,
      mapping: 'standard',
      id: 'WebSocket Virtual Gamepad',
      index: this.virtualGamepadIndex,
      timestamp: performance.now()
    }
  }
  
  private overrideGetGamepads() {
    const originalGetGamepads = navigator.getGamepads.bind(navigator)
    navigator.getGamepads = () => {
      const originalGamepads = originalGetGamepads()
      if (!this.virtualGamepad) return originalGamepads
      
      const result = [...originalGamepads]
      result[this.virtualGamepadIndex] = this.virtualGamepad
      return result
    }
  }
  
  connect() {
    const event = new Event('gamepadconnected') as any
    event.gamepad = this.virtualGamepad
    window.dispatchEvent(event)
  }
  
  disconnect() {
    const event = new Event('gamepaddisconnected') as any  
    event.gamepad = this.virtualGamepad
    this.virtualGamepad = null
    window.dispatchEvent(event)
  }
}
```

#### 2. Command-to-Gamepad Mapping

```typescript
// src/commandToGamepadMapper.ts
import { MouseCommand } from './wsCommandClient'

const GAMEPAD_BUTTON_MAP = {
  // Standard gamepad button indices
  A: 0,           // Jump, UI select
  B: 1,           // Back, drop  
  X: 2,           // Inventory
  Y: 3,           // Right click
  LEFT_BUMPER: 4,     // Previous hotbar slot
  RIGHT_BUMPER: 5,    // Next hotbar slot  
  LEFT_TRIGGER: 6,    // Interact/place
  RIGHT_TRIGGER: 7,   // Attack/destroy
  BACK: 8,           // Pause menu
  START: 9,          // Pause menu
  LEFT_STICK: 10,    // Sprint
  RIGHT_STICK: 11,   // Sneak
}

class CommandToGamepadMapper {
  constructor(private virtualGamepad: VirtualGamepadManager) {}
  
  handleWebSocketCommand(cmd: MouseCommand) {
    switch (cmd.type) {
      case 'leftDown':
        this.virtualGamepad.setButtonState(GAMEPAD_BUTTON_MAP.RIGHT_TRIGGER, true)
        break
      case 'leftUp':  
        this.virtualGamepad.setButtonState(GAMEPAD_BUTTON_MAP.RIGHT_TRIGGER, false)
        break
      case 'rightDown':
        this.virtualGamepad.setButtonState(GAMEPAD_BUTTON_MAP.LEFT_TRIGGER, true)
        break
      case 'rightUp':
        this.virtualGamepad.setButtonState(GAMEPAD_BUTTON_MAP.LEFT_TRIGGER, false)
        break
      case 'move':
        // Map movement to left stick
        this.virtualGamepad.setAxisState(0, cmd.x ?? 0) // Left stick X
        this.virtualGamepad.setAxisState(1, cmd.z ?? 0) // Left stick Y  
        break
      case 'look':
        // Map camera to right stick  
        const sensitivity = 0.01
        this.virtualGamepad.setAxisState(2, (cmd.movementX ?? 0) * sensitivity) // Right stick X
        this.virtualGamepad.setAxisState(3, (cmd.movementY ?? 0) * sensitivity) // Right stick Y
        break
      case 'inventory':
        this.virtualGamepad.setButtonState(GAMEPAD_BUTTON_MAP.X, true)
        setTimeout(() => this.virtualGamepad.setButtonState(GAMEPAD_BUTTON_MAP.X, false), 50)
        break
      // ... handle other commands
    }
  }
}
```

#### 3. Replace wsCommandClient.ts

```typescript
// src/wsCommandClient.ts (simplified)
import { VirtualGamepadManager } from './virtualGamepadManager'
import { CommandToGamepadMapper } from './commandToGamepadMapper'

export function setupWsCommandClient(bot: any) {
  const virtualGamepad = new VirtualGamepadManager()
  const mapper = new CommandToGamepadMapper(virtualGamepad)
  
  // Connect WebSocket
  const ws = new WebSocket(wsUrl)
  
  ws.addEventListener('open', () => {
    console.log('[WsCommandClient] Connected, emulating gamepad')
    virtualGamepad.connect() // Dispatch gamepadconnected event
  })
  
  ws.addEventListener('message', ev => {
    try {
      const cmd = JSON.parse(ev.data as string) as MouseCommand
      mapper.handleWebSocketCommand(cmd) // Convert to gamepad input
    } catch (err) {
      console.error('[WsCommandClient] Invalid command', err)
    }
  })
  
  ws.addEventListener('close', () => {
    virtualGamepad.disconnect() // Dispatch gamepaddisconnected event
  })
}
```

## Benefits of This Approach

### 1. **Eliminates Code Duplication**
- ❌ **Before**: Separate command handling in `wsCommandClient.ts`, touch controls, etc.
- ✅ **After**: Single command path through ControMax

### 2. **Automatic UI Consistency** 
- ✅ Gamepad cursor appears automatically when using WebSocket/pygame
- ✅ All gamepad UI hints work (button prompts, etc.)
- ✅ Consistent behavior with real gamepads

### 3. **Simplifies Testing**
- ✅ Single code path to test
- ✅ Can test with real gamepads or virtual ones identically

### 4. **Future-Proof**
- ✅ New commands only need gamepad mapping, not separate handling
- ✅ MCP mode can use the same virtual gamepad approach
- ✅ Easy to add new input sources

### 5. **Zero Breaking Changes**
- ✅ Existing gamepad, keyboard, touch continue working
- ✅ WebSocket commands become more consistent, not less

## Migration Strategy

### Phase 1: Implement Virtual Gamepad Manager
1. Create `VirtualGamepadManager` class
2. Add command-to-gamepad mapping  
3. Test with simple commands (movement, look)

### Phase 2: Replace WebSocket Commands
1. Modify `wsCommandClient.ts` to use virtual gamepad
2. Remove direct bot command calls
3. Test all WebSocket command types

### Phase 3: Extend to Pygame Controller  
1. Have pygame controller emit virtual gamepad events
2. Eliminates the dual event loop problem mentioned in README
3. Single mouse tracking logic

### Phase 4: MCP Integration
1. MCP commands also create virtual gamepad events
2. Consistent behavior between pygame and MCP modes
3. Simplified architecture

## Technical Details

### Standard Gamepad Layout
```
Buttons:  [A, B, X, Y, LB, RB, LT, RT, Back, Start, LS, RS, DPad↑, DPad↓, DPad←, DPad→, Home]
Axes:     [LS.x, LS.y, RS.x, RS.y]
```

### Virtual Gamepad Index
- Use index `5` to avoid conflicts with real gamepads (typically 0-3)
- VR controllers use index `4`

### Event Timing
- Button press: Set state to `true`, dispatch immediately
- Button release: Set state to `false` after small delay (50ms) for single-press actions
- Continuous actions: Update state continuously (movement, camera)

## Implementation Files

1. **`src/virtualGamepadManager.ts`** - Core virtual gamepad emulation
2. **`src/commandToGamepadMapper.ts`** - WebSocket/pygame command mapping
3. **`src/wsCommandClient.ts`** - Simplified WebSocket client using virtual gamepad
4. **Update `mc_pygame_controller/`** - Use virtual gamepad instead of dual loops

## Conclusion

By following the VR controller pattern, we can **eliminate the entire wsCommandClient command handling system** and replace it with a simple virtual gamepad emulator. This gives us:

- **90% less code** in the command handling layer
- **100% consistency** with existing gamepad behavior  
- **Zero maintenance burden** for UI consistency
- **Future-proof architecture** for new input methods

The VR system proves this approach works perfectly - we just need to apply the same pattern to WebSocket and pygame inputs. 