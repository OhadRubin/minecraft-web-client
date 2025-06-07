# Inventory Interaction Debug Guide: pygame vs MCP Mode

## Issue Summary

**Problem**: Inventory item pickup and placement works in pygame mode but fails in MCP mode, despite using the same UI interface.

**Impact**: Cannot record complete inventory management workflows in MCP mode, affecting training data quality for 3D spatial reasoning research.

## Current Behavior Analysis

### Pygame Mode (Working) ✅
- **Click Detection**: Direct pygame mouse events
- **Command Generation**: Immediate WebSocket commands
- **Inventory Response**: Items can be picked up and placed
- **UI Feedback**: Cursor shows item drag, slots highlight

### MCP Mode (Broken) ❌  
- **Click Detection**: Mouse events through dual event loop
- **Command Generation**: `documentMouseEvent` WebSocket commands
- **Inventory Response**: No item interaction occurs
- **UI Feedback**: No visual response to clicks

## WebSocket Command Comparison

### Pygame Mode Commands
Based on working inventory interaction, pygame mode likely sends:
```json
{"type": "leftDown"}
{"type": "leftUp"} 
```

### MCP Mode Commands  
From logs, MCP mode sends:
```json
{"type": "documentMouseEvent", "button": 0, "action": "down", "updateMouse": true}
{"type": "documentMouseEvent", "button": 0, "action": "up", "updateMouse": false}
```

## Root Cause Investigation

### Hypothesis 1: Command Type Mismatch
**Theory**: MCP mode sends `documentMouseEvent` while pygame mode sends `leftDown/leftUp`, and the web client handles them differently.

**Evidence**: Different command structures in logs
**Test**: Compare actual pygame mode commands during inventory interaction

### Hypothesis 2: Coordinate System Issues
**Theory**: MCP mode doesn't preserve click coordinates for UI elements, so inventory slots don't receive click events.

**Evidence**: `documentMouseEvent` has no `clientX/clientY` coordinates
**Test**: Check if pygame mode includes coordinate data

### Hypothesis 3: Event Routing Differences
**Theory**: Different event loops in pygame vs MCP mode route mouse events through different code paths.

**Evidence**: Dual event loop architecture documented in README
**Test**: Trace event handling in both modes

### Hypothesis 4: UI State Conflicts  
**Theory**: MCP mode's gamepad emulation interferes with inventory UI click detection.

**Evidence**: Recent gamepad cursor changes might affect click handling
**Test**: Disable gamepad cursor in MCP mode temporarily

## Debugging Protocol

### Phase 1: Command Comparison
1. **Enable pygame mode debug logging**:
   ```python
   # In mc_pygame_controller/controller_base.py
   def handle_inventory_click(self, button, pos):
       print(f"[PYGAME] Inventory click: button={button}, pos={pos}")
       print(f"[PYGAME] Sending command: {command}")
   ```

2. **Capture pygame mode inventory interaction**:
   - Start pygame mode
   - Open inventory  
   - Pick up item
   - Record exact WebSocket commands sent

3. **Compare with MCP mode commands**:
   - Start MCP mode
   - Open inventory
   - Attempt same interaction
   - Compare command differences

### Phase 2: Event Path Tracing
1. **Trace pygame event handling**:
   ```python
   # Add to _run_pygame_loop() around line 796-815
   if event.type == pygame.MOUSEBUTTONDOWN:
       print(f"[PYGAME EVENT] Mouse down: {event.pos}, button: {event.button}")
       if self.inventory_area.collidepoint(event.pos):
           print(f"[PYGAME EVENT] Click in inventory area")
   ```

2. **Trace MCP event handling**:
   ```python
   # Add to animation_loop() around line 1055-1074  
   if mouse_pressed:
       print(f"[MCP EVENT] Mouse pressed: {mouse_pos}")
       if self.inventory_area.collidepoint(mouse_pos):
           print(f"[MCP EVENT] Click in inventory area")
   ```

### Phase 3: WebSocket Command Analysis
1. **Monitor WebSocket traffic** in browser dev tools during:
   - Pygame mode inventory interaction (working)
   - MCP mode inventory interaction (broken)

2. **Compare `wsCommandClient.ts` handling**:
   - How are `leftDown/leftUp` processed?
   - How are `documentMouseEvent` processed?
   - Do they reach the same inventory UI code?

### Phase 4: UI Click Detection
1. **Test direct click simulation** in both modes:
   ```javascript
   // In browser console during inventory interaction
   const inventorySlot = document.querySelector('[data-inventory-slot="0"]');
   inventorySlot.click(); // Does this work in both modes?
   ```

2. **Check gamepad cursor interference**:
   ```javascript
   // Test if gamepad cursor affects inventory clicks
   console.log('miscUiState.usingGamepadInput:', miscUiState.usingGamepadInput);
   console.log('wsCursorState.usingWsInput:', wsCursorState.usingWsInput);
   ```

## Gamepad System Insights for Debugging

### Current Gamepad Implementation

The Minecraft web client has a sophisticated gamepad system that may be interfering with inventory interactions in MCP mode. Understanding this system is crucial for debugging the inventory issue.

#### Gamepad Cursor System (`src/react/GamepadUiCursor.tsx`)
- **Purpose**: Shows a visual crosshair cursor when using gamepad input in menus
- **Activation**: Appears when `miscUiState.usingGamepadInput = true` AND (in modals OR game not loaded)  
- **Key Behavior**: Hides mouse cursor during gameplay but shows gamepad cursor in inventory

```typescript
const doDisplay = usingGamepadInput && (hasModals || !gameLoaded)
document.body.style.cursor = gameLoaded && !hasModals && usingGamepadInput ? 'none' : 'auto'
```

#### Recent WebSocket Integration Changes
**Critical Discovery**: Recent changes to `wsCommandClient.ts` now set `miscUiState.usingGamepadInput = true` when WebSocket commands are received:

```typescript
async execute (cmd: MouseCommand) {
  wsCursorState.usingWsInput = true
  miscUiState.usingGamepadInput = true  // This was recently added
  // ... rest of command handling
}
```

**Impact**: This means MCP mode now triggers gamepad cursor behavior, which could interfere with inventory clicks.

#### Smart Click Handling Implementation  
**Recent Enhancement**: The WebSocket command handler now has smart click detection that behaves differently when gamepad mode is active:

```typescript
// In leftDown case
if (miscUiState.usingGamepadInput && wsCursorState.usingWsInput) {
  // Click at cursor position for inventory/UI
  const x = (wsCursorState.x / 100) * window.innerWidth
  const y = (wsCursorState.y / 100) * window.innerHeight
  const elementAtCursor = document.elementFromPoint(x, y)
  elementAtCursor.dispatchEvent(new MouseEvent('mousedown', {...}))
} else {
  // Fallback to bot commands for game world
  this.bot.leftClickStart()
}
```

### Potential Gamepad-Related Issues

#### Issue 1: Cursor Position Mismatch
**Problem**: MCP mode might be clicking at gamepad cursor position instead of actual mouse position.

**Investigation**:
```javascript
// Check cursor positions during inventory interaction
console.log('wsCursorState:', wsCursorState.x, wsCursorState.y);
console.log('Mouse position:', event.clientX, event.clientY);
console.log('Element at cursor:', document.elementFromPoint(x, y));
```

#### Issue 2: Event Path Conflicts
**Problem**: Gamepad cursor system might be intercepting mouse events before they reach inventory UI.

**Investigation**:
- Check if inventory slots receive `mousedown`/`mouseup` events in both modes
- Verify event propagation isn't stopped by gamepad cursor handlers

#### Issue 3: State Flag Interactions
**Problem**: Multiple input state flags might conflict:
- `miscUiState.usingGamepadInput` (enables gamepad cursor)
- `wsCursorState.usingWsInput` (enables WebSocket cursor control)
- Native inventory UI mouse handling

**Investigation**:
```javascript
// Monitor all relevant state flags
console.log('State flags:', {
  usingGamepadInput: miscUiState.usingGamepadInput,
  usingWsInput: wsCursorState.usingWsInput,
  gameLoaded: miscUiState.gameLoaded,
  hasModals: activeModalStack.length > 0
});
```

### Gamepad Architecture Patterns

#### VR Controller Emulation Pattern
**Discovery**: The system already has virtual gamepad emulation for VR controllers in `renderer/viewer/three/world/vr.ts`:

```typescript
// VR controllers create virtual gamepad events
const event = new Event('gamepadconnected')
event.gamepad = { ...gamepad, mapping: 'standard', index: virtualGamepadIndex }
window.dispatchEvent(event)

// Override navigator.getGamepads() to inject virtual gamepad
navigator.getGamepads = () => {
  return [...originalGamepads, virtualGamepad]
}
```

**Relevance**: This proves the system can handle virtual gamepad input, but MCP mode uses WebSocket commands instead.

#### ControMax Integration  
**Key System**: The `ControMax` library handles gamepad input detection and mapping:
- Polls `navigator.getGamepads()` every 10ms
- Automatically sets `miscUiState.usingGamepadInput` when real gamepads detected
- Maps gamepad buttons to game commands

**MCP Mode Conflict**: MCP mode manually sets `usingGamepadInput = true` without actually emulating a gamepad, which might confuse the system.

### Debugging Gamepad-Specific Issues

#### Test 1: Disable Gamepad Mode in MCP
```typescript
// Temporarily comment out in wsCommandClient.ts
// miscUiState.usingGamepadInput = true

// Test if inventory works without gamepad cursor active
```

#### Test 2: Cursor Position Verification
```javascript
// In browser console during MCP mode inventory interaction
const inventory = document.querySelector('.inventory-container');
const rect = inventory.getBoundingClientRect();
console.log('Inventory bounds:', rect);
console.log('Cursor position:', wsCursorState.x + '%', wsCursorState.y + '%');
console.log('Actual coordinates:', 
  (wsCursorState.x / 100) * window.innerWidth,
  (wsCursorState.y / 100) * window.innerHeight
);
```

#### Test 3: Event Propagation Analysis
```javascript
// Add to inventory elements
element.addEventListener('mousedown', (e) => {
  console.log('Inventory mousedown:', e.target, e.clientX, e.clientY);
  console.log('Event source:', e.isTrusted ? 'real' : 'synthetic');
});
```

### Recommended Gamepad-Aware Solutions

#### Option A: Coordinate Synchronization
Ensure MCP mode cursor position matches actual click coordinates:
```python
# In pygame controller, when sending mouse events
def send_mouse_event_with_position(self, action, pygame_pos):
    # Convert pygame coordinates to web coordinates  
    web_x = (pygame_pos[0] / self.window_width) * 100
    web_y = (pygame_pos[1] / self.window_height) * 100
    
    return {
        "type": "cursor",  # Update cursor position first
        "x": web_x,
        "z": web_y
    }, {
        "type": "leftDown" if action == "down" else "leftUp"
    }
```

#### Option B: Bypass Gamepad Cursor for Inventory
```typescript
// In wsCommandClient.ts, modify click handling
if (miscUiState.usingGamepadInput && wsCursorState.usingWsInput) {
  // Check if clicking in inventory area
  const inventoryElement = document.querySelector('.inventory-container');
  const isInventoryClick = inventoryElement?.contains(document.elementFromPoint(x, y));
  
  if (isInventoryClick) {
    // Use direct coordinates instead of cursor position
    // for inventory interactions
  }
}
```

#### Option C: True Gamepad Emulation  
Follow the VR controller pattern to create a virtual gamepad for MCP mode:
```typescript
// Create virtual gamepad that ControMax can detect
const virtualGamepad = {
  axes: [0, 0, 0, 0],
  buttons: Array(17).fill({pressed: false, touched: false, value: 0}),
  connected: true,
  mapping: 'standard',
  id: 'MCP Virtual Gamepad',
  index: 5
};
```

This gamepad-aware debugging approach should help identify whether the inventory interaction issue is related to the gamepad cursor system interfering with normal mouse event handling.

## Proposed Solutions

### Solution 1: Unify Command Types
**Approach**: Make MCP mode send `leftDown/leftUp` commands instead of `documentMouseEvent`.

**Implementation**:
```python
# In mc_pygame_controller/controller_base.py
def handle_click_mcp_mode(self, button, pos):
    if button == 1:  # Left click
        command = {"type": "leftDown"}
    elif button == 3:  # Right click  
        command = {"type": "rightDown"}
    
    self.send_command_sync(command)
    
    # Send corresponding up command after delay
    asyncio.create_task(self.send_delayed_up_command(button))
```

### Solution 2: Add Coordinates to documentMouseEvent
**Approach**: Enhance `documentMouseEvent` to include click coordinates.

**Implementation**:
```python
# In pygame controller
def generate_document_mouse_event(self, button, action, pos):
    return {
        "type": "documentMouseEvent",
        "button": button, 
        "action": action,
        "clientX": pos[0],
        "clientY": pos[1], 
        "updateMouse": True
    }
```

**Web client update**:
```typescript
// In wsCommandClient.ts, enhance documentMouseEvent handling
case 'documentMouseEvent': {
  const event = new MouseEvent('mouse' + cmd.action, {
    bubbles: true,
    cancelable: true,
    clientX: cmd.clientX || 0,  // Add coordinate support
    clientY: cmd.clientY || 0,
    button: cmd.button,
    buttons: cmd.button === 0 ? 1 : 2
  });
  
  // Use coordinates to find target element
  const targetElement = document.elementFromPoint(cmd.clientX, cmd.clientY);
  if (targetElement) {
    targetElement.dispatchEvent(event);
  }
}
```

### Solution 3: Mode-Specific Click Handlers
**Approach**: Create separate click handling for inventory interactions in each mode.

**Implementation**:
```python
class InventoryClickHandler:
    def __init__(self, mode):
        self.mode = mode
    
    def handle_inventory_click(self, pos, button):
        if self.mode == "pygame":
            return self._handle_pygame_inventory_click(pos, button)
        elif self.mode == "mcp":
            return self._handle_mcp_inventory_click(pos, button)
    
    def _handle_pygame_inventory_click(self, pos, button):
        # Current working implementation
        pass
    
    def _handle_mcp_inventory_click(self, pos, button):
        # Enhanced implementation with coordinates
        pass
```

### Solution 4: Event Loop Unification (Long-term)
**Approach**: Eliminate dual event loops to ensure consistent click handling.

**Benefits**: 
- Fixes inventory issue permanently
- Eliminates other mode inconsistencies
- Reduces maintenance burden

**Implementation**: Follow the gamepad emulation architecture proposed earlier.

## Testing Checklist

### Basic Functionality Tests
- [ ] Can open inventory in both modes
- [ ] Can see cursor/highlighting in both modes  
- [ ] Can close inventory in both modes

### Item Interaction Tests
- [ ] Pick up single item (pygame mode)
- [ ] Pick up single item (MCP mode)
- [ ] Move item between slots (pygame mode)
- [ ] Move item between slots (MCP mode)
- [ ] Split item stack (pygame mode)
- [ ] Split item stack (MCP mode)

### Edge Case Tests
- [ ] Click empty slot (both modes)
- [ ] Click outside inventory (both modes)
- [ ] Rapid clicking (both modes)
- [ ] Hold and drag (both modes)

### Integration Tests
- [ ] Inventory interaction while recording trajectory
- [ ] Inventory interaction with gamepad cursor active
- [ ] Inventory interaction during MCP tool execution

## Success Criteria

1. **Functional Parity**: MCP mode inventory interactions work identically to pygame mode
2. **Coordinate Preservation**: Click coordinates reach inventory UI elements
3. **Visual Feedback**: Inventory slots highlight and respond in both modes
4. **Training Data**: Complete inventory workflows can be recorded in MCP mode
5. **No Regression**: Pygame mode continues to work perfectly

## Implementation Priority

1. **Phase 1** (Quick Fix): Solution 1 - Unify command types
2. **Phase 2** (Robust Fix): Solution 2 - Add coordinates to documentMouseEvent  
3. **Phase 3** (Long-term): Solution 4 - Event loop unification

## Related Files

- `mc_pygame_controller/controller_base.py` - Dual event loops (lines 796-815, 1055-1074)
- `src/wsCommandClient.ts` - WebSocket command handling
- `src/react/GamepadUiCursor.tsx` - Gamepad cursor that might interfere
- `src/globalState.ts` - UI state management
- `server.js` - WebSocket relay server

## Next Steps

1. **Start with Phase 1 debugging** to identify exact command differences
2. **Implement Solution 1** as immediate fix for research needs
3. **Plan Solution 2** for robust long-term fix
4. **Consider Solution 4** as part of larger architectural refactoring

This guide provides a systematic approach to diagnosing and fixing the inventory interaction inconsistency between pygame and MCP modes. 