# TASK 07: Action Conversion Accuracy Verification

**Assigned Developer**: [DEV_NAME]  
**Estimated Time**: 4-5 hours  
**Priority**: HIGH (Data quality critical)

## **Objective**
Verify that pygame actions convert to MCP format with mathematically correct parameters, consistent calculations, and no data loss.

## **Scope**
Deep validation of conversion logic in `action_converter.py`:
- Movement magnitude → duration calculations
- Camera pixels → angle degrees calculations  
- Click timing → duration string mappings
- Parameter consistency across similar actions

## **What You Need to Test**

### **1. Movement Duration Calculations**
```bash
# Test Protocol:
1. Start: python -m mc_pygame_controller.controller --data-collection
2. Press F5, enter task: "Testing movement calculations"
3. Test specific movement magnitudes:
   - Small movement: W tap (0.1 second)
   - Medium movement: W hold (1 second)
   - Large movement: W hold (3 seconds)
   - Diagonal movement: W+A hold (2 seconds)
4. Record actual durations vs MCP durations
5. Press F6 to save session
```

### **2. Camera Angle Calculations**
```bash
# Test Protocol:
1. Start new session: "Testing camera calculations"
2. Test specific camera movements:
   - Small drag: 10 pixels horizontal
   - Medium drag: 50 pixels horizontal
   - Large drag: 200 pixels horizontal
   - Vertical drag: 30 pixels up/down
   - Diagonal drag: 45-degree angle
3. Record pixel movements vs MCP angles
4. Save session
```

### **3. Click Duration Mappings**
```bash
# Test Protocol:
1. Start new session: "Testing click duration mappings"
2. Test specific click durations:
   - Quick tap: <150ms
   - Short hold: 500ms
   - Medium hold: 1500ms
   - Long hold: 3000ms
   - Very long hold: 8000ms
3. Record actual times vs MCP duration strings
4. Save session
```

## **Mathematical Validation**

### **Movement Duration Formula**
```python
# From action_converter.py - verify this calculation:
magnitude = (x**2 + z**2) ** 0.5
duration = int(magnitude * ActionConverter.MAGNITUDE_DURATION_SCALE)
# Where MAGNITUDE_DURATION_SCALE = 2000
```

**Test Cases:**
```markdown
| Input (x, z) | Magnitude | Expected Duration | Actual Duration | ✅/❌ |
|--------------|-----------|-------------------|-----------------|-------|
| (0.5, 0.0)   | 0.5       | 1000ms           | [result]        |       |
| (1.0, 0.0)   | 1.0       | 2000ms           | [result]        |       |
| (0.5, 0.5)   | 0.707     | 1414ms           | [result]        |       |
| (0.1, 0.0)   | 0.1       | 200ms            | [result]        |       |
```

### **Camera Angle Formula**
```python
# From action_converter.py - verify this calculation:
x_angle = movement_x / ActionConverter.SENSITIVITY
y_angle = -(movement_y / ActionConverter.SENSITIVITY)  # Inverted Y
# Where SENSITIVITY = 5.0
```

**Test Cases:**
```markdown
| Pixel Movement (x, y) | Expected Angle (x, y) | Actual Angle | ✅/❌ |
|-----------------------|------------------------|--------------|-------|
| (50, 0)               | (10.0, 0.0)           | [result]     |       |
| (0, 25)               | (0.0, -5.0)           | [result]     |       |
| (100, -50)            | (20.0, 10.0)          | [result]     |       |
| (5, 5)                | (1.0, -1.0)           | [result]     |       |
```

### **Click Duration Mapping**
```python
# From action_handler.py - verify this mapping:
if duration_ms < 150: return "very_short"      # 100ms
elif duration_ms < 750: return "short"         # 500ms  
elif duration_ms < 1500: return "medium"       # 1000ms
elif duration_ms < 3500: return "long"         # 2000ms
elif duration_ms < 7500: return "very_long"    # 5000ms
else: return "very_very_long"                  # 10000ms
```

**Test Cases:**
```markdown
| Actual Hold (ms) | Expected Duration | Actual Duration | ✅/❌ |
|------------------|-------------------|-----------------|-------|
| 100              | "very_short"      | [result]        |       |
| 600              | "short"           | [result]        |       |
| 1200             | "medium"          | [result]        |       |
| 2500             | "long"            | [result]        |       |
| 6000             | "very_long"       | [result]        |       |
| 9000             | "very_very_long"  | [result]        |       |
```

## **Consistency Verification**

### **Cross-Input Consistency**
- WASD movement vs joystick movement: same magnitude = same duration
- UI button clicks vs direct mouse clicks: same timing = same duration
- Keyboard shortcuts vs UI buttons: same action = same parameters

### **Boundary Testing**
- Test threshold values (exactly 150ms, exactly 750ms, etc.)
- Test edge cases (zero movement, maximum movement)
- Test negative values and invalid inputs

## **Verification Points**

### **✅ Success Criteria:**
1. **Mathematical Accuracy**: All formulas produce expected results
2. **Consistent Scaling**: Similar inputs produce similar outputs
3. **Threshold Correctness**: Boundary values map to correct categories
4. **No Data Loss**: All meaningful input differences preserved
5. **Cross-Input Consistency**: Same logical action = same MCP parameters
6. **Range Validation**: All outputs within expected ranges

### **❌ Failure Modes to Check:**
- Mathematical errors in conversion formulas
- Inconsistent scaling between input methods
- Wrong threshold boundaries
- Floating point precision issues
- Off-by-one errors in mappings
- Missing edge case handling

## **Deliverables**

### **1. Validation Report** (`conversion_accuracy_report.md`)
```markdown
## Mathematical Formula Validation
- [✅/❌] Movement magnitude calculation correct
- [✅/❌] Camera angle calculation correct  
- [✅/❌] Click duration mapping correct
- [Evidence: calculation verification tables]

## Consistency Testing
- [✅/❌] WASD vs joystick consistency
- [✅/❌] Button vs direct input consistency
- [✅/❌] Cross-platform parameter consistency
- [Evidence: comparison tables]

## Boundary Testing
- [✅/❌] Duration thresholds correct (150ms, 750ms, etc.)
- [✅/❌] Movement thresholds correct (0.1, 0.2, etc.)
- [✅/❌] Angle thresholds correct
- [Evidence: boundary test results]

## Edge Case Testing
- [✅/❌] Zero/minimal inputs handled correctly
- [✅/❌] Maximum inputs handled correctly
- [✅/❌] Invalid inputs handled gracefully
- [Evidence: edge case test log]
```

### **2. Calculation Verification Spreadsheet**
Create CSV files with test data:
- `movement_calculations.csv`
- `camera_calculations.csv`
- `duration_mappings.csv`

### **3. Consistency Analysis**
Document any inconsistencies found:
```markdown
| Issue | Input Method A | Input Method B | Expected | Actual A | Actual B | Impact |
|-------|----------------|----------------|----------|----------|----------|---------|
| [example] | [method] | [method] | [value] | [value] | [value] | [level] |
```

## **Key Files to Examine**

- `mc_pygame_controller/action_converter.py` - Core conversion logic
- `mc_pygame_controller/action_handler.py` - Duration calculation  
- `mc_pygame_controller/look_path.py` - Camera angle processing
- `mc_pygame_controller/constants.py` - Threshold values

## **Testing Tools**

Create helper scripts for validation:

### **Movement Test Script**
```python
# Create manual_movement_test.py
from mc_pygame_controller.action_converter import ActionConverter

test_movements = [
    {"type": "move", "x": 0.5, "z": 0.0},
    {"type": "move", "x": 1.0, "z": 0.0},  
    {"type": "move", "x": 0.5, "z": 0.5},
    # Add more test cases...
]

for movement in test_movements:
    result = ActionConverter.convert_pygame_action(movement)
    print(f"Input: {movement} → Output: {result}")
```

### **Camera Test Script**
```python
# Create manual_camera_test.py  
test_looks = [
    {"type": "look", "movementX": 50, "movementY": 0},
    {"type": "look", "movementX": 0, "movementY": 25},
    # Add more test cases...
]

for look in test_looks:
    result = ActionConverter.convert_pygame_action(look)
    print(f"Input: {look} → Output: {result}")
```

## **Debug Commands**

```bash
# Test conversion accuracy manually
cd /Users/ohadr/minecraft-web-client
python verification_tasks/manual_movement_test.py
python verification_tasks/manual_camera_test.py

# Run data collection with detailed logging
python -m mc_pygame_controller.controller --data-collection --verbose
```

## **Questions to Answer**

1. Are conversion formulas mathematically sound?
2. Do threshold boundaries make sense for gameplay?
3. Are there any precision loss issues with floating point?
4. Do all input methods produce consistent results?
5. Are edge cases handled appropriately?

**DEADLINE**: [SET_DEADLINE]  
**Contact**: [LEAD_DEV] for questions 