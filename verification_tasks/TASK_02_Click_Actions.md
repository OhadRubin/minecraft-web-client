# TASK 02: Click Actions Verification

**Assigned Developer**: [DEV_NAME]  
**Estimated Time**: 3-4 hours  
**Priority**: HIGH (Core interaction)

## **Objective**
Verify that all click actions (left/right via UI buttons and direct mouse clicks) trigger proper MCP data collection without duplication errors.

## **Scope**
Test these click actions:
- ✅ Left click (via UI button) → `leftClick` MCP tool
- ✅ Left click (via direct mouse) → `leftClick` MCP tool
- ✅ Right click (via UI button) → `rightClick` MCP tool  
- ✅ Right click (via direct mouse) → `rightClick` MCP tool

## **What You Need to Test**

### **1. Left Click via UI Button**
```bash
# Test Protocol:
1. Start: python -m mc_pygame_controller.controller --data-collection
2. Press F5, enter task: "Testing left click button"
3. Click the left click UI button (bottom area):
   - Single quick click
   - Hold for 1 second, release
   - Hold for 3 seconds, release (long mining)
   - Multiple rapid clicks
4. Press F6 to save session
```

### **2. Left Click via Direct Mouse**
```bash
# Test Protocol:
1. Start new session: "Testing direct left click"
2. Click directly in main game area (not on UI buttons):
   - Single quick left click
   - Hold left mouse button down for 2 seconds
   - Multiple rapid left clicks
3. Save session
```

### **3. Right Click via UI Button**
```bash
# Test Protocol:
1. Start new session: "Testing right click button"
2. Click the right click UI button:
   - Single quick click
   - Hold for different durations
   - Rapid repeated clicks
3. Save session
```

### **4. Right Click via Direct Mouse**
```bash
# Test Protocol:
1. Start new session: "Testing direct right click" 
2. Right click in main game area:
   - Single quick right click
   - Hold right mouse button
   - Rapid right clicks
3. Save session
```

## **Expected MCP Traces**

### **Left Click Should Generate:**
```json
{
  "tool": "leftClick",
  "parameters": {
    "duration": "short" | "medium" | "long" | "very_long"
  }
}
```

### **Right Click Should Generate:**
```json
{
  "tool": "rightClick", 
  "parameters": {
    "duration": "short" | "medium" | "long" | "very_long"
  }
}
```

## **Critical Issues to Watch For**

### **🚨 Duplication Bug (FIXED - Verify Fix Works):**
Previously, mouse down + mouse up generated 2 separate leftClick actions.  
**Expected**: 1 click action per user click  
**Verify**: No duplicate actions in console or session files

### **Duration Calculation:**
- Quick clicks: "short" 
- 1-2 second holds: "medium"
- 2+ second holds: "long" or "very_long"

## **Verification Points**

### **✅ Success Criteria:**
1. **No Duplicates**: Each user click = exactly 1 MCP action
2. **Correct Duration**: Duration matches actual hold time
3. **getBotStatus Called**: After each click sequence
4. **Both Input Methods Work**: UI buttons and direct mouse clicks both work
5. **Session Data**: Complete conversations saved for each click

### **❌ Failure Modes to Check:**
- Duplicate leftClick/rightClick actions
- Wrong duration calculations
- UI button clicks not triggering MCP collection
- Direct mouse clicks not triggering MCP collection
- Missing getBotStatus responses

## **Deliverables**

### **1. Test Results Document** (`click_test_results.md`)
```markdown
## Left Click Tests
### UI Button Clicks
- [✅/❌] Single click generates 1 leftClick action
- [✅/❌] Hold duration calculated correctly
- [✅/❌] No duplicate actions
- [Console log snippet]

### Direct Mouse Clicks  
- [✅/❌] Direct left click triggers MCP action
- [✅/❌] Duration calculation works
- [Console log snippet]

## Right Click Tests
### UI Button Clicks
- [✅/❌] Right click button works
- [✅/❌] Duration calculated correctly
- [Console log snippet]

### Direct Mouse Clicks
- [✅/❌] Direct right click works
- [✅/❌] No errors or duplicates
- [Console log snippet]

## Duplication Bug Verification
- [✅/❌] No duplicate actions (verify fix works)
- [Evidence: session file snippets showing single actions]
```

### **2. Sample Session Files**
- `session_left_clicks.json`
- `session_right_clicks.json`
- `session_mixed_clicks.json`

### **3. Duration Accuracy Test**
Time actual click holds and verify MCP duration matches:
```markdown
| Actual Hold Time | Expected Duration | Actual MCP Duration | ✅/❌ |
|------------------|-------------------|---------------------|-------|
| 0.1s             | "short"           | [result]            |       |
| 1.0s             | "medium"          | [result]            |       |
| 2.5s             | "long"            | [result]            |       |
```

## **Key Files to Examine**

- `mc_pygame_controller/action_handler.py` (lines ~180-220) - Click handling
- `mc_pygame_controller/mode_strategy.py` (lines ~150-180) - `handle_timed_action()`
- `mc_pygame_controller/action_converter.py` (lines ~90-110) - Click conversion
- `mc_pygame_controller/ui_manager.py` - UI button processing

## **Special Focus: Duplication Bug**

This was a major issue that was recently fixed. Pay special attention to:

### **Code to Review:**
```python
# In action_converter.py - verify this fix is working:
elif action_type == "documentMouseEvent" and action.get("button") == 0:
    # Only convert mouse down events, skip mouse up events to avoid duplicates
    if action.get("action") == "down":
        return ActionConverter._convert_left_click_action(action)
    return None
```

### **Test Specifically:**
1. Hold left mouse button for 2 seconds
2. Check console output - should see exactly 1 "leftClick" queued
3. Check session file - should see exactly 1 leftClick conversation
4. If you see 2 leftClick actions, the fix didn't work

## **Quick Start Commands**

```bash
# Navigate to project
cd /Users/ohadr/minecraft-web-client

# Start with verbose output to see MCP traces
python -m mc_pygame_controller.controller --data-collection

# Monitor console for click traces:
# Should see: "📋 Queued MCP action: leftClick (sequence: ...)"
# Should NOT see duplicate actions
```

**DEADLINE**: [SET_DEADLINE]  
**Contact**: [LEAD_DEV] for questions 