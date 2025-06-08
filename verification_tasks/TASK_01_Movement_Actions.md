# TASK 01: Movement Actions Verification

**Assigned Developer**: [DEV_NAME]  
**Estimated Time**: 4-6 hours  
**Priority**: HIGH (Core gameplay actions)

## **Objective**
Verify that all movement-related actions in pygame mode trigger proper MCP data collection with correct parameters.

## **Scope**
Test these movement actions:
- ✅ WASD keyboard movement → `walk` MCP tool
- ✅ Virtual joystick movement → `walk` MCP tool  
- ⚠️ Mouse camera look/drag → `lookAngle` MCP tool (needs verification)

## **What You Need to Test**

### **1. WASD Keyboard Movement**
```bash
# Test Protocol:
1. Start: python -m mc_pygame_controller.controller --data-collection
2. Press F5, enter task: "Testing WASD movement"
3. Test each key individually:
   - Hold W for 2 seconds, release
   - Hold S for 2 seconds, release  
   - Hold A for 2 seconds, release
   - Hold D for 2 seconds, release
4. Test combinations:
   - Hold W+A (diagonal), release
   - Hold S+D (diagonal), release
5. Press F6 to save session
```

### **2. Virtual Joystick Movement**
```bash
# Test Protocol:
1. Start new session: "Testing joystick movement"
2. Use mouse to drag virtual joystick:
   - Drag to each cardinal direction (N,S,E,W)
   - Drag to diagonal positions (NE,NW,SE,SW)  
   - Hold in position for 2+ seconds
   - Release to center
3. Save session
```

### **3. Camera Look/Drag**
```bash
# Test Protocol:
1. Start new session: "Testing camera movement"
2. Perform camera actions:
   - Click and drag mouse in camera area (horizontal sweep)
   - Click and drag vertically (look up/down)
   - Quick flick movements
   - Slow precise movements
3. Save session
```

## **Expected MCP Traces**

### **Walk Actions Should Generate:**
```json
{
  "tool": "walk",
  "parameters": {
    "duration": [calculated_based_on_magnitude]
  }
}
```

### **LookAngle Actions Should Generate:**
```json
{
  "tool": "lookAngle", 
  "parameters": {
    "xAngle": [degrees],
    "yAngle": [degrees],
    "speed": "normal"
  }
}
```

## **Verification Points**

### **✅ Success Criteria:**
1. **Console Output**: Each movement shows MCP action queued
2. **getBotStatus Called**: After each movement sequence  
3. **Session Data**: Saved sessions contain movement conversations
4. **No Errors**: No JSON serialization or sequence tracking errors
5. **Correct Parameters**: Duration/angles calculated properly

### **❌ Failure Modes to Check:**
- Movement not triggering MCP collection
- Incorrect duration calculations  
- Missing getBotStatus calls
- Camera movements not converting to lookAngle
- Session files empty or corrupted

## **Deliverables**

### **1. Test Results Document** (`movement_test_results.md`)
```markdown
## WASD Movement Tests
- [✅/❌] W key triggers walk MCP action
- [✅/❌] Duration calculated correctly  
- [✅/❌] getBotStatus called after movement
- [Console log snippet]

## Joystick Movement Tests  
- [✅/❌] Joystick drag triggers walk MCP action
- [✅/❌] Diagonal movements work correctly
- [Console log snippet]

## Camera Movement Tests
- [✅/❌] Mouse drag triggers lookAngle MCP action
- [✅/❌] Angle calculations are reasonable
- [Console log snippet]
```

### **2. Sample Session Files**
Save example session JSON files showing successful movement data collection:
- `session_wasd_test.json`
- `session_joystick_test.json` 
- `session_camera_test.json`

### **3. Bug Report** (if any issues found)
- Description of problem
- Steps to reproduce
- Expected vs actual behavior
- Console error logs

## **Key Files to Examine**

- `mc_pygame_controller/mode_strategy.py` (lines ~120-140) - `handle_movement()`
- `mc_pygame_controller/action_converter.py` (lines ~50-80) - Movement conversion logic
- `mc_pygame_controller/look_path.py` - Camera movement handling
- `mc_pygame_controller/ui_manager.py` (lines ~250-290) - Input processing

## **Quick Start Commands**

```bash
# Navigate to project
cd /Users/ohadr/minecraft-web-client

# Start data collection mode
python -m mc_pygame_controller.controller --data-collection

# Check session files after testing
ls -la collected_trajectories/
```

## **Questions for Code Review**

While testing, answer these questions:
1. Do all movement inputs trigger `_queue_parallel_mcp_execution()`?
2. Are duration calculations consistent between WASD and joystick?
3. Does camera movement properly convert pixel deltas to angle degrees?
4. Are there any movement actions that don't trigger data collection?

**DEADLINE**: [SET_DEADLINE]  
**Contact**: [LEAD_DEV] for questions 