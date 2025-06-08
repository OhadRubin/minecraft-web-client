# TASK 06: Hotbar Actions Verification

**Assigned Developer**: [DEV_NAME]  
**Estimated Time**: 2-3 hours  
**Priority**: HIGH (Item selection crucial)

## **Objective**
Verify that hotbar slot selection (1-9 keys and UI buttons) triggers proper MCP data collection with correct slot parameters.

## **Scope**
Test these hotbar actions:
- ⚠️ Hotbar selection (1-9 keys) → `setHotbarSlot` MCP tool (needs verification)
- ⚠️ Hotbar selection (UI buttons) → `setHotbarSlot` MCP tool (needs verification)

## **What You Need to Test**

### **1. Number Key Hotbar Selection**
```bash
# Test Protocol:
1. Start: python -m mc_pygame_controller.controller --data-collection
2. Press F5, enter task: "Testing hotbar number keys"
3. Test each number key:
   - Press 1 (slot 0)
   - Press 2 (slot 1)
   - Press 3 (slot 2)
   - ... through 9 (slot 8)
4. Test selection patterns:
   - 1 → 5 → 3 → 9 (random selections)
   - Rapid key presses (1,2,3,4,5...)
   - Same key twice (should it trigger twice?)
5. Press F6 to save session
```

### **2. UI Button Hotbar Selection**
```bash
# Test Protocol:
1. Start new session: "Testing hotbar UI buttons"
2. Test UI button clicks:
   - Click each hotbar slot button (1-9)
   - Click same slot multiple times
   - Click different slots in sequence
3. Save session
```

### **3. Hotbar State Management**
```bash
# Test Protocol:
1. Start new session: "Testing hotbar state"
2. Test state tracking:
   - Select slot 1, then slot 1 again (duplicate?)
   - Select slot 3, then slot 7, then slot 3 (return)
   - Hotbar selection while performing other actions
3. Save session
```

## **Expected MCP Traces**

### **Hotbar Selection Should Generate:**
```json
{
  "tool": "setHotbarSlot",
  "parameters": {
    "slot": 0  // 0-8 (keys 1-9 map to slots 0-8)
  }
}
```

**Key Mapping:**
- Key "1" → slot 0
- Key "2" → slot 1
- Key "3" → slot 2
- ...
- Key "9" → slot 8

## **Critical State Management**

### **Duplicate Prevention:**
- Should selecting the same slot twice generate MCP action?
- Or should it only trigger when slot actually changes?
- Check current implementation behavior

### **Slot Tracking:**
- System should track current selected slot
- Only generate MCP action on slot change
- Verify slot persistence across other actions

## **Verification Points**

### **✅ Success Criteria:**
1. **Number Keys Work**: All 1-9 keys trigger setHotbarSlot MCP actions
2. **UI Buttons Work**: All hotbar UI buttons trigger MCP actions
3. **Correct Slot Mapping**: Key 1=slot 0, Key 2=slot 1, etc.
4. **State Tracking**: System tracks current selected slot
5. **getBotStatus Called**: After each hotbar selection sequence
6. **Edge Detection**: Uses edge detection (not continuous hold)

### **❌ Failure Modes to Check:**
- Number keys not triggering MCP collection
- UI buttons not triggering MCP collection
- Wrong slot numbers (off-by-one errors)
- Duplicate actions for same slot
- Slot state not persisting
- Missing getBotStatus calls

## **Deliverables**

### **1. Test Results Document** (`hotbar_test_results.md`)
```markdown
## Number Key Tests
- [✅/❌] Key 1 triggers setHotbarSlot with slot=0
- [✅/❌] Key 2 triggers setHotbarSlot with slot=1
- [✅/❌] Key 9 triggers setHotbarSlot with slot=8
- [✅/❌] All keys 1-9 work correctly
- [✅/❌] Edge detection (no spam on hold)
- [Console log snippet]

## UI Button Tests
- [✅/❌] Hotbar buttons trigger setHotbarSlot
- [✅/❌] Button slots match key slots
- [✅/❌] All 9 hotbar buttons work
- [Console log snippet]

## State Management Tests
- [✅/❌] Same slot twice behavior verified
- [✅/❌] Slot state persists across actions
- [✅/❌] No duplicate actions for same slot
- [Evidence: state tracking log]

## Slot Mapping Verification
| Key | Expected Slot | Actual Slot | ✅/❌ |
|-----|---------------|-------------|-------|
| 1   | 0             | [result]    |       |
| 2   | 1             | [result]    |       |
| 3   | 2             | [result]    |       |
| ... | ...           | ...         |       |
| 9   | 8             | [result]    |       |
```

### **2. Sample Session Files**
- `session_hotbar_keys.json`
- `session_hotbar_buttons.json`
- `session_hotbar_state.json`

### **3. State Behavior Analysis**
```markdown
| Action | Previous Slot | New Slot | Expected MCP | Actual MCP | ✅/❌ |
|--------|---------------|----------|--------------|------------|-------|
| Press 1 | None | 0 | {"slot": 0} | [result] | |
| Press 1 again | 0 | 0 | No action? | [result] | |
| Press 5 | 0 | 4 | {"slot": 4} | [result] | |
```

## **Key Files to Examine**

- `mc_pygame_controller/action_handler.py` (lines ~350-390) - Hotbar edge detection
- `mc_pygame_controller/controller_state.py` - Current/last hotbar slot tracking
- `mc_pygame_controller/mode_strategy.py` - `handle_simple_action()` for hotbar
- `mc_pygame_controller/ui_manager.py` - Hotbar UI button processing

## **Key Code to Review**

Look for hotbar logic:
```python
# In action_handler.py - verify hotbar edge detection:
def process_edge_detections(self, keys_pressed):
    # Handle hotbar slot shortcuts (1-9 keys)
    for i, key in enumerate([pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, 
                           pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]):
        key_name = f"hotbar_{i}"
        just_pressed, _ = self._detect_key_edge(key_name, keys_pressed[key])
        
        if just_pressed:
            self.handle_hotbar_slot(i)  # i should be 0-8

# In handle_hotbar_slot - verify slot change detection:
def handle_hotbar_slot(self, slot: int):
    if 0 <= slot <= 8 and slot != self.state.last_hotbar_slot:
        # Only act if slot actually changed
```

## **Debug Commands**

```bash
# Start with hotbar debugging
python -m mc_pygame_controller.controller --data-collection

# Watch for these patterns:
# On key 1: "📋 Queued MCP action: setHotbarSlot" with slot=0
# On key 5: "📋 Queued MCP action: setHotbarSlot" with slot=4
# State change: "HOTBAR SLOT 1 - sending command" (slot+1 for display)
```

## **Questions to Answer**

1. Does the system prevent duplicate hotbar actions for same slot?
2. Are slot numbers 0-indexed (0-8) or 1-indexed (1-9)?
3. Do hotbar selections work while other actions are active?
4. Are there visual indicators for currently selected slot?
5. Does hotbar state persist across sessions/reconnections?

**DEADLINE**: [SET_DEADLINE]  
**Contact**: [LEAD_DEV] for questions 