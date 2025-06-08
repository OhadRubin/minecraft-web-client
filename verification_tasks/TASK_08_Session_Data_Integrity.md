# TASK 08: Session Data Integrity Verification

**Assigned Developer**: [DEV_NAME]  
**Estimated Time**: 3-4 hours  
**Priority**: HIGH (Data quality critical)

## **Objective**
Verify that session JSON files contain complete, valid data structures with proper conversation chains and no serialization errors.

## **Scope**
Validate session file structure, content, and format:
- JSON structure validation
- Conversation chain completeness
- Tool call format correctness
- Response data integrity
- File handling robustness

## **What You Need to Test**

### **1. Session File Structure Validation**
```bash
# Test Protocol:
1. Start: python -m mc_pygame_controller.controller --data-collection
2. Press F5, enter task: "Testing session structure"
3. Perform varied actions:
   - Movement (WASD)
   - Camera (mouse drag)
   - Clicks (left/right)
   - Jump (spacebar)
   - Hotbar selection (1-9)
4. Press F6 to save session
5. Examine resulting JSON file structure
```

### **2. Conversation Chain Validation**
```bash
# Test Protocol:
1. Start new session: "Testing conversation chains"
2. Create multi-action sequences:
   - Move → Click → Jump (3 actions)
   - Look → Move → Look → Click (4 actions)
   - Hotbar → Click → Move → Jump → Look (5 actions)
3. Save session
4. Verify each action generates proper conversation
```

### **3. Edge Case Data Handling**
```bash
# Test Protocol:
1. Start new session: "Testing edge cases"
2. Test problematic scenarios:
   - Very long task descriptions (>1000 characters)
   - Special characters in task names
   - Rapid action sequences (stress test)
   - Empty action sequences
   - Single action sequences
3. Save session
4. Verify all data handled correctly
```

## **Expected JSON Structure**

### **Session File Format**
```json
{
  "session_id": "session_[timestamp]",
  "start_time": [timestamp],
  "end_time": [timestamp], 
  "conversations": [
    {
      "conversation_id": "conv_seq_[id]_[timestamp]",
      "task_description": "[user_task]",
      "start_time": [timestamp],
      "end_time": [timestamp],
      "duration": [seconds],
      "messages": [
        {
          "role": "user",
          "content": "[task_description]"
        },
        {
          "role": "assistant", 
          "content": "I'll help you [task]. Let me perform these actions:",
          "tool_calls": [
            {
              "id": "call_[id]",
              "type": "function",
              "function": {
                "name": "[tool_name]",
                "arguments": "{\"param\": \"value\"}"
              }
            }
          ]
        },
        {
          "role": "tool",
          "content": "[tool_response]",
          "tool_call_id": "call_[id]"
        }
      ]
    }
  ]
}
```

### **Tool Call Format Validation**
Each tool call should have:
```json
{
  "id": "call_[unique_id]",
  "type": "function",
  "function": {
    "name": "[walk|lookAngle|leftClick|rightClick|jump|getBotStatus|etc]",
    "arguments": "[valid_json_string]"
  }
}
```

### **Tool Response Format**
Each tool response should have:
```json
{
  "role": "tool",
  "content": "[response_data]", 
  "tool_call_id": "[matching_call_id]"
}
```

## **Validation Checks**

### **1. JSON Validity**
- Valid JSON syntax (no parse errors)
- Proper escaping of special characters  
- Consistent field types
- No missing required fields

### **2. Structure Completeness**
- All conversations have start/end times
- All tool calls have matching responses
- All IDs are unique within session
- All required fields present

### **3. Data Consistency**
- Timestamps in chronological order
- Duration calculations correct
- Tool call IDs match response IDs
- No orphaned tool calls or responses

### **4. Content Validation**
- Task descriptions preserved correctly
- Tool parameters match expected format
- Response data contains expected fields
- No data corruption or truncation

## **Verification Points**

### **✅ Success Criteria:**
1. **Valid JSON**: All session files parse without errors
2. **Complete Structure**: All required fields present
3. **Proper Tool Calls**: All actions converted to valid tool calls
4. **Matching Responses**: Every tool call has corresponding response
5. **Chronological Order**: Timestamps and sequences make sense
6. **Data Preservation**: No loss of user input or system output

### **❌ Failure Modes to Check:**
- JSON parse errors
- Missing or null required fields
- Orphaned tool calls (no response)
- Orphaned responses (no call)
- Timestamp inconsistencies
- Corrupted or truncated data
- Special character encoding issues

## **Deliverables**

### **1. Data Integrity Report** (`session_integrity_report.md`)
```markdown
## JSON Structure Validation
- [✅/❌] All session files parse as valid JSON
- [✅/❌] Required fields present in all sessions
- [✅/❌] Field types consistent and correct
- [Evidence: validation script output]

## Conversation Chain Validation
- [✅/❌] All conversations have complete message sequences
- [✅/❌] User → Assistant → Tool → Assistant pattern correct
- [✅/❌] Tool call IDs match response IDs
- [Evidence: chain analysis report]

## Data Completeness Validation  
- [✅/❌] All user actions captured in conversations
- [✅/❌] All tool calls have corresponding responses
- [✅/❌] No data loss or corruption detected
- [Evidence: completeness check results]

## Edge Case Handling
- [✅/❌] Special characters handled correctly
- [✅/❌] Long inputs handled without truncation
- [✅/❌] Empty/minimal sessions handled correctly
- [Evidence: edge case test results]
```

### **2. Sample Validated Session Files**
- `session_valid_simple.json` - Simple action sequence
- `session_valid_complex.json` - Complex multi-action sequence
- `session_valid_edge_cases.json` - Edge cases and special characters

### **3. Validation Script**
Create `validate_session_files.py`:
```python
import json
import glob
from pathlib import Path

def validate_session_file(filepath):
    """Validate single session file structure and content"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Check required top-level fields
        required_fields = ['session_id', 'start_time', 'conversations']
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"
        
        # Validate conversations
        for conv in data['conversations']:
            # Check conversation structure
            # Validate tool calls and responses
            # Check timestamp consistency
            pass
            
        return "Valid"
    except Exception as e:
        return f"Error: {e}"

# Run validation on all session files
session_files = glob.glob("collected_trajectories/session_*.json")
for file in session_files:
    result = validate_session_file(file)
    print(f"{file}: {result}")
```

## **Key Files to Examine**

- `mc_pygame_controller/data_collection_controller.py` - Session file creation
- `mc_pygame_controller/chain.py` - Conversation chain building
- `mc_pygame_controller/conversation.py` - Message formatting
- `mc_pygame_controller/mode_strategy.py` - Data collection pipeline

## **Test Tools & Scripts**

### **JSON Validation Script**
```bash
# Create json_validator.py
import json
import sys

def validate_json_file(filepath):
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        print(f"✅ {filepath}: Valid JSON")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ {filepath}: JSON Error - {e}")
        return False

# Validate all session files
for file in sys.argv[1:]:
    validate_json_file(file)
```

### **Structure Validation Script** 
```bash
# Create structure_validator.py
import json

def check_tool_call_format(tool_call):
    required = ['id', 'type', 'function']
    function_required = ['name', 'arguments']
    
    for field in required:
        if field not in tool_call:
            return f"Missing tool_call field: {field}"
    
    for field in function_required:
        if field not in tool_call['function']:
            return f"Missing function field: {field}"
    
    # Validate arguments is valid JSON string
    try:
        json.loads(tool_call['function']['arguments'])
    except:
        return "Invalid arguments JSON string"
    
    return "Valid"
```

## **Debug Commands**

```bash
# Navigate to project directory
cd /Users/ohadr/minecraft-web-client

# Validate existing session files
python verification_tasks/json_validator.py collected_trajectories/session_*.json

# Run structure validation
python verification_tasks/structure_validator.py

# Check for common issues
grep -r "Object of type" collected_trajectories/
find collected_trajectories/ -name "*.json" -size 0  # Find empty files
```

## **Questions to Answer**

1. Are all JSON files valid and parseable?
2. Do conversation chains follow the expected message pattern?
3. Are tool call/response pairs properly matched?
4. Is there any data loss during serialization?
5. How are edge cases (special chars, long inputs) handled?
6. Are timestamps and durations calculated correctly?

**DEADLINE**: [SET_DEADLINE]  
**Contact**: [LEAD_DEV] for questions 