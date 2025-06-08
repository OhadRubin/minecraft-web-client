# TASK 04: Toggle Actions Verification

**Assigned Developer**: [DEV_NAME]  
**Estimated Time**: 2-3 hours  
**Priority**: MEDIUM (Gameplay modifiers)

## **Objective**
Verify that toggle actions (sneak/sprint) via keyboard and UI buttons trigger proper MCP data collection with correct state management.

## **Scope**
Test these toggle actions:
- ⚠️ Sneak toggle → `sneak` MCP tool (needs verification)
- ⚠️ Sprint toggle → `sprint` MCP tool (needs verification)

## **What You Need to Test**

### **1. Sneak Toggle**
```bash
# Test Protocol:
1. Start: python -m mc_pygame_controller.controller --data-collection
2. Press F5, enter task: "Testing sneak toggle"
3. Test sneak patterns:
   - Toggle sneak ON, wait 2 seconds, toggle OFF
   - Rapid sneak toggle on/off/on/off
   - Sneak while moving (should change movement speed)
   - Sneak via button vs keyboard
4. Press F6 to save session
```

### **2. Sprint Toggle**
```bash
# Test Protocol:
1. Start new session: "Testing sprint toggle"
2. Test sprint patterns:
   - Toggle sprint ON, wait 2 seconds, toggle OFF
   - Rapid sprint toggle on/off/on/off
   - Sprint while moving (should change movement speed)
   - Sprint via button vs keyboard
3. Save session
```

### **3. State Combinations**
```bash
# Test Protocol:
1. Start new session: "Testing toggle combinations"
2. Test state interactions:
   - Sneak + Sprint (can you do both?)
   - Toggle states while moving
   - Toggle states while jumping
   - Toggle states while clicking
3. Save session
```

## **Expected MCP Traces**

### **Sneak Action Should Generate:**
```json
{
  "tool": "sneak",
  "parameters": {
    "state": true | false
  }
}
```

### **Sprint Action Should Generate:**
```json
{
  "tool": "sprint",
  "parameters": {
    "state": true | false
  }
}
```

## **Critical State Management**

### **Toggle Logic:**
- Each toggle should generate ONE MCP action with new state
- ON toggle: `{"state": true}`
- OFF toggle: `{"state": false}`
- Multiple rapid toggles should generate multiple MCP actions

### **State Tracking:**
- System should track current sneak/sprint state
- Only send MCP action when state actually changes
- No duplicate actions for same state

## **Verification Points**

### **✅ Success Criteria:**
1. **State Changes**: Each toggle generates MCP action with correct state
2. **No Duplicates**: Same state doesn't generate multiple actions
3. **Both Input Methods**: Keyboard and UI buttons both work
4. **State Persistence**: States maintained correctly across actions
5. **getBotStatus Called**: After each toggle sequence
6. **Realistic Behavior**: Toggle states affect other actions appropriately

### **❌ Failure Modes to Check:**
- Toggle not triggering MCP collection
- Wrong state values (always true, always false)
- Duplicate actions for same state
- State not persisting correctly
- Conflicts between sneak and sprint
- Missing getBotStatus calls

## **Deliverables**

### **1. Test Results Document** (`toggle_test_results.md`)
```markdown
## Sneak Toggle Tests
- [✅/❌] Sneak ON generates {"state": true}
- [✅/❌] Sneak OFF generates {"state": false}
- [✅/❌] No duplicate actions for same state
- [✅/❌] Keyboard and button both work
- [Console log snippet]

## Sprint Toggle Tests
- [✅/❌] Sprint ON generates {"state": true}
- [✅/❌] Sprint OFF generates {"state": false}
- [✅/❌] State tracking works correctly
- [Console log snippet]

## State Management Tests
- [✅/❌] Multiple rapid toggles work correctly
- [✅/❌] States persist across other actions
- [✅/❌] No conflicts between sneak and sprint
- [Evidence: state transition log]

## Integration Tests
- [✅/❌] Toggle + movement works correctly
- [✅/❌] Toggle + jumping works correctly
- [✅/❌] Toggle + clicking works correctly
```

### **2. Sample Session Files**
- `session_sneak_toggles.json`
- `session_sprint_toggles.json`
- `session_toggle_combinations.json`

### **3. State Transition Analysis**
Track state changes to verify logic:
```markdown
| Action | Expected State | Actual MCP | Current State | ✅/❌ |
|--------|----------------|------------|---------------|-------|
| Sneak ON | {"state": true} | [result] | sneak=true | |
| Sneak ON (again) | No action | [result] | sneak=true | |
| Sneak OFF | {"state": false} | [result] | sneak=false | |
| Sprint ON | {"state": true} | [result] | sprint=true | |
```

## **Key Files to Examine**

- `mc_pygame_controller/action_handler.py` (lines ~250-280) - Toggle handling
- `mc_pygame_controller/mode_strategy.py` - `handle_toggle_action()`
- `mc_pygame_controller/controller_state.py` - State tracking
- `mc_pygame_controller/ui_manager.py` - UI toggle buttons

## **Key Code to Review**

Look for toggle state management:
```python
# In action_handler.py - verify this pattern:
def _handle_toggle_action(self, action_name: str, toggled: bool, pygame_control: str, mcp_tool: str):
    """Generic handler for toggle actions (sneak, sprint)"""
    state = self.state.action_states[action_name]

    if toggled != state["active"]:  # Only act on state change
        self.strategy.handle_toggle_action(mcp_tool, toggled, pygame_control)
        state["active"] = toggled
```

## **Debug Commands**

```bash
# Start with state debugging
python -m mc_pygame_controller.controller --data-collection

# Watch for these patterns:
# On sneak toggle: "📋 Queued MCP action: sneak"
# State change: "State change: sneak=true"
# No duplicate: Should NOT see same state twice in a row
```

## **Questions to Answer**

1. Are toggle states tracked correctly in `controller_state.py`?
2. Does `handle_toggle_action()` prevent duplicate state actions?
3. Can sneak and sprint be active simultaneously?
4. Do toggle states affect movement/click actions appropriately?
5. Are there any UI visual indicators for toggle states?

**DEADLINE**: [SET_DEADLINE]  
**Contact**: [LEAD_DEV] for questions 