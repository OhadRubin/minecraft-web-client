# Right-Click Issue Analysis

## Problem Summary
Right-clicking functionality in the pygame controller is **mode-specific**: it works in **Creative mode** but is broken in **Survival mode**. This issue predates the MCP (Model Context Protocol) integration and was incorrectly attributed to recent WebSocket server routing changes.

## Corrected Timeline
- **6+ commits ago**: Right-clicking worked in Creative mode, but was already broken in Survival mode
- **MCP Integration**: WebSocket routing was modified, but this did not cause the right-click issue
- **Current Status**: Right-clicking still works in Creative mode, still broken in Survival mode

## Initial Misdiagnosis
The issue was incorrectly attributed to MCP integration changes because:
1. Testing was likely done primarily in Creative mode where right-clicking works
2. The WebSocket routing changes happened around the same time awareness of the issue increased
3. The mode-specific nature of the bug was not initially recognized

## Updated Root Cause Analysis

### Confirmed Working
- **Creative Mode**: Right-clicking works properly (both pygame and MCP)
- **Command Format**: `rightDown`/`rightUp` commands are correctly structured
- **Server Routing**: WebSocket message forwarding works correctly
- **Bot Client**: `wsCommandClient.ts` properly handles right-click commands

### The Real Issue: Survival Mode Incompatibility
The problem appears to be in how right-click commands are processed specifically in **Survival mode**:

#### Possible Causes
1. **Permission/Authentication**: Survival mode may require additional validation for right-click actions
2. **Resource Checks**: Survival mode might validate item availability before allowing right-click actions
3. **Game State Dependencies**: Right-click in Survival may depend on player state (hunger, health, etc.)
4. **Different Command Requirements**: Survival mode might need different or additional command parameters

## Mode-Specific Behavior Differences

### Creative Mode Right-Click
- Unlimited block placement
- No resource consumption validation
- Simplified permission model
- More permissive command execution

### Survival Mode Right-Click  
- Resource consumption required
- Item durability checks
- Hunger/health state validation
- Stricter permission validation
- May require additional game state synchronization

## Investigation Strategy (Revised)

### 1. Confirm Mode-Specific Behavior
- ✅ Test right-click in Creative mode (confirmed working)
- ✅ Test right-click in Survival mode (confirmed broken)
- Compare command flow between modes

### 2. Debug Survival Mode Command Processing
- Add logging to track right-click command execution in Survival mode
- Check if commands reach the bot client in Survival mode
- Verify bot client state when processing right-click in Survival mode

### 3. Compare Mode-Specific Requirements
- Investigate what additional validations Survival mode requires
- Check if right-click needs inventory/resource validation
- Look for mode-specific command handling differences

### 4. Bot Client State Analysis
- Verify bot is actually in Survival mode when expected
- Check bot inventory state during right-click attempts
- Monitor bot health/hunger status impact on right-click

## Server Routing Logic (Status: Working)
The WebSocket routing changes were **not the cause**:
```javascript
// This routing works correctly for both modes
if (pygameClients.has(ws)) {
    // Forward to bot clients - WORKS
}
```

## Command Format (Status: Correct)
Both pygame and MCP use the correct format:
- Pygame: `{"type": "rightDown"}` / `{"type": "rightUp"}`  
- MCP: `{"type": "rightDown"}` / `{"type": "rightUp"}`
- Bot handles: `bot.rightClickStart()` / `bot.rightClickEnd()`

## Next Steps (Updated)

1. **Immediate**: Test both modes to confirm the mode-specific behavior
2. **Debug**: Add detailed logging specifically for Survival mode right-click processing
3. **Compare**: Analyze differences in bot client behavior between Creative and Survival modes
4. **Investigate**: Look into Survival mode requirements for right-click actions
5. **Fix**: Address the Survival mode-specific right-click handling

## Files Involved
- `src/wsCommandClient.ts` - Bot client command processing (mode-dependent behavior?)
- `pygame_controller.py` - Pygame client (command format correct)
- `minecraft-mcp-server.ts` - MCP server (command format correct)
- Bot client core code - Mode-specific right-click handling

## Current Status
- **Creative Mode**: Right-click works correctly ✅
- **Survival Mode**: Right-click broken ❌
- **MCP Integration**: Not the root cause ✅
- **Command Routing**: Working correctly ✅

## Risk Assessment (Updated)
- **High**: Survival mode gameplay significantly impacted
- **Medium**: Mode-specific bug may indicate deeper game state synchronization issues
- **Low**: Creative mode functionality unaffected
- **Note**: Issue is older than initially thought, reducing urgency but confirming complexity

## Proposed Fix: Duration-Based Right-Click Commands

### Current Implementation Problem
The current right-click implementation sends separate `rightDown` and `rightUp` events:

```python
# pygame_controller.py - Current approach
def handle_right_click(self, pressed: bool):
    if pressed and not self.right_clicking:
        self.send_command_sync({"type": "rightDown"})
    elif not pressed and self.right_clicking:
        self.send_command_sync({"type": "rightUp"})
```

### Survival Mode Duration Requirements
In Survival mode, many right-click actions require **sustained input** for a specific duration:

- **Block Placement**: May need minimum hold time for proper placement
- **Eating/Drinking**: Requires holding right-click for full consumption duration  
- **Tool Usage**: Items like hoes, axes on logs, etc. may need sustained interaction
- **Door/Container Opening**: Might require minimum interaction time
- **Item Usage**: Bows, shields, and other items often need duration-based input

### Proposed Solution: Duration-Based Commands

#### Option 1: Single Command with Duration
Replace separate down/up events with a single duration-based command:

```python
# New approach - single command with duration
def handle_right_click_duration(self, duration_ms: int = 500):
    command = {
        "type": "rightClickWithDuration", 
        "duration": duration_ms
    }
    self.send_command_sync(command)
```

#### Option 2: Minimum Duration Enforcement
Ensure a minimum duration between down and up events:

```python
# Modified approach - enforced minimum duration  
def handle_right_click(self, pressed: bool):
    if pressed and not self.right_clicking:
        self.right_click_start_time = time.time()
        self.send_command_sync({"type": "rightDown"})
        self.right_clicking = True
    elif not pressed and self.right_clicking:
        # Ensure minimum duration (e.g., 200ms for Survival mode)
        elapsed = time.time() - self.right_click_start_time
        min_duration = 0.2  # 200ms
        if elapsed < min_duration:
            # Wait remaining time before sending up event
            time.sleep(min_duration - elapsed)
        self.send_command_sync({"type": "rightUp"})
        self.right_clicking = False
```

#### Option 3: Mode-Aware Duration
Detect game mode and adjust duration accordingly:

```python
# Mode-aware duration handling
def handle_right_click(self, pressed: bool):
    # In Creative: instant response (current behavior)
    # In Survival: enforced duration
    duration = self.get_mode_appropriate_duration()
    
    if self.game_mode == "survival":
        # Use duration-based approach
        if pressed and not self.right_clicking:
            self.send_right_click_with_duration(duration)
    else:
        # Use existing instant approach for Creative
        self.handle_right_click_instant(pressed)
```

### Bot Client Implementation
The bot client (`wsCommandClient.ts`) would need to support duration-based commands:

```typescript
case 'rightClickWithDuration':
  try {
    console.log(`[WsCommandClient] Right-click with duration: ${cmd.duration}ms`)
    if (typeof this.bot.rightClickStart === 'function') {
      this.bot.rightClickStart()
      
      // Hold for specified duration
      setTimeout(() => {
        if (typeof this.bot.rightClickEnd === 'function') {
          this.bot.rightClickEnd()
        }
      }, cmd.duration || 500) // Default 500ms
    }
  } catch (error) {
    console.error('[WsCommandClient] Error in rightClickWithDuration:', error)
  }
  break
```

### Implementation Priority
1. **Quick Fix**: Option 2 (minimum duration enforcement) - requires minimal changes
2. **Better Solution**: Option 1 (duration-based commands) - cleaner architecture  
3. **Optimal Solution**: Option 3 (mode-aware) - most robust but requires mode detection

### Testing Strategy for Duration Fix
1. Test various duration values (100ms, 200ms, 500ms, 1000ms)
2. Verify block placement works consistently in Survival mode
3. Test eating/drinking mechanics with duration commands
4. Ensure Creative mode functionality remains unaffected
5. Compare behavior with native Minecraft client timing 