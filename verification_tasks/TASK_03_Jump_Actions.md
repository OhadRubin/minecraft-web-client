# TASK 03: Jump Actions Verification

**Assigned Developer**: [DEV_NAME]  
**Estimated Time**: 2-3 hours  
**Priority**: MEDIUM (Common action)

## **Objective**
Verify that jump actions via keyboard (spacebar) and UI button trigger proper MCP data collection with correct timing.

## **Scope**
Test these jump actions:
- ⚠️ Jump (spacebar) → `jump` MCP tool (needs verification)
- ⚠️ Jump (UI button) → `jump` MCP tool (needs verification)

## **What You Need to Test**

### **1. Spacebar Jump**
```bash
# Test Protocol:
1. Start: python -m mc_pygame_controller.controller --data-collection
2. Press F5, enter task: "Testing spacebar jump"
3. Test jump patterns:
   - Single quick spacebar tap
   - Hold spacebar for 1 second (should be single jump)
   - Rapid repeated spacebar taps (multiple jumps)
   - Hold spacebar while moving (jump + movement)
4. Press F6 to save session
```

### **2. UI Button Jump**
```bash
# Test Protocol:
1. Start new session: "Testing jump button"
2. Test UI button jump:
   - Single click on jump button
   - Hold jump button for different durations
   - Rapid clicks on jump button
   - Jump button while using other controls
3. Save session
```

### **3. Combined Actions**
```bash
# Test Protocol:
1. Start new session: "Testing jump combinations"
2. Test realistic scenarios:
   - Jump while moving forward (W + spacebar)
   - Jump while looking around (camera + spacebar)
   - Jump while clicking (mining + jumping)
3. Save session
```

## **Expected MCP Traces**

### **Jump Action Should Generate:**
```json
{
  "tool": "jump",
  "parameters": {
    "duration": "short" | "medium" | "long"
  }
}
```

**Note**: Jump is typically instantaneous in Minecraft, so duration should usually be "short" regardless of how long spacebar is held.

## **Verification Points**

### **✅ Success Criteria:**
1. **Spacebar Detection**: Spacebar press triggers jump MCP action
2. **UI Button Works**: Jump button triggers jump MCP action  
3. **Correct Duration**: Duration calculated appropriately
4. **getBotStatus Called**: After each jump sequence
5. **No Conflicts**: Jump works with other simultaneous actions
6. **Session Data**: Jump conversations saved properly

### **❌ Failure Modes to Check:**
- Spacebar not triggering MCP collection
- UI button not triggering MCP collection
- Incorrect duration calculation
- Jump interfering with other actions
- Missing getBotStatus calls

## **Special Considerations**

### **Edge Detection Logic**
Jump uses "edge detection" (press/release) rather than continuous hold:
- Should trigger on spacebar DOWN, not UP
- Holding spacebar should only generate ONE jump action
- Multiple rapid taps should generate multiple jump actions

### **Combination Testing**
Jump often occurs with other actions:
- Jump + movement should generate separate MCP actions
- Jump + camera should work independently
- Verify no actions are lost when jumping

## **Deliverables**

### **1. Test Results Document** (`jump_test_results.md`)
```markdown
## Spacebar Jump Tests
- [✅/❌] Single spacebar tap triggers jump MCP action
- [✅/❌] Held spacebar only generates 1 jump action
- [✅/❌] Rapid taps generate multiple jump actions
- [✅/❌] Duration calculated correctly
- [Console log snippet]

## UI Button Jump Tests
- [✅/❌] Jump button triggers jump MCP action
- [✅/❌] Button behavior matches spacebar behavior
- [Console log snippet]

## Combination Tests
- [✅/❌] Jump + movement works (separate MCP actions)
- [✅/❌] Jump + camera works independently
- [✅/❌] No action conflicts or lost actions
- [Console log snippet]

## Edge Detection Verification
- [✅/❌] Jump triggers on key down, not up
- [✅/❌] Held key doesn't spam jump actions
- [Evidence: timing analysis]
```

### **2. Sample Session Files**
- `session_spacebar_jumps.json`
- `session_button_jumps.json`
- `session_jump_combinations.json`

### **3. Timing Analysis**
Verify edge detection works correctly:
```markdown
| Test Case | Expected Behavior | Actual Behavior | ✅/❌ |
|-----------|-------------------|-----------------|-------|
| Quick tap | 1 jump action     | [result]        |       |
| 2s hold   | 1 jump action     | [result]        |       |
| 3 rapid taps | 3 jump actions | [result]        |       |
```

## **Key Files to Examine**

- `mc_pygame_controller/action_handler.py` (lines ~220-250) - Jump handling & edge detection
- `mc_pygame_controller/ui_manager.py` (lines ~290-320) - UI button jump processing
- `mc_pygame_controller/mode_strategy.py` - `handle_timed_action()` for jump
- `mc_pygame_controller/controller_state.py` - Action state management

## **Key Code to Review**

Look for edge detection logic:
```python
# In action_handler.py - verify this pattern:
def _detect_key_edge(self, key_name: str, current_state: bool) -> tuple[bool, bool]:
    """Detect key press/release edges. Returns (just_pressed, just_released)"""
    last_state = self.state.last_key_states.get(key_name, False)
    self.state.last_key_states[key_name] = current_state

    just_pressed = current_state and not last_state
    just_released = not current_state and last_state

    return just_pressed, just_released
```

## **Debug Commands**

```bash
# Start with extra debugging
python -m mc_pygame_controller.controller --data-collection

# Watch for these console patterns:
# On spacebar press: "JUMP DOWN - sending command"
# MCP action queued: "📋 Queued MCP action: jump"
# getBotStatus: "🔄 Executing MCP tool: getBotStatus"
```

## **Questions to Answer**

1. Does jump use `handle_timed_action()` or `handle_simple_action()`?
2. Is the duration calculation meaningful for jump actions?
3. Do simultaneous actions (jump + move) create separate MCP sequences?
4. Are there any UI responsiveness issues with jump button?

**DEADLINE**: [SET_DEADLINE]  
**Contact**: [LEAD_DEV] for questions 