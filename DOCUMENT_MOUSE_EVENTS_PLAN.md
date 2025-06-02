# Document Mouse Events Implementation Plan

## 🎯 Objective
Implement reliable left/right click functionality for the pygame controller by dispatching mouse events to the document, exactly mimicking how the Minecraft web client's touch buttons work.

## 📋 What We Learned

### **Touch Button Analysis (TouchAreasControls.tsx)**

#### How Touch Buttons Actually Work:
```typescript
// Break button (pickaxe) - Left Click
break() {
  if (!bot) return
  document.dispatchEvent(new MouseEvent('mousedown', { button: 0 }))
  bot.mouse.update()
  active = true
}

// Action button (circle) - Right Click  
action() {
  if (!bot) return
  document.dispatchEvent(new MouseEvent('mousedown', { button: 2 }))
  bot.mouse.update()
}
```

#### Key Insights:
1. **Document-level events** - Touch buttons dispatch `MouseEvent` to `document`, not to themselves
2. **Standard mouse buttons** - Uses `button: 0` (left) and `button: 2` (right)
3. **Bot state update** - Calls `bot.mouse.update()` after dispatching
4. **Event flow** - Document → Mouse Plugin → Bot Methods

### **Mouse Plugin Flow (mouse.ts)**
```typescript
document.addEventListener('mousedown', (e) => {
  // ... validation checks ...
  if (e.button === 0) {
    bot.leftClickStart()    // ← Final destination
  } else if (e.button === 2) {
    bot.rightClickStart()
  }
})

document.addEventListener('mouseup', (e) => {
  if (e.button === 0) {
    bot.leftClickEnd()
  } else if (e.button === 2) {
    bot.rightClickEnd()
  }
})
```

### **Why Our Previous Approaches Failed**

#### ❌ Direct WebSocket Commands:
- **Issue**: Rapid press/release cycles causing "lifting too fast"
- **Root cause**: Bypasses mouse plugin state management and validation
- **Evidence**: User reported "I'm not able to break anything it's lifting too fast"

#### ❌ DOM Element PointerEvents:
- **Issue**: Sent pointer events to touch button elements themselves
- **Root cause**: Touch buttons use React event system and pointer capture
- **Evidence**: Console showed events reaching elements but no action occurred

#### ❌ DOM Element MouseEvents:
- **Issue**: Sent mouse events to touch button elements
- **Root cause**: Touch buttons don't listen for mouse events, they generate them

## 🔧 The Correct Solution: Document Mouse Events

### **Why This Will Work:**
1. **Exact replication** - Uses the same event flow as working touch buttons
2. **Mouse plugin integration** - Leverages all existing validation and state management
3. **Proven path** - We know this path works because touch buttons use it successfully

### **Implementation Strategy:**

#### **WebSocket Command Type:**
```typescript
// Add new command type
type: 'documentMouseEvent'
button: 0 | 2  // 0 = left, 2 = right
action: 'down' | 'up'
updateMouse?: boolean  // Whether to call bot.mouse.update()
```

#### **WebSocket Handler:**
```typescript
case 'documentMouseEvent': {
  try {
    console.log(`[WsCommandClient] Dispatching document mouse event: button ${cmd.button} ${cmd.action}`)
    
    const event = new MouseEvent(`mouse${cmd.action}`, {
      bubbles: true,
      cancelable: true,
      button: cmd.button,
      buttons: cmd.action === 'down' ? (cmd.button === 0 ? 1 : 2) : 0
    })
    
    document.dispatchEvent(event)
    
    if (cmd.updateMouse && this.bot?.mouse?.update) {
      this.bot.mouse.update()
    }
    
    console.log(`[WsCommandClient] Successfully dispatched mouse${cmd.action} button ${cmd.button}`)
  } catch (error) {
    console.error('[WsCommandClient] Error in documentMouseEvent:', error)
  }
  break
}
```

#### **Pygame Controller Update:**
```python
def handle_left_click(self, pressed: bool):
    if pressed and not self.left_clicking:
        self.send_command_sync({
            "type": "documentMouseEvent",
            "button": 0,
            "action": "down",
            "updateMouse": True
        })
        self.left_clicking = True
    elif not pressed and self.left_clicking:
        self.send_command_sync({
            "type": "documentMouseEvent", 
            "button": 0,
            "action": "up",
            "updateMouse": False
        })
        self.left_clicking = False

def handle_right_click(self, pressed: bool):
    if pressed and not self.right_clicking:
        self.send_command_sync({
            "type": "documentMouseEvent",
            "button": 2, 
            "action": "down",
            "updateMouse": True
        })
        self.right_clicking = True
    elif not pressed and self.right_clicking:
        self.send_command_sync({
            "type": "documentMouseEvent",
            "button": 2,
            "action": "up", 
            "updateMouse": False
        })
        self.right_clicking = False
```

## 🧪 Testing Strategy

### **Phase 1: Manual Console Testing**
Test the approach manually to validate the concept:
```javascript
// Test left click (break blocks)
document.dispatchEvent(new MouseEvent('mousedown', { button: 0 }))
// Wait 2 seconds while pointing at block
document.dispatchEvent(new MouseEvent('mouseup', { button: 0 }))

// Test right click (place/use)
document.dispatchEvent(new MouseEvent('mousedown', { button: 2 }))
// Wait 1 second
document.dispatchEvent(new MouseEvent('mouseup', { button: 2 }))
```

### **Phase 2: WebSocket Implementation**
1. Add the new command type to interface
2. Implement the WebSocket handler
3. Test with simple WebSocket messages

### **Phase 3: Pygame Integration**
1. Update pygame controller handlers
2. Test button press/release cycles
3. Verify continuous action (hold to break)

### **Phase 4: Edge Case Testing**
1. Test rapid button presses
2. Test holding buttons
3. Test button state synchronization
4. Test with different game states (inventory open, etc.)

## 📊 Expected Behavior

### **Left Click (Break/Attack):**
- **Press**: Continuous breaking/attacking starts
- **Hold**: Breaking/attacking continues
- **Release**: Breaking/attacking stops
- **Validation**: Blocks should break, mobs should take damage

### **Right Click (Use/Place):**
- **Press**: Use item/place block starts  
- **Hold**: Continuous use (eating, charging bow, rapid placing)
- **Release**: Action stops
- **Validation**: Items should be used, blocks should be placed

## 🔄 Fallback Options

### **Option 1: Hybrid Approach**
If document events have issues, try:
```typescript
// Dispatch to document AND call bot methods
document.dispatchEvent(event)
this.bot.leftClickStart() // Direct call as backup
```

### **Option 2: Enhanced WebSocket Commands**
If document approach fails, improve direct WebSocket commands:
```typescript
// Add debouncing and state tracking
case 'leftDown':
  if (!this.leftClickActive) {
    this.bot.leftClickStart()
    this.leftClickActive = true
  }
  break
```

### **Option 3: Event Listener Override**
Hook into the existing event listeners:
```typescript
// Inject our events into the existing mouse event flow
const originalHandler = document.querySelector('body').onmousedown
// Trigger original handler with synthetic events
```

## 🚀 Implementation Order

1. **Manual console testing** (5 minutes)
2. **WebSocket command implementation** (15 minutes)
3. **Basic pygame integration** (10 minutes)
4. **Testing and refinement** (20 minutes)
5. **Documentation update** (10 minutes)

## 📈 Success Criteria

- ✅ Left click button breaks blocks continuously when held
- ✅ Right click button places blocks/uses items when held  
- ✅ No rapid press/release cycles
- ✅ Consistent behavior matching touch button functionality
- ✅ Works in all game states (survival, creative, spectator)
- ✅ Clean console output with proper event logging

## 🔍 Debugging Tools

### **Console Commands for Testing:**
```javascript
// Check mouse plugin state
console.log('Mouse buttons:', bot.mouse.buttons)
console.log('Control states:', bot.controlState)

// Monitor document events
document.addEventListener('mousedown', e => console.log('Doc mousedown:', e.button))
document.addEventListener('mouseup', e => console.log('Doc mouseup:', e.button))

// Test bot methods directly
bot.leftClickStart()
setTimeout(() => bot.leftClickEnd(), 2000)
```

### **WebSocket Message Logging:**
```typescript
// Enhanced logging in WebSocket handler
console.log(`[WsCommandClient] Mouse state before: buttons=${this.bot?.mouse?.buttons}`)
document.dispatchEvent(event)
console.log(`[WsCommandClient] Mouse state after: buttons=${this.bot?.mouse?.buttons}`)
```

This approach should provide **100% reliable** left/right click functionality by using the exact same event pathway that the proven-working touch interface uses. 