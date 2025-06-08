# TASK 09: Sequence Tracking & getBotStatus Verification

**Assigned Developer**: [DEV_NAME]  
**Estimated Time**: 3-4 hours  
**Priority**: HIGH (Core data collection timing)

## **Objective**
Verify that action sequence tracking works correctly, getBotStatus is called at appropriate times, and sequence completion detection is accurate.

## **Scope**
Test the sequence tracking system that was recently fixed:
- Action sequence creation and tracking
- getBotStatus timing and execution
- Sequence completion detection
- MCP response counting and matching
- Timing and synchronization

## **What You Need to Test**

### **1. Single Action Sequences**
```bash
# Test Protocol:
1. Start: python -m mc_pygame_controller.controller --data-collection
2. Press F5, enter task: "Testing single actions"
3. Perform individual actions with pauses between:
   - Single W press (wait 3 seconds)
   - Single left click (wait 3 seconds)  
   - Single jump (wait 3 seconds)
   - Single hotbar selection (wait 3 seconds)
4. Press F6 to save session
5. Verify each action creates complete sequence
```

### **2. Multi-Action Sequences**
```bash
# Test Protocol:
1. Start new session: "Testing multi-action sequences"
2. Perform rapid action combinations:
   - W + left click + release both
   - Camera drag + jump + hotbar selection
   - Movement + multiple clicks + jump
3. Save session
4. Verify sequences track all actions correctly
```

### **3. getBotStatus Timing**
```bash
# Test Protocol:
1. Start new session: "Testing getBotStatus timing"
2. Monitor console output for getBotStatus calls:
   - After single actions
   - After multi-action sequences
   - During rapid action sequences
   - At sequence completion
3. Save session
4. Verify getBotStatus called at correct times
```

### **4. Sequence Completion Detection**
```bash
# Test Protocol:
1. Start new session: "Testing sequence completion"
2. Test various completion scenarios:
   - Simple: 1 action + getBotStatus (expect 2 responses)
   - Complex: 3 actions + getBotStatus (expect 4 responses)
   - Rapid: Fast actions with overlapping timing
3. Save session
4. Verify sequences complete when all responses received
```

## **Sequence Tracking Architecture**

### **How It Works (Recently Fixed)**
1. **Sequence Start**: `start_sequence()` creates tracking entry
2. **Expected Responses**: Calculates number of MCP actions + 1 (getBotStatus)
3. **Response Collection**: `add_response()` collects MCP tool responses
4. **Completion Detection**: `is_sequence_complete()` checks response count
5. **Data Collection**: Complete sequences converted to conversations

### **Key Fixed Issues**
- **Duplicate Actions**: Mouse down/up now generates single action
- **Response Counting**: Counts MCP actions correctly (not pygame actions)
- **JSON Serialization**: Handles function objects gracefully
- **Timing**: Proper sequence completion detection

## **Expected Console Output Patterns**

### **Successful Sequence:**
```
🔄 Converted 1 pygame actions to 1 MCP actions
🎬 Started tracking sequence seq_1_1749395736_772637 with 1 actions
🎯 Expecting 2 total responses for sequence seq_1_1749395736_772637
📋 Queued MCP action: walk (sequence: seq_1_1749395736_772637)
📋 Queued MCP action: getBotStatus (sequence: seq_1_1749395736_772637)  
🔄 Executing MCP tool: walk
✅ Tool walk executed successfully
🔄 Executing MCP tool: getBotStatus
✅ Tool getBotStatus executed successfully
🎯 Sequence seq_1_1749395736_772637 complete: 2/2 responses
💾 Built conversation chain: 3 messages
💾 Saved conversation: conv_seq_1_1749395736_772637
```

### **Failure Patterns to Watch For:**
```
❌ JSON serialization error
❌ Sequence never completing (waiting forever)
❌ Missing getBotStatus calls
❌ Wrong response count expectations
❌ Duplicate actions creating double responses
```

## **Verification Points**

### **✅ Success Criteria:**
1. **Sequence Creation**: Every action group creates a tracked sequence
2. **Response Counting**: Expected response count = MCP actions + 1 (getBotStatus)
3. **getBotStatus Automatic**: getBotStatus added to every sequence automatically
4. **Completion Detection**: Sequences complete when all responses received
5. **No Orphans**: No sequences left incomplete or hanging
6. **Console Clarity**: Clear logging shows sequence progress

### **❌ Failure Modes to Check:**
- Sequences created but never completed
- Wrong expected response counts
- Missing getBotStatus calls
- Duplicate action counting
- JSON serialization failures
- Sequence ID collisions
- Timing/synchronization issues

## **Deliverables**

### **1. Sequence Tracking Report** (`sequence_tracking_report.md`)
```markdown
## Single Action Tests
- [✅/❌] Single actions create sequences correctly
- [✅/❌] getBotStatus automatically added to all sequences
- [✅/❌] Expected response count = actions + 1
- [✅/❌] Sequences complete successfully
- [Console log evidence]

## Multi-Action Tests
- [✅/❌] Multi-action sequences track all actions
- [✅/❌] Response counting works for complex sequences
- [✅/❌] No actions lost in rapid sequences
- [Console log evidence]

## getBotStatus Timing Tests
- [✅/❌] getBotStatus called after every sequence
- [✅/❌] getBotStatus responses received successfully
- [✅/❌] No missing getBotStatus calls
- [Evidence: getBotStatus timing log]

## Completion Detection Tests
- [✅/❌] Sequences complete when all responses received
- [✅/❌] No sequences left hanging incomplete
- [✅/❌] Completion timing is reasonable
- [Evidence: completion timing analysis]
```

### **2. Sequence Timing Analysis**
Create spreadsheet tracking sequence lifecycles:
```markdown
| Sequence ID | Actions | Expected | Received | Complete | Duration | ✅/❌ |
|-------------|---------|----------|----------|----------|----------|-------|
| seq_1_...   | 1       | 2        | 2        | Yes      | 1.2s     | ✅    |
| seq_2_...   | 3       | 4        | 4        | Yes      | 2.1s     | ✅    |
| seq_3_...   | 2       | 3        | 2        | No       | >5s      | ❌    |
```

### **3. getBotStatus Coverage Report**
Track getBotStatus execution:
```markdown
| User Action | MCP Actions | getBotStatus Called | Response Received | ✅/❌ |
|-------------|-------------|-------------------|------------------|-------|
| W press     | 1 walk      | Yes               | Yes              | ✅    |
| Left click  | 1 leftClick | Yes               | Yes              | ✅    |
| W+Click     | 2 actions   | Yes               | Yes              | ✅    |
```

## **Key Files to Examine**

- `mc_pygame_controller/action_sequence_tracker.py` - Core sequence tracking logic
- `mc_pygame_controller/mode_strategy.py` - Sequence creation and completion
- `mc_pygame_controller/action_converter.py` - Action counting (check for duplicates)
- `mc_pygame_controller/mcp_client.py` - MCP response handling

## **Debug Monitoring**

### **Console Grep Commands**
```bash
# Monitor sequence creation
grep "Started tracking sequence" [console_output]

# Monitor completion  
grep "Sequence.*complete:" [console_output]

# Monitor getBotStatus
grep "getBotStatus" [console_output]

# Look for errors
grep "❌\|Error\|Failed" [console_output]
```

### **Real-time Monitoring Script**
```python
# Create sequence_monitor.py
import re
import time

def monitor_console_output():
    """Monitor console for sequence tracking patterns"""
    sequences = {}
    
    # Track sequence creation
    # Track completion
    # Report hanging sequences
    pass

if __name__ == "__main__":
    monitor_console_output()
```

## **Stress Testing**

### **Rapid Action Test**
```bash
# Test Protocol:
1. Start session: "Stress testing rapid actions"  
2. Perform very rapid actions (1 per second):
   - W, click, jump, 2, click, W, look, click (rapid sequence)
3. Monitor console for sequence handling
4. Save session
5. Verify all actions captured correctly
```

### **Timing Edge Cases**
```bash
# Test Protocol:
1. Test edge timing cases:
   - Action while previous sequence still completing
   - Multiple rapid identical actions
   - Actions with very fast/slow responses
2. Monitor sequence overlap and completion
```

## **Questions to Answer**

1. Do all user actions result in completed sequences?
2. Is getBotStatus called consistently for every sequence?
3. Are expected response counts calculated correctly?
4. Do sequences complete in reasonable time?
5. Are there any hanging or orphaned sequences?
6. Does rapid action input cause sequence tracking issues?

**DEADLINE**: [SET_DEADLINE]  
**Contact**: [LEAD_DEV] for questions 