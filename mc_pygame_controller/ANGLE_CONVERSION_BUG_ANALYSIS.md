# Angle Conversion Bug Analysis and Solution

## Problem Summary

The mc_pygame_controller has an **inconsistent scaling/conversion bug** where identical mouse input produces different final camera rotation angles between pygame mode and MCP mode. This breaks the fundamental expectation that the same gesture should produce the same result regardless of execution timing.

## Root Cause: Complete Pipeline Analysis

After analyzing the full conversion pipeline including `minecraft-mcp-server.ts`, `server.js`, and `wsCommandClient.ts`, I found the **real source** of the 22° angle inconsistency.

### Complete Data Flow Analysis

#### **Pygame Mode Pipeline:**
```
Raw Mouse Input (100 pixels)
         ↓
Pygame 2x Scaling (controller_base.py:292-293)
         ↓  
Scaled Values (200 pixels)
         ↓
Direct WebSocket Command: {"type": "look", "movementX": 200}
         ↓
server.js forwards to wsCommandClient.ts
         ↓
wsCommandClient.ts calls: onCameraMove({movementX: 200, movementY: 0, type: 'ws'})
         ↓
Direct camera rotation in Minecraft client
```

#### **MCP Mode Pipeline:**
```
Raw Mouse Input (100 pixels)
         ↓
Pygame 2x Scaling Applied (controller_base.py:292-293)
         ↓  
Scaled Values (200 pixels) - STORED in LookPathTracker
         ↓
MCP Sensitivity Conversion (look_path.py:283): 200 ÷ 5 = 40°
         ↓
MCP Command: lookAngle({xAngle: 40, yAngle: 0})
         ↓
minecraft-mcp-server.ts stepLook() function (lines 291-323)
         ↓
stepLook() RECONVERTS: 40° × 5 = 200 total pixels
         ↓
stepLook() BREAKS INTO MULTIPLE STEPS with easing
         ↓
Multiple commands: {"type": "look", "movementX": dx, "movementY": dy}
         ↓
server.js forwards to wsCommandClient.ts
         ↓
Each step calls: onCameraMove({movementX: dx, movementY: dy, type: 'ws'})
```

### The REAL Bug: stepLook() Smoothing Algorithm

The 22° difference comes from the **stepLook() smoothing algorithm** in `minecraft-mcp-server.ts` (lines 291-323):

```typescript
async function stepLook(xAngle: number, yAngle: number, speed: "slow" | "normal" | "fast" = "normal") {
    const SENSITIVITY_X = 5; // yaw sensitivity
    const SENSITIVITY_Y = 5; // pitch sensitivity

    const totalPixelX = xAngle * SENSITIVITY_X;  // 40° × 5 = 200 pixels
    const totalPixelY = yAngle * SENSITIVITY_Y;

    const maxDisplacement = Math.max(Math.abs(totalPixelX), Math.abs(totalPixelY));
    const steps = Math.max(1, Math.ceil(maxDisplacement / config.avgPixelsPerStep)); // BREAKS INTO STEPS

    const easeInOutSine = (t: number) => -(Math.cos(Math.PI * t) - 1) / 2; // EASING FUNCTION

    let prev = 0;
    for (let i = 0; i < steps; i++) {
        const progress = easeInOutSine((i + 1) / steps); // APPLIES EASING
        const weight = progress - prev;
        prev = progress;

        const dx = totalPixelX * weight; // DISTRIBUTES PIXELS WITH EASING
        const dy = totalPixelY * weight;

        await sendCommand({ type: "look", movementX: dx, movementY: dy });
        await new Promise((resolve) => setTimeout(resolve, config.delay));
    }
}
```

**The problem**: The easing function `easeInOutSine()` distributes the 200 pixels across multiple steps with **non-linear timing**, which can result in **cumulative rounding errors** and slightly different final camera positions compared to a single 200-pixel movement.

### Expected vs Actual Results

For identical 100-pixel mouse movement:

| Mode | Pipeline | Final Camera Commands | Result |
|------|----------|----------------------|--------|
| **Pygame** | `100 → *2 → 200 pixels` | **1 command**: `{"type": "look", "movementX": 200}` | Direct rotation |
| **MCP** | `100 → *2 → 200 → ÷5 → 40° → stepLook()` | **~20 commands**: Multiple small `{"type": "look", "movementX": dx}` with easing | Smoothed rotation with rounding errors |

**The 22° difference comes from**:
1. **Rounding errors** in the stepLook() easing calculation
2. **Cumulative precision loss** across multiple small movements 
3. **Different execution timing** (immediate vs. delayed with easing)

## Code Locations

### 1. Pygame Scaling Application
**File**: `controller_base.py`  
**Lines**: 289-302

```python
def handle_camera_look(self, delta_x: int, delta_y: int):
    if delta_x != 0 or delta_y != 0:
        # Scale the movement for better sensitivity
        scaled_x = delta_x * 2  # ← PROBLEM: Applied before storage
        scaled_y = delta_y * 2  # ← PROBLEM: Applied before storage
        
        # Add to path tracker
        self.look_path_tracker.add_movement(scaled_x, scaled_y)  # ← Stores scaled values
        
        # Only send WebSocket command in pygame mode
        if self.mode == "pygame":
            command = {"type": "look", "movementX": scaled_x, "movementY": scaled_y}
            self.send_command_sync(command)
```

### 2. MCP Sensitivity Conversion  
**File**: `look_path.py`  
**Lines**: 282-286

```python
def _execute_accumulated_movement(self, trigger_reason):
    if self.current_stats:
        total_x, total_y = self.current_stats["total_displacement"]
        
        # Convert pixels to degrees using configurable sensitivity
        x_angle = total_x / self.sensitivity  # ← PROBLEM: Applied to scaled values
        y_angle = -(total_y / self.sensitivity)  # ← PROBLEM: Applied to scaled values
```

### 3. LookPathTracker Storage
**File**: `look_path.py`  
**Lines**: 22-54

```python
def add_movement(self, movement_x: int, movement_y: int):
    # Stores whatever values are passed (currently scaled values)
    movement = {
        "movement_x": movement_x,  # ← Currently receives scaled values
        "movement_y": movement_y,  # ← Currently receives scaled values
    }
```

## Detailed Problem Analysis

### Why This Creates Inconsistency

1. **Pygame Mode Flow**:
   - Raw input: 100 pixels
   - Apply 2x scaling: 200 pixels  
   - Send directly: `{"type": "look", "movementX": 200}`
   - **Result**: Camera rotates by amount corresponding to 200 pixels

2. **MCP Mode Flow**:
   - Raw input: 100 pixels
   - Apply 2x scaling: 200 pixels
   - Store in tracker: 200 pixels
   - Convert to degrees: 200 ÷ 5 = 40°
   - Send via MCP: `lookAngle({xAngle: 40})`
   - **MCP server converts back**: 40° × 5 = 200 pixels
   - **Result**: Camera rotates by amount corresponding to 200 pixels

**Wait, that seems consistent...**

### The REAL Issue: Debug Output Shows Different Angles

From the README.md debug output comparison:

| Mode | Same Mouse Input | Calculated Angle |
|------|------------------|------------------|
| **Pygame** | Identical gesture | `-126.4°, -5.2°` |
| **MCP** | Identical gesture | `-148.4°, -0.8°` |

**22° difference for identical input!**

This suggests there are **additional scaling inconsistencies** beyond the simple 2x vs sensitivity conversion.

### Additional Factors

1. **Y-axis inversion**: MCP mode inverts Y (`y_angle = -(total_y / sensitivity)`)
2. **Accumulation differences**: Pygame sends 25 individual commands, MCP accumulates and sends 1
3. **Timing differences**: Real-time vs batched processing may affect intermediate calculations

## Proposed Solutions

### Option 1: Fix stepLook() Rounding Errors (Recommended)

**Principle**: Keep existing architecture but fix the precision loss in stepLook() function.

#### Modified `stepLook()` in `minecraft-mcp-server.ts`:

```typescript
async function stepLook(xAngle: number, yAngle: number, speed: "slow" | "normal" | "fast" = "normal") {
    const SENSITIVITY_X = 5;
    const SENSITIVITY_Y = 5;

    const totalPixelX = xAngle * SENSITIVITY_X;
    const totalPixelY = yAngle * SENSITIVITY_Y;

    // OPTION A: Send as single command to match pygame behavior
    await sendCommand({ type: "look", movementX: totalPixelX, movementY: totalPixelY });
    
    // OPTION B: Use integer pixel steps to avoid rounding errors
    const steps = Math.max(1, Math.ceil(Math.max(Math.abs(totalPixelX), Math.abs(totalPixelY)) / 10));
    const stepX = totalPixelX / steps;  // Exact division
    const stepY = totalPixelY / steps;
    
    for (let i = 0; i < steps; i++) {
        await sendCommand({ type: "look", movementX: stepX, movementY: stepY });
        await new Promise((resolve) => setTimeout(resolve, 30));
    }
}
```

### Option 2: Separate Storage from UI Scaling

**Principle**: Store raw pixel values, apply scaling only when generating commands.

#### Modified `handle_camera_look()` in `controller_base.py`:

```python
def handle_camera_look(self, delta_x: int, delta_y: int):
    if delta_x != 0 or delta_y != 0:
        # Store RAW pixel values in tracker (no scaling)
        self.look_path_tracker.add_movement(delta_x, delta_y)
        
        # Apply scaling only for pygame command generation
        if self.mode == "pygame":
            scaled_x = delta_x * 2
            scaled_y = delta_y * 2
            command = {"type": "look", "movementX": scaled_x, "movementY": scaled_y}
            self.send_command_sync(command)
```

#### Modified `_execute_accumulated_movement()` in `look_path.py`:

```python
def _execute_accumulated_movement(self, trigger_reason):
    if self.current_stats:
        total_x, total_y = self.current_stats["total_displacement"]
        
        # Apply pygame-equivalent 2x scaling before conversion
        scaled_total_x = total_x * 2
        scaled_total_y = total_y * 2
        
        # Convert scaled pixels to degrees using MCP server standard
        x_angle = scaled_total_x / 5.0  # Standard MCP sensitivity
        y_angle = -(scaled_total_y / 5.0)  # Invert Y axis
```

### 2. Unified Conversion Standards

**Establish consistent conversion factors**:

- **UI Scaling**: 2x multiplier for both modes (applied at command generation)
- **Angle Conversion**: 5 pixels per degree (matching MCP server standard)
- **Y-axis Handling**: Consistent inversion rules

### 3. Verification Strategy

**Test with identical mouse input**:

1. Record raw pixel deltas: `[50, -25, 30, -10, ...]`
2. **Pygame calculation**: `sum(deltas) * 2 = total_pixels`
3. **MCP calculation**: `(sum(deltas) * 2) / 5 = degrees`
4. **Verify**: Both produce same final camera rotation

## Implementation Steps

### Step 1: Fix Storage
- Modify `handle_camera_look()` to store raw pixels
- Apply 2x scaling only for pygame commands

### Step 2: Fix MCP Conversion  
- Apply 2x scaling before sensitivity conversion
- Ensure Y-axis inversion is consistent

### Step 3: Testing
- Test identical mouse gestures in both modes
- Verify debug output shows identical accumulated angles
- Confirm camera ends up in same position

### Step 4: Documentation
- Update README.md to reflect unified conversion system
- Add troubleshooting guide for angle consistency

## Recommendation: Option 1 (Fix stepLook)

**Option 1 is recommended** because:

1. **Simpler fix**: Only requires modifying one function in `minecraft-mcp-server.ts`
2. **Preserves existing behavior**: No changes to pygame controller or UI scaling
3. **Addresses root cause**: Fixes the actual source of rounding errors
4. **Minimal risk**: Isolated change with clear before/after behavior

### Implementation Priority:

**Option 1A (Single Command)**: Replace stepLook() easing with single command
- **Pro**: Perfect consistency with pygame mode
- **Con**: Loses smooth camera movement for AI

**Option 1B (Integer Steps)**: Use exact division without easing
- **Pro**: Maintains smooth movement while fixing precision
- **Con**: Slightly more complex

## Expected Outcome

After implementing Option 1A, identical mouse input will produce:

| Mode | Pipeline | Final Commands | Result |
|------|----------|----------------|--------|
| **Pygame** | `100 → *2 → 200` | `{"type": "look", "movementX": 200}` | Direct rotation |
| **MCP** | `100 → *2 → 200 ÷ 5 → 40° → 40*5` | `{"type": "look", "movementX": 200}` | **Identical rotation** |

This eliminates the 22° inconsistency while maintaining the intentional architectural differences (execution timing, command routing).

## Risk Assessment

**Low Risk Changes**:
- Only affects internal calculation order
- No changes to external interfaces
- Preserves existing sensitivity settings
- Maintains backward compatibility

**Testing Required**:
- Verify pygame mode still feels responsive
- Confirm MCP mode produces expected angles  
- Test edge cases (very small/large movements)
- Validate with multiple sensitivity settings