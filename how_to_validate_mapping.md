# How to Validate Pygame ↔ MCP Action Mapping

## Prerequisites - Required Reading

To understand this validation process, you **must** read these files first:

### Core Architecture Files:
1. **`mc_pygame_controller/README.md`** - Complete system architecture and data flow
2. **`mc_pygame_controller/action_handler.py`** - Action processing and dispatch logic
3. **`mc_pygame_controller/action_converter.py`** - Pygame→MCP conversion algorithms
4. **`mc_pygame_controller/mode_strategy.py`** - Mode-specific execution strategies

### Key Sections to Focus On:
- **README.md Lines 122-137**: Message flow architecture  
- **README.md Lines 194-235**: Data consistency requirements
- **action_handler.py Lines 25-49**: Action dispatch dictionary
- **action_converter.py Lines 22-27**: Conversion constants and thresholds

## Validation Objective

**Verify that the WebSocket commands (ground truth) and MCP tool calls (training data) represent the same spatial actions consistently.**

## Critical Validation Questions

For each action type, validate:
1. **Does the pygame WebSocket command accurately represent what the human did?**
2. **Does the MCP tool call accurately represent the same spatial action?**
3. **Do both produce the same result when getBotStatus is called?**
4. **Are the coordinate systems and mathematical conversions consistent?**

## Complete Action Mapping Table

| Action Type | Human Input | Pygame WebSocket Command | MCP Tool Call | Handler Location | Converter Location | Execution Path | Logging Location | Data Collection | Async/Sync | Consistency Risk |
|-------------|-------------|-------------------------|---------------|------------------|-------------------|----------------|------------------|-----------------|------------|------------------|
| **Movement** | WASD/Joystick | `{"type": "move", "x": 0.5, "z": 0.3}` | `{"tool": "walk", "parameters": {"duration": 1000}}` | `action_handler.py:161-173` | `action_converter.py:59-72` | `strategy.handle_movement()` | None in controller | Action + screenshot | Sync | 🔴 **HIGH** - Direction lost |
| **Camera Look** | Mouse drag | `{"type": "look", "movementX": 10, "movementY": -5}` | `{"tool": "lookAngle", "parameters": {"xAngle": 2.0, "yAngle": 1.0}}` | `action_handler.py:175-188` | `action_converter.py:75-96` | `look_path_tracker` + `controller_base.py:371,382` | `controller_base.py:297-308` | LookPath tracking | Mixed | 🔴 **HIGH** - Relative vs absolute |
| **Left Click** | Mouse/Button | `{"type": "leftDown"}` + `{"type": "leftUp"}` | `{"tool": "leftClick", "parameters": {"duration": "short"}}` | `action_handler.py:190-205` | `action_converter.py:99-101` | `strategy.handle_timed_action()` | `action_handler.py:118,124` | Duration calculation | Sync | 🟡 **MEDIUM** - Duration calc |
| **Right Click** | Mouse/Button | `{"type": "rightDown"}` + `{"type": "rightUp"}` | `{"tool": "rightClick", "parameters": {"duration": "short"}}` | `action_handler.py:207-222` | `action_converter.py:104-106` | `strategy.handle_timed_action()` | `action_handler.py:118,124` | Duration calculation | Sync | 🟡 **MEDIUM** - Duration calc |
| **Jump** | Space/Button | `{"type": "control", "control": "jump", "state": true/false}` | `{"tool": "jump", "parameters": {"duration": "short"}}` | `action_handler.py:224-232` | `action_converter.py:274-278` | `strategy.handle_timed_action()` | `action_handler.py:118,124` | Duration calculation | Sync | 🟡 **MEDIUM** - State vs duration |
| **Sneak** | Shift toggle | `{"type": "control", "control": "sneak", "state": true/false}` | `{"tool": "sneak", "parameters": {"state": true}}` | `action_handler.py:234-236` | `action_converter.py:279-283` | `strategy.handle_toggle_action()` | None | State tracking | Sync | 🟢 **LOW** - Direct mapping |
| **Sprint** | Ctrl toggle | `{"type": "control", "control": "sprint", "state": true/false}` | `{"tool": "sprint", "parameters": {"state": true}}` | `action_handler.py:238-240` | `action_converter.py:284-288` | `strategy.handle_toggle_action()` | None | State tracking | Sync | 🟢 **LOW** - Direct mapping |
| **Inventory** | E key | `{"type": "inventory"}` | `{"tool": "toggleInventory", "parameters": {}}` | `action_handler.py:242-259` | `action_converter.py:289-293` | `strategy.handle_simple_action()` | `action_handler.py:251-252` | Simple toggle | Sync | 🟢 **LOW** - Simple toggle |
| **Hotbar Slot** | 1-9 keys | `{"type": "setHotbarSlot", "slot": 3}` | `{"tool": "setHotbarSlot", "parameters": {"slot": 3}}` | `action_handler.py:261-272` | `action_converter.py:269-273` | `strategy.handle_simple_action()` | `action_handler.py:265` | Slot number | Sync | 🟢 **LOW** - Direct mapping |
| **Drop Item** | Q key | `{"type": "dropItem", "amount": 1}` | `{"tool": "dropItem", "parameters": {"amount": 1}}` | `action_handler.py:274-282` | `action_converter.py:294-298` | `strategy.handle_simple_action()` | `action_handler.py:277` | Amount value | Sync | 🟢 **LOW** - Direct mapping |
| **Swap Hands** | F key | `{"type": "swapHands"}` | `{"tool": "swapHands", "parameters": {}}` | `action_handler.py:284-291` | `action_converter.py:299-303` | `strategy.handle_simple_action()` | `action_handler.py:287` | Simple action | Sync | 🟢 **LOW** - Direct mapping |

## Critical Controller Logging Points (controller_base.py)

### Camera Drag State Tracking (Lines 297-308):
```python
print(f"🔍 Camera state change: clicking={camera_is_clicking}, was_clicking={prev_clicking}")
print("🖱️ Mouse pressed in camera area - starting drag tracking")
print("🖱️ Mouse released - ending drag tracking")
```

### MCP Command Execution Logging (Lines 371, 376, 382-383):
```python
print(f"🎮 Executing: {mcp_command['tool']}({mcp_command['parameters']})")
print(f"🎮 MCP Command (no executor): {mcp_command['tool']}({mcp_command['parameters']})")  
print(f"🎭 Camera drag action: {mcp_command['tool']}({mcp_command['parameters']})")
```

### getBotStatus Result Capture (Line 550):
```python
print(f"📊 Pygame startup getBotStatus result: \n====\n{text}\n====\n")
```

### Data Collection Status (Lines 102-104):
```python
print("🎬 Data collection enabled!")
print("📋 Hotkeys: F5=Start session | F6=Save session | F7=Cancel session")
print("💡 This will capture spatial reasoning data for AI training")
```

**⚠️ Key Insight**: Camera movements have **special execution paths** that bypass normal action processing:
- `look_path_tracker.add_movement()` in `action_handler.py:182`
- `_execute_pygame_mcp_action()` in `controller_base.py:379-392`
- Different logging for camera vs other actions

## Validation Test Plan

### Phase 1: High-Risk Actions (🔴 Critical Issues)

#### Test 1: Movement Direction Consistency
**Test Scenario**: Move forward (W key) for 2 seconds

**Expected pygame WebSocket**:
```json
{"type": "move", "x": 0.0, "z": -1.0}
```

**Expected MCP Logging**:
```json
{"tool": "walk", "parameters": {"duration": 2000}}
```

**🚨 CRITICAL ISSUE**: **Direction vector (x=0, z=-1) is completely lost in MCP logging!**

**Validation Steps**:
1. Start data collection mode
2. Hold W key for exactly 2 seconds
3. Check WebSocket logs for move commands with direction
4. Check MCP logs for walk commands with duration only
5. **Verify**: Can the MCP command reproduce the same movement?

#### Test 2: Camera Look Angle Consistency  
**Test Scenario**: Look right by dragging mouse 100 pixels

**Expected pygame WebSocket**:
```json
{"type": "look", "movementX": 100, "movementY": 0}
```

**Expected MCP Logging**:
```json
{"tool": "lookAngle", "parameters": {"xAngle": 20.0, "yAngle": 0.0, "speed": "normal"}}
```

**🚨 CRITICAL ISSUE**: **Relative mouse movement vs absolute angle target!**

**Validation Steps**:
1. Note current player yaw angle (`getBotStatus`)
2. Drag mouse right 100 pixels  
3. Check WebSocket logs for relative movement
4. Check MCP logs for absolute angle change
5. **Verify**: Do both produce the same final yaw angle?

### Phase 2: Medium-Risk Actions (🟡 Duration/Timing Issues)

#### Test 3: Click Duration Mapping
**Test Scenario**: Hold left click for 3 seconds

**Expected pygame WebSocket**:
```json
{"type": "leftDown"}
// ... 3 seconds later ...
{"type": "leftUp"}
```

**Expected MCP Logging**:
```json
{"tool": "leftClick", "parameters": {"duration": "long"}}
```

**Validation**: Check `action_handler.py:84-103` duration calculation logic.

### Phase 3: Low-Risk Actions (🟢 Simple Mappings)

Test hotbar, inventory, and toggle actions for basic consistency.

## Critical Code Locations for Investigation

### Conversion Constants (action_converter.py:22-27):
```python
MOVEMENT_THRESHOLD = 0.1
LOOK_THRESHOLD = 0.2  
SENSITIVITY = 5.0
MAGNITUDE_DURATION_SCALE = 2000
```

### Movement Conversion Logic (action_converter.py:59-72):
```python
magnitude = (x**2 + z**2) ** 0.5
duration = int(magnitude * ActionConverter.MAGNITUDE_DURATION_SCALE)
return {"tool": "walk", "parameters": {"duration": duration}}
```

**🚨 SPATIAL DATA LOSS**: Direction vector (x, z) is discarded!

### Look Conversion Logic (action_converter.py:75-96):
```python
x_angle = movement_x / ActionConverter.SENSITIVITY  
y_angle = -(movement_y / ActionConverter.SENSITIVITY)
```

**🚨 COORDINATE SYSTEM MISMATCH**: Relative mouse delta → absolute angle change.

## Critical Sensitivity & Pixel-to-Angle Conversion Issues

### The Sensitivity Chain Problem

**Multiple sensitivity transformations** are applied to mouse movements, creating potential inconsistencies:

#### 1. Initial Scaling (action_handler.py:177-179):
```python
# Scale the movement for better sensitivity  
scaled_x = delta_x * 2
scaled_y = delta_y * 2
```
**Result**: 10px mouse movement → 20px WebSocket command

#### 2. WebSocket Command:
```json
{"type": "look", "movementX": 20, "movementY": 0}
```
**Sent to Minecraft client**: Raw pixel values (20px)

#### 3. MCP Conversion (action_converter.py:81-82):
```python
x_angle = movement_x / ActionConverter.SENSITIVITY  # SENSITIVITY = 5.0
y_angle = -(movement_y / ActionConverter.SENSITIVITY)
```
**Result**: 20px ÷ 5.0 = 4.0° MCP angle

#### 4. MCP Command:
```json
{"tool": "lookAngle", "parameters": {"xAngle": 4.0, "yAngle": 0.0}}
```

### 🚨 The Fundamental Question

**Does the Minecraft client actually rotate 4.0° when it receives `{"movementX": 20}`?**

If **NO**, then the entire MCP conversion is using the **wrong sensitivity constant**, and all camera training data is corrupted.

### Sensitivity Sources in Codebase

| Location | Purpose | Value | Applied To |
|----------|---------|-------|------------|
| `action_handler.py:178` | WebSocket scaling | `× 2` | Mouse delta → WebSocket command |
| `action_converter.py:25` | MCP conversion | `÷ 5.0` | WebSocket pixels → MCP degrees |
| `controller_base.py:53` | LookPathTracker | User parameter (default 5.0) | Path tracking calculations |
| Controller initialization | Global setting | Command line arg | Overall system sensitivity |

### Potential Sensitivity Mismatch Scenarios

#### Scenario A: Correct Conversion
- Mouse: 10px → WebSocket: 20px → Minecraft: 4.0° → MCP logs: 4.0°
- **✅ Consistent**: MCP training data matches actual rotation

#### Scenario B: Wrong Sensitivity Constant  
- Mouse: 10px → WebSocket: 20px → Minecraft: 2.0° → MCP logs: 4.0°
- **❌ Broken**: MCP training data shows 2× larger rotations than actually happened

#### Scenario C: WebSocket Uses Different Units
- Mouse: 10px → WebSocket: 20px → Minecraft: (some internal conversion) → MCP logs: 4.0°
- **❌ Unknown**: Can't validate without understanding Minecraft's internal conversion

### Validation Test for Sensitivity Issues

#### Critical Test: Pixel-to-Degree Calibration

1. **Record initial camera angle** via `getBotStatus`:
   ```
   Position: (x, y, z) facing East (-288.15°, -2.55°)
   ```

2. **Perform controlled mouse movement**:
   - Move mouse exactly 50 pixels right
   - Capture WebSocket command: `{"movementX": 100}` (50 × 2 scaling)
   - Capture MCP conversion: `{"xAngle": 20.0}` (100 ÷ 5.0)

3. **Record final camera angle** via `getBotStatus`:
   ```
   Position: (x, y, z) facing East (-268.15°, -2.55°)
   ```

4. **Calculate actual rotation**:
   ```python
   actual_rotation = -268.15 - (-288.15) = 20.0°
   mcp_logged_rotation = 20.0°
   websocket_implied_rotation = 100 / 5.0 = 20.0°
   ```

5. **Validation**:
   - **✅ PASS**: `actual_rotation == mcp_logged_rotation`
   - **❌ FAIL**: Any mismatch indicates sensitivity constant is wrong

### Expected Sensitivity Issues

Based on code analysis, potential problems:

1. **Hardcoded Constants**: `SENSITIVITY = 5.0` may not match Minecraft's actual conversion
2. **Double Scaling**: Mouse delta scaled by 2× then divided by 5.0 (net 0.4× factor)
3. **Different WebSocket Interpretation**: Minecraft client may use different pixel-to-angle formula  
4. **Mode-Dependent Sensitivity**: Different sensitivity between pygame and MCP modes
5. **Platform Differences**: Mouse sensitivity may vary by OS/hardware

### Red Flags for Sensitivity Issues

Watch for these symptoms during validation:

- **Systematic rotation errors**: All MCP angles consistently 2× or 0.5× actual rotation
- **Variable sensitivity**: Same mouse movement produces different rotations  
- **Mode-dependent rotation**: Pygame vs MCP modes result in different final angles
- **Non-linear scaling**: Small movements work but large movements are wrong

**If sensitivity is wrong, ALL camera training data is corrupted and unusable for spatial reasoning.**

## LookPath Calculation Validation

### Confirming LookPath Tracker Accuracy

The `look_path_tracker` performs its own camera movement calculations that should match what `getBotStatus` reports. This validates that the tracker's mathematical analysis is correct.

### LookPath vs getBotStatus Consistency Test

#### Test Setup: Camera Drag Validation
```python
# 1. Record initial camera state
initial_status = await getBotStatus()
initial_yaw = parse_yaw(initial_status)    # e.g., -288.15°
initial_pitch = parse_pitch(initial_status) # e.g., -2.55°

# 2. Start look path tracking
look_path_tracker.start_mouse_tracking()

# 3. Perform controlled mouse drag
mouse_movements = [
    (10, 0),   # 10px right
    (10, 0),   # 10px right  
    (0, -5),   # 5px up
    (15, 0),   # 15px right
]

for dx, dy in mouse_movements:
    look_path_tracker.add_movement(dx, dy)

# 4. Stop tracking and get calculations
look_path_tracker.stop_mouse_tracking()
path_stats = look_path_tracker.get_current_path_stats()

# 5. Get what LookPath calculated
calculated_total_x = path_stats.total_degrees_x  # e.g., 7.0°
calculated_total_y = path_stats.total_degrees_y  # e.g., -1.0°

# 6. Record final camera state after movements executed
final_status = await getBotStatus()
final_yaw = parse_yaw(final_status)      # e.g., -281.15°
final_pitch = parse_pitch(final_status)  # e.g., -3.55°

# 7. Calculate actual camera change
actual_yaw_change = final_yaw - initial_yaw      # -281.15 - (-288.15) = 7.0°
actual_pitch_change = final_pitch - initial_pitch # -3.55 - (-2.55) = -1.0°

# 8. Validation
assert abs(calculated_total_x - actual_yaw_change) < 0.5, f"Yaw calculation wrong: {calculated_total_x}° vs {actual_yaw_change}°"
assert abs(calculated_total_y - actual_pitch_change) < 0.5, f"Pitch calculation wrong: {calculated_total_y}° vs {actual_pitch_change}°"
```

### What This Validates

1. **LookPath Math is Correct**: The tracker's pixel-to-degree calculations match reality
2. **Sensitivity Constant is Right**: The `SENSITIVITY = 5.0` value used by LookPath works
3. **WebSocket Execution Works**: Commands sent to Minecraft actually execute correctly
4. **No Cumulative Errors**: Multiple small movements don't drift over time

### Expected LookPath Calculations

Based on current code (`look_path_tracker` calculations):

| Mouse Movement | LookPath Calculation | Expected getBotStatus Change |
|---------------|---------------------|------------------------------|
| 50px right | `50 / 5.0 = 10.0°` yaw | Yaw increases by 10.0° |
| 25px left | `25 / 5.0 = -5.0°` yaw | Yaw decreases by 5.0° |
| 30px up | `30 / 5.0 = 6.0°` pitch | Pitch increases by 6.0° |
| 15px down | `15 / 5.0 = -3.0°` pitch | Pitch decreases by 3.0° |

### Red Flags for LookPath Issues

If this validation fails, it indicates:

1. **Wrong Sensitivity in LookPath**: The tracker uses different sensitivity than WebSocket commands
2. **Coordinate System Bug**: X/Y axis mapping is wrong between tracker and game
3. **Execution Timing Issues**: Commands sent but not executed before getBotStatus call
4. **Cumulative Drift**: Small rounding errors accumulate over multiple movements
5. **WebSocket Command Issues**: Commands formatted incorrectly or lost in transmission

### Integration with Action Conversion

**This test is critical because**:
- If LookPath calculations are wrong, MCP conversions are wrong
- If LookPath is right but MCP conversion differs, there's a conversion bug
- If both LookPath and MCP match getBotStatus, the training data is accurate

**Validation Flow**:
1. ✅ **LookPath ↔ getBotStatus**: Confirm tracker calculations match reality
2. ✅ **MCP Conversion ↔ LookPath**: Confirm conversion uses same math as tracker  
3. ✅ **MCP Conversion ↔ getBotStatus**: Confirm training data matches reality

**If all three match, camera training data is accurate for spatial reasoning.**

## Async Execution Timing Validation

### The Critical Timing Problem

**All validation depends on `getBotStatus` capturing state AFTER actions complete.** If getBotStatus returns "old" state due to async race conditions, all validation results are meaningless.

### Async Race Condition Test

#### Problem Scenario
```python
# BAD: Race condition - getBotStatus may return old state
send_websocket_command({"type": "move", "x": 1.0, "z": 0.0})  # Async
final_status = await getBotStatus()  # May execute before move completes!
```

#### Proper Timing Validation
```python
# 1. Record initial state
initial_status = await getBotStatus()
initial_pos = parse_position(initial_status)  # (30, 63, -18)

# 2. Send action command
await send_websocket_command({"type": "move", "x": 1.0, "z": 0.0})

# 3. CRITICAL: Wait for action completion
await asyncio.sleep(0.2)  # Allow time for WebSocket + game processing

# 4. Verify state has changed
intermediate_status = await getBotStatus()
intermediate_pos = parse_position(intermediate_status)

# 5. Validate action completed
position_changed = intermediate_pos != initial_pos
assert position_changed, f"Action didn't complete: {initial_pos} == {intermediate_pos}"

# 6. Wait additional time to ensure state is stable
await asyncio.sleep(0.1)
final_status = await getBotStatus()
final_pos = parse_position(final_status)

# 7. Validate state is stable (no further changes)
assert final_pos == intermediate_pos, f"State still changing: {intermediate_pos} -> {final_pos}"
```

### Timing Validation Requirements

#### Action Completion Detection
**Required for each action type:**

| Action Type | Completion Signal | Minimum Wait Time | Validation Method |
|-------------|------------------|-------------------|-------------------|
| **Movement** | Position change | 200ms | Compare coordinates |
| **Camera Look** | Rotation change | 100ms | Compare yaw/pitch |
| **Left/Right Click** | Block state change | 150ms | Check block interaction |
| **Jump** | Y-coordinate change | 300ms | Detect vertical movement |
| **Inventory** | Context change | 100ms | Check UI state |

#### State Settling Validation
```python
async def wait_for_state_stable(action_type: str, max_wait: float = 1.0):
    """Wait until getBotStatus returns consistent results."""
    stable_count = 0
    last_status = None
    
    for _ in range(int(max_wait * 10)):  # Check every 100ms
        current_status = await getBotStatus()
        
        if current_status == last_status:
            stable_count += 1
            if stable_count >= 3:  # 3 consecutive identical results
                return current_status
        else:
            stable_count = 0
            last_status = current_status
            
        await asyncio.sleep(0.1)
    
    raise TimeoutError(f"State never stabilized for {action_type}")
```

### Network Latency Handling

#### Variable Timing Test
```python
async def test_network_timing_variability():
    """Test if action completion time varies with network conditions."""
    completion_times = []
    
    for i in range(10):
        start_time = time.time()
        
        # Send action
        await send_websocket_command({"type": "move", "x": 0.1, "z": 0.0})
        
        # Wait for completion
        while True:
            status = await getBotStatus()
            if position_changed(status):
                completion_time = time.time() - start_time
                completion_times.append(completion_time)
                break
            await asyncio.sleep(0.01)
    
    # Analyze timing variability
    avg_time = sum(completion_times) / len(completion_times)
    max_time = max(completion_times)
    min_time = min(completion_times)
    
    print(f"Action completion times: avg={avg_time:.3f}s, range={min_time:.3f}-{max_time:.3f}s")
    
    # Validate reasonable consistency
    assert max_time - min_time < 0.5, f"Timing too variable: {min_time}-{max_time}s"
    
    return max_time * 1.5  # Recommended wait time = 1.5x max observed
```

### Command Queue Validation

#### Action Ordering Test
```python
async def test_action_sequence_ordering():
    """Verify commands execute in the order sent."""
    initial_status = await getBotStatus()
    
    # Send rapid sequence of commands
    commands = [
        {"type": "move", "x": 1.0, "z": 0.0},  # Move east
        {"type": "look", "movementX": 50},      # Look right
        {"type": "move", "x": 0.0, "z": 1.0},  # Move south
    ]
    
    for cmd in commands:
        await send_websocket_command(cmd)
        await asyncio.sleep(0.05)  # Small delay between commands
    
    # Wait for all actions to complete
    await asyncio.sleep(0.5)
    
    final_status = await getBotStatus()
    
    # Validate final state matches expected sequence result
    expected_pos = calculate_expected_final_position(initial_status, commands)
    actual_pos = parse_position(final_status)
    
    assert positions_match(expected_pos, actual_pos), f"Sequence failed: {expected_pos} vs {actual_pos}"
```

### Red Flags for Timing Issues

Watch for these symptoms indicating async timing problems:

1. **Inconsistent Validation Results**: Same action sometimes passes, sometimes fails
2. **Position Drift**: Small movements accumulate unexpected errors
3. **State Flickering**: getBotStatus alternates between old and new values
4. **Command Drops**: Actions logged but no game state change detected
5. **Order Scrambling**: Commands execute out of sequence

### Critical Timing Requirements

**For validation to be trustworthy:**

1. ✅ **Wait for Action Completion**: Every command must finish before getBotStatus
2. ✅ **State Stability**: getBotStatus must return consistent results  
3. ✅ **Predictable Timing**: Action completion times must be reasonably consistent
4. ✅ **Sequence Preservation**: Commands must execute in sent order
5. ✅ **No Race Conditions**: Validation timing must be deterministic

**If timing validation fails, all other validation results are unreliable.**

## getBotStatus Validation Protocol

**Critical**: `getBotStatus` calls provide the **ground truth** for validation. Each test must verify:

### Before Action:
```python
initial_status = await mcp_server.execute_tool("getBotStatus", {})
initial_position = parse_position(initial_status)
initial_rotation = parse_rotation(initial_status)
```

### After Action:
```python
final_status = await mcp_server.execute_tool("getBotStatus", {})
final_position = parse_position(final_status)
final_rotation = parse_rotation(final_status)
```

### Validation Logic:
```python
# For movement actions
actual_movement = final_position - initial_position
expected_movement = calculate_expected_from_websocket_command(command)
assert actual_movement == expected_movement, "Position mismatch!"

# For camera actions  
actual_rotation = final_rotation - initial_rotation
expected_rotation = calculate_expected_from_websocket_command(command)
assert actual_rotation == expected_rotation, "Rotation mismatch!"
```

**📊 getBotStatus Output Format** (controller_base.py:550):
```
====
Position: (30, 63, -18) facing East (-288.15°, -2.55°)
Biome: Sparse Jungle
Day 0, 8.71 minutes until sunset
Selected slot: 1
Hotbar: [0: Oak Sapling x3] [1: Jungle Log x1]
Looking at: Vines (is close enough to dig)
====
```

## Expected Validation Failures

Based on code analysis, expect these **fundamental inconsistencies**:

1. **Movement Direction Loss**: WebSocket preserves direction vectors, MCP only logs duration
2. **Camera Angle Mismatch**: WebSocket uses relative deltas, MCP uses absolute angles  
3. **Timing Granularity**: WebSocket sends continuous events, MCP logs discrete durations
4. **State vs Duration**: Some actions use state changes (WebSocket) vs duration (MCP)
5. **Camera Special Path**: Different execution route bypasses normal validation
6. **Async/Sync Timing**: Data collection vs direct execution timing differences

## Validation Success Criteria

**✅ PASS**: Both pygame and MCP modes produce identical `getBotStatus` results after the same user input

**❌ FAIL**: Any difference in:
- Final player position coordinates
- Final player rotation angles  
- Final game state (inventory, selected slot, etc.)

## Recommended Action

**If validation fails** (which is highly likely based on code analysis):

1. **Don't collect 50 trajectories with broken mapping** - the spatial reasoning data will be corrupted
2. **Fix the conversion logic** - preserve spatial information in MCP format
3. **Or redesign MCP protocol** - add direction parameters to `walk`, relative parameters to `lookAngle`  
4. **Or accept the abstraction level** - train AI on high-level actions, not low-level spatial movements

**The core question**: Are you training spatial reasoning or high-level task execution?


| Action Type | Pygame Mode (Ground Truth) | MCP Mode (Training Data Conversion) | Validation Conclusion & Consistency Risk | Remaining Gaps for Full Validation |
| :--- | :--- | :--- | :--- | :--- |
| **Movement**<br>(WASD/Joystick) | **WebSocket Command:**<br>`{"type": "move", "x": 0.5, "z": 0.3}`<br><br>**Behavior:** Sends a continuous stream of commands with precise direction vectors.<br><br>**Source:** `mode_strategy.py:161-171` | **MCP Tool Call:**<br>`{"tool": "walk", "parameters": {"duration": 1166}}`<br><br>**Behavior:** Converts the vector's *magnitude* into a duration but **discards the direction**.<br><br>**Source:** `action_converter.py:68-71` | 🔴 **HIGH - Confirmed Data Loss**<br><br>The tests conclusively prove that the direction vector is lost during conversion. The MCP command **cannot** reproduce the original spatial movement. <br><br>**Evidence:** `docs/movement_camera_consistency_report.md`, `tests/test_movement_camera_validation.py:89-105` | **Fix Required.** The inconsistency is proven. A fix would require redesigning the `walk` tool to accept direction parameters. The validation task of proving the inconsistency is complete. |
| **Camera Look**<br>(Mouse Drag) | **WebSocket Command:**<br>`{"type": "look", "movementX": 20, "movementY": -10}`<br><br>**Behavior:** Sends relative mouse pixel movements, which are first scaled by 2x.<br><br>**Source:** `action_handler.py:178-188` | **MCP Tool Call:**<br>`{"tool": "lookAngle", "parameters": {"xAngle": 4.0, "yAngle": 2.0}}`<br><br>**Behavior:** Converts cumulative pixel delta into an absolute angle change using a hardcoded sensitivity constant.<br><br>**Source:** `look_path.py:321-331`, `action_converter.py:25` | 🔴 **HIGH - Unvalidated Conversion**<br><br>The conversion from relative pixels to absolute degrees relies on `SENSITIVITY = 5.0` matching the game's internal logic. This has **not** been validated against a live game.<br><br>**Evidence:** `docs/movement_camera_consistency_report.md` | **Live Integration Test Required.** A pixel-to-degree calibration test must be performed by comparing the converted angle to the actual yaw/pitch change from `getBotStatus` after a controlled mouse drag. |
| **Left Click**<br>(Mouse/Button) | **WebSocket Command:**<br>`{"type": "leftDown"}` ... `{"type": "leftUp"}`<br><br>**Behavior:** Sends simple state changes. This is **known to work** for inventory interactions.<br><br>**Source:** `action_handler.py:190-205` | **MCP Tool Call:**<br>`{"tool": "leftClick", "parameters": {"duration": "short"}}`<br><br>**Behavior:** Sends a different command, `documentMouseEvent`. This is **known to be broken** for inventory interactions.<br><br>**Source:** `docs/inventory-interaction-debug-guide.md` | ❌ **FAILED - Confirmed Inconsistency**<br><br>There is a fundamental, documented command mismatch that breaks inventory management. The two modes do not behave identically. <br><br>**Evidence:** `docs/inventory-interaction-debug-guide.md` | **Fix Required.** The root cause must be fixed. The proposed long-term solution is to unify all inputs via a **Virtual Gamepad Emulator** as detailed in `docs/gamepad-emulation-architecture.md`. |
| **Right Click**<br>(Mouse/Button) | **WebSocket Command:**<br>`{"type": "rightDown"}` ... `{"type": "rightUp"}`<br><br>**Behavior:** Sends simple state changes for placing blocks, etc.<br><br>**Source:** `action_handler.py:207-222` | **MCP Tool Call:**<br>`{"tool": "rightClick", "parameters": {"duration": "long"}}`<br><br>**Behavior:** Converts hold time into a duration parameter. The underlying command sent may also be inconsistent.<br><br>**Source:** `action_handler.py:84-103` | 🟡 **MEDIUM - Potential Inconsistency**<br><br>While the duration calculation logic is validated (`test_action_handler.py:59-67`), it likely suffers from the same command type mismatch as Left Click. | **Live Integration Test Required.** Test block placement and other right-click interactions to ensure the command type sent by the MCP path works identically to the pygame path. |
| **Jump**<br>(Space/Button) | **WebSocket Command:**<br>`{"type": "control", "control": "jump", "state": true/false}`<br><br>**Behavior:** Sends state-based commands.<br><br>**Source:** `action_handler.py:224-232` | **MCP Tool Call:**<br>`{"tool": "jump", "parameters": {"duration": "short"}}`<br><br>**Behavior:** Converts the state change into a timed, duration-based action.<br><br>**Source:** `action_converter.py:274-278` | 🟡 **MEDIUM - State vs. Duration**<br><br>The representations are different (a state vs. a timed event). While less critical than movement, this is still an inconsistency. The internal logic is validated.<br><br>**Evidence:** `test_action_handler.py:106-113` | **Live Integration Test Required.** After a jump action, call `getBotStatus` and verify the player's Y-coordinate changed as expected. |
| **Sneak/Sprint**<br>(Shift/Ctrl Toggle)| **WebSocket Command:**<br>`{"type": "control", "control": "sneak", "state": true/false}`<br><br>**Behavior:** Sends a state toggle.<br><br>**Source:** `action_handler.py:234-240` | **MCP Tool Call:**<br>`{"tool": "sneak", "parameters": {"state": true/false}}`<br><br>**Behavior:** Directly maps the state toggle.<br><br>**Source:** `action_converter.py:279-288` | 🟢 **LOW - Consistent Mapping**<br><br>The WebSocket and MCP commands are semantically identical and represent the same action. This is a direct, consistent mapping.<br><br>**Evi=dence:** `test_action_handler.py:70-79` | Minimal. A simple integration test could confirm the state change in `getBotStatus`, but this is not a high-priority risk. |
| **Hotbar/Drop/Swap**<br>(1-9, Q, F keys) | **WebSocket Command:**<br>`{"type": "setHotbarSlot", "slot": 3}`<br><br>**Behavior:** Sends a simple, direct command with parameters that map 1:1.<br><br>**Source:** `action_handler.py:261-291` | **MCP Tool Call:**<br>`{"tool": "setHotbarSlot", "parameters": {"slot": 3}}`<br><br>**Behavior:** The MCP tool call is a direct 1:1 representation of the Pygame command.<br><br>**Source:** `action_converter.py:269-303` | 🟢 **LOW - Consistent Mapping**<br><br>These actions have direct, unambiguous mappings between Pygame and MCP formats. The logic is validated.<br><br>**Evidence:** `test_action_handler.py:82-88` | Minimal. An integration test confirming the `selected_slot` or inventory state in `getBotStatus` would provide full confidence. |
| **`getBotStatus`**<br>(State Validation) | N/A | N/A | ❌ **FAILED - No Live Validation**<br><br>The parser for `getBotStatus` output is robust (`tests/test_getbotstatus_parser.py`), but there are **zero tests** that call `getBotStatus` on a live game instance to validate its consistency or accuracy. All "ground truth" is currently unverified.<br><br>**Evidence:** `docs/getbotstatus_consistency.md` and its follow-ups. | **Live Integration Tests are Essential.** All the "Remaining Gaps" for other actions depend on this. Tests must be created to check for data jitter, timing variability, and action outcome verification against a real Minecraft client. |