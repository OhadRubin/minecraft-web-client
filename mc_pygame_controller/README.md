# mc_pygame_controller
A sophisticated pygame-based controller for Minecraft Web Client that provides both manual control and AI-driven autonomous gameplay through MCP (Model Context Protocol) integration. **Core component of the 3D Visual SKETCHPAD research project for collecting spatial reasoning training data.**

## Research Context

This controller is part of a larger research pipeline aimed at **collecting 50K Visual SKETCHPAD trajectories for 3D spatial reasoning** and demonstrating transfer to web agents and other domains. The system captures human demonstrations of 3D spatial reasoning tasks in Minecraft, converting them into training data for AI agents.

**Research Pipeline**:
- **Phase 0**: Implement 3D Visual SKETCHPAD tools (MVP) ✅
- **Phase 1**: Collect 50 manual examples 
- **Phase 2**: Finetune GPT-4.1-nano on examples
- **Phase 3**: Use finetuned model to collect 1K trajectories
- **Phase 4-7**: Scale to 50K trajectories and evaluate transfer

**Core Hypothesis**: 3D spatial reasoning skills learned in Minecraft will transfer to web agent tasks and other domains.

## Overview

The `mc_pygame_controller` is a dual-mode interface that bridges human input and AI control for Minecraft gameplay. It supports:

- **pygame mode**: Direct WebSocket communication with Minecraft Web Client for human control
- **MCP mode**: AI-driven autonomous gameplay using Model Context Protocol servers
- **3D annotation development**: Core `annotate_3d_position` tool implementation

## Architecture

### Complete System Architecture

The mc_pygame_controller operates within a larger ecosystem of interconnected services:

```
┌─────────────────────┐    ┌─────────────────────┐    ┌──────────────────────┐
│  pygame Controller  │    │   minecraft-mcp-    │    │   Minecraft Web      │
│  (This Module)      │◄──►│   server.ts         │◄──►│   Client (Browser)   │
│                     │    │   (MCP Tools)       │    │   (Three.js/WebGL)   │
└─────────────────────┘    └─────────────────────┘    └──────────────────────┘
           │                          │                          │
           └──────────────────────────┼──────────────────────────┘
                                      ▼
                            ┌─────────────────────┐
                            │    server.js        │
                            │  (WebSocket Relay)  │
                            │   Port 8081         │
                            └─────────────────────┘
```

**Key Components:**

1. **server.js (WebSocket Relay Server)**: Central message routing hub
   - Manages three client types: `bot`, `pygame`, `mcp`
   - Routes messages between pygame controller ↔ Minecraft client
   - Routes messages between MCP server ↔ Minecraft client
   - Runs on port 8081 (WebSocket) + 8080 (HTTP)

2. **minecraft-mcp-server.ts (MCP Tools)**: Provides AI control capabilities
   - Tools: `walk`, `lookAngle`, `leftClick`, `rightClick`, `getBotStatus`, `wait`
   - **3D Visual SKETCHPAD tool**: `annotate_3d_position` (in development)
   - Screenshot capture with status overlay
   - Connects as `mcp` client to WebSocket server

3. **Minecraft Web Client (Browser)**: The actual game interface
   - Three.js WebGL renderer with scene access (`window.world.scene`)
   - Receives commands via WebSocket, executes in game world
   - Registers as `bot` client to WebSocket server
   - Provides visual feedback and screenshots

4. **mc_pygame_controller (This Module)**: Human interface and demonstration capture
   - Registers as `pygame` client to WebSocket server
   - Captures human spatial reasoning demonstrations
   - Converts to PygameMCPAsyncMessageChain format for AI training

### Message Flow Architecture

```
Human Input → pygame Controller → WebSocket Server → Minecraft Client → Visual Feedback
     ↑                                    ↕                              ↓
Agent Loop ← MCP Server ← MCP Tools ←─────┘                        Screenshots
     ↑                     ↓
Training Data ←─── Trajectory Recording
```

**Data Flow Steps:**
1. **Human demonstrates** spatial reasoning task via pygame interface
2. **pygame controller** sends WebSocket commands to Minecraft client  
3. **Minecraft client** executes actions and updates visual scene
4. **Screenshots captured** showing results of spatial reasoning
5. **Trajectory recorded** in PygameMCPAsyncMessageChain format
6. **Training data** used to teach AI agents spatial reasoning skills

### Three-Client-Type System

The WebSocket server manages three distinct client types:

- **`bot` clients**: Minecraft Web Client instances that execute commands
- **`pygame` clients**: This pygame controller for human demonstrations  
- **`mcp` clients**: MCP servers providing AI control tools

**Message Routing Rules:**
- `pygame` → `bot`: Human commands forwarded to Minecraft
- `mcp` → `bot`: AI tool calls forwarded to Minecraft  
- `bot` → `mcp`: Game state/screenshots sent to AI tools
- `bot` → `pygame`: Status updates sent to human interface

### Core Components

#### 1. Controller Layer (`controller_base.py`, `controller.py`)

**MinecraftController** - The main controller class that manages:
- pygame display and input handling
- WebSocket communication with Minecraft Web Client
- UI element management and rendering
- Dual-mode operation (pygame/MCP)

Key features:
- Configurable mouse sensitivity for camera control
- Asynchronous event loop integration
- Real-time UI updates at 60 FPS
- State management for all game controls

#### 2. MCP Integration Layer (`mcp_client.py`)

**Server** - Manages MCP server connections and tool execution:
- Stdio-based communication with MCP servers
- Tool discovery and schema generation
- Async tool execution with retry mechanisms
- Resource cleanup and error handling

**Configuration** - Handles environment and server configuration:
- Environment variable loading
- JSON-based server configuration
- API key management

#### 3. Message Chain System (`chain.py`, `message_chain.py`)

**PygameMCPAsyncMessageChain** - Immutable message chain for AI conversations:
- Functional approach with method chaining
- OpenAI-compatible tool integration
- Multimodal content support (text, images, audio)
- Automatic tool call execution and response handling

**ConversationPanel** - Manages conversation state for MCP integration:
- Message processing for AI communication
- Integration with PygameMCPAsyncMessageChain system
- Development foundation for future data collection

#### 4. Look Path System (`look_path.py`)

**LookPathTracker** - Advanced camera movement analysis:
- Real-time movement accumulation during drag operations
- Angle analysis and compass direction calculation
- Configurable sensitivity (pixels to degrees conversion)
- Automatic MCP command generation from mouse movements

**LookPathVisualizationArea** - Real-time visualization:
- Grid-based movement path display
- Live angle analysis statistics
- Drag operation status indicators

#### 5. User Interface (`ui_elements.py`)

Comprehensive UI component library:
- **Button**: Standard clickable buttons
- **ToggleButton**: Stateful toggle controls
- **VirtualJoystick**: Analog movement control
- **KeyboardMovement**: WASD keyboard input handling
- **TouchArea**: Large camera control area with drag detection

#### 6. Interface & Demonstration System (`interface.py`)

**MinecraftControllerInterface** - Interface for MCP integration:
- MCP command execution and result handling
- Integration with PygameMCPAsyncMessageChain system
- Development foundation for spatial reasoning tools

**TrajectoryStorage** - Data management system:
- Foundation for future demonstration recording
- JSON data structure support
- Development infrastructure

### Human-to-LLM Action Translation System

**Core Translation Mechanism**: The controller captures human pygame actions and converts them into LLM-compatible message chains using a multi-step process:

#### 1. Action Capture & MCP Conversion (`controller_base.py`)

**Primary Translation Method**: `convert_to_mcp_format()` (lines 450-504)
```python
# Example: Button click → MCP tool call
def convert_to_mcp_format(self, command_type, params):
    if command_type == "left_click":
        return {"tool": "leftClick", "parameters": {"duration": "medium"}}
    elif command_type == "walk": 
        return {"tool": "walk", "parameters": {"duration": params.get("duration", 1000)}}
```

**Action Execution Pipeline**: `execute_mcp_action()` → `interface.capture_command()` → trajectory storage

#### 2. Mouse Movement Translation (`look_path.py`)

**Drag-to-Command System**: 
- Mouse drag in camera area accumulates pixel movements
- On release: converts to discrete `lookAngle` command
- **Conversion Formula**: `x_angle = total_x / sensitivity` (pixels → degrees)

```python
# Example output from mouse drag
mcp_command = {
    "tool": "lookAngle",
    "parameters": {"xAngle": 45.0, "yAngle": -12.0, "speed": "normal"}
}
```

#### 3. Trajectory Recording (`interface.py`, `conversation.py`)

**Recording Flow**:
1. `start_trajectory_recording()` - Initialize capture session
2. `capture_command()` - Store each human action as MCP tool call  
3. `convert_actions_to_mock_response()` - Convert to OpenAI message format
4. `stop_trajectory_recording()` - Save as training data

**Output Format** (OpenAIAsyncMessageChain compatible):
```json
{
  "content": "I'll look around and move forward to explore.",
  "tool_calls": [
    {"function": {"name": "lookAngle", "arguments": "{\"xAngle\": 45.0}"}},
    {"function": {"name": "walk", "arguments": "{\"duration\": 1000}"}}
  ]
}
```

#### 4. **CRITICAL ISSUE**: Mode Inconsistency Problem

**Current Major Problem**: MCP mode behaves differently than pygame mode when using the same interface, causing inconsistent and unexpected cursor/camera behavior.

**Pygame Mode (Works Correctly)**:
- Mouse movements in camera area → immediate `{"type": "look", "movementX": int, "movementY": int}` WebSocket commands
- Real-time, continuous camera control that feels natural
- Direct 1:1 mapping between mouse movement and camera response

**MCP Mode (Inconsistent Behavior)**:
- Mouse movements → accumulated in LookPathTracker → executed as discrete `lookAngle` commands on drag completion
- Delayed, batched camera control that feels unnatural
- Different sensitivity/conversion logic causes unexpected camera jumps

#### 5. Root Cause Analysis

**The Core Problem**: Two different execution paths for the same user input:

```python
# In handle_camera_look() - controller_base.py:296-302
if self.mode == "pygame":
    # Direct, immediate execution
    command = {"type": "look", "movementX": scaled_x, "movementY": scaled_y}
    self.send_command_sync(command)
else:
    # MCP mode: accumulated, delayed execution via LookPathTracker
    # Uses different sensitivity calculation and timing
```

**Specific Issues**:
1. **Different sensitivity handling**: Pygame uses `scaled_x = delta_x * 2`, MCP uses `x_angle = total_x / self.sensitivity`
2. **Timing differences**: Pygame = immediate, MCP = on mouse release only
3. **Coordinate system**: Pygame uses pixel deltas, MCP converts to degrees
4. **Accumulation logic**: MCP batches movements, pygame sends individual movements

**Result**: Same mouse gesture produces completely different camera behavior between modes, making MCP mode unusable for normal gameplay.

#### 6. **CRITICAL ARCHITECTURE ISSUE**: Dual Event Loop System

**Root Cause**: The system runs **two completely separate event loops** with **duplicated mouse tracking logic** that can get out of sync.

**Event Loop Architecture**:

| Mode | Event Loop | File Location | Line Range |
|------|------------|---------------|------------|
| **Pygame Mode** | `_run_pygame_loop()` | `controller_base.py` | Lines 669-901 |
| **MCP Mode** | `animation_loop()` | `controller_base.py` | Lines 1015-1085 |

**Critical Code Duplication**: Mouse tracking logic exists in **both loops**:

```python
# Location 1: _run_pygame_loop() (lines 796-815)
camera_is_clicking = self.camera_area.is_touching and mouse_pressed
prev_clicking = getattr(self, "camera_was_clicking", False)
if camera_is_clicking and not prev_clicking:
    self.look_path_tracker.start_mouse_tracking()
    self.camera_was_clicking = True

# Location 2: animation_loop() (lines 1055-1074) - MUST BE IDENTICAL
camera_is_clicking = self.camera_area.is_touching and mouse_pressed  
prev_clicking = getattr(self, "camera_was_clicking", False)
if camera_is_clicking and not prev_clicking:
    self.look_path_tracker.start_mouse_tracking()
    self.camera_was_clicking = True
```

**⚠️ MAINTENANCE CRITICAL**: Any changes to mouse tracking **must be applied to both locations** or modes will behave differently.

#### 7. Mouse Tracking State Machine

**Complete State Flow Documentation**:

```
[Mouse Outside Camera] → [Mouse Enters Camera] → [Mouse Pressed] → [Dragging] → [Mouse Released] → [Command Executed]
        ↓                        ↓                     ↓              ↓              ↓               ↓
   No tracking            No tracking         start_mouse_tracking()  accumulate    stop_mouse_tracking()  reset
   camera_was_clicking=?  camera_was_clicking=?  camera_was_clicking=True  movements   camera_was_clicking=False  state
```

**State Variables**:
- `self.camera_was_clicking` (controller level) - Tracks if mouse was previously clicking in camera area
- `self.mouse_tracking_active` (LookPathTracker level) - Tracks if currently accumulating movements
- `self.camera_area.is_touching` - Whether mouse is currently over camera area
- `mouse_pressed` - Whether left mouse button is currently pressed

**State Transition Logic**:

```python
# State Detection
camera_is_clicking = self.camera_area.is_touching and mouse_pressed
prev_clicking = getattr(self, "camera_was_clicking", False)

# Transition 1: Start Drag (False → True)
if camera_is_clicking and not prev_clicking:
    print("🖱️ Mouse pressed in camera area - starting drag tracking")
    self.look_path_tracker.start_mouse_tracking()  # Sets mouse_tracking_active=True
    self.camera_was_clicking = True

# Transition 2: End Drag (True → False)  
elif not mouse_pressed and prev_clicking:
    print("🖱️ Mouse released - ending drag tracking")
    self.look_path_tracker.stop_mouse_tracking()   # Sets mouse_tracking_active=False, executes command
    self.camera_was_clicking = False
```

**Critical Python Gotcha** - State Detection Anti-Pattern:

```python
# ❌ BROKEN - hasattr() returns True even when value is False
if hasattr(self, "camera_was_clicking"):
    # This will ALWAYS be True after first drag, even when camera_was_clicking=False
    # Causes "works first time only" bug

# ✅ CORRECT - getattr() returns actual value or default
if getattr(self, "camera_was_clicking", False):
    # This correctly evaluates the boolean value
```

#### 8. Debug Output Reference Guide

**Normal Successful Drag Output**:
```
🖱️ Mouse pressed in camera area - starting drag tracking (was_clicking: False)
🖱️ Started drag operation - accumulating movements
🖱️ Mouse released - ending drag tracking (mouse_pressed: False)  
🖱️ Drag completed (0.5s) - executing command
📊 Drag analysis (drag_complete):
   🎯 Camera rotation: -128.8°, -1.2°
   ✅ Executing MCP command
🗑️ Reset drag tracking data
```

**Failure Pattern 1: "Works First Time Only"**
```
# First drag - works
🖱️ Mouse pressed in camera area - starting drag tracking
🖱️ Started drag operation - accumulating movements
🖱️ Mouse released - ending drag tracking
   ✅ Executing MCP command

# Second drag - fails (missing start message)
🚫 Movement ignored: tracking not active (42, 0)
🚫 Movement ignored: tracking not active (100, -6)
```
**Diagnosis**: `camera_was_clicking` state not resetting properly. Check for `hasattr()` vs `getattr()` bug.

**Failure Pattern 2: "Movements Ignored"**
```
🚫 Movement ignored: tracking not active (42, 0)
🚫 Movement ignored: tracking not active (100, -6)
```
**Diagnosis**: `mouse_tracking_active=False` in LookPathTracker. Either:
- `start_mouse_tracking()` never called (check controller state logic)
- Called but `mouse_tracking_active` not set to `True` (check LookPathTracker logic)

**Failure Pattern 3: "No Execution Callback"**
```
📊 Drag analysis (drag_complete):
   🎯 Camera rotation: -128.8°, -1.2°
   ⚠️  No execution callback set - command not executed
```
**Diagnosis**: MCP mode but `self.execution_callback` not set. Check line 199 in constructor.

**Debug State Inspection Commands**:
```python
# Add these to debugging sessions:
print(f"camera_was_clicking: {getattr(self, 'camera_was_clicking', 'NOT_SET')}")
print(f"mouse_tracking_active: {self.look_path_tracker.mouse_tracking_active}")
print(f"execution_callback set: {self.look_path_tracker.execution_callback is not None}")
print(f"camera_area.is_touching: {self.camera_area.is_touching}")
print(f"mouse_pressed: {mouse_pressed}")
```

#### 9. Common Failure Patterns & Root Causes

**Pattern 1: Mode Inconsistency**
- **Symptom**: Same mouse gesture behaves differently in pygame vs MCP mode
- **Root Cause**: Event loop code drift - one loop updated, other wasn't
- **Detection**: Compare lines 796-815 vs lines 1055-1074 in `controller_base.py`
- **Fix**: Manually sync both event loops

**Pattern 2: State Management Bugs**  
- **Symptom**: "Works first time only" behavior
- **Root Cause**: `hasattr()` used instead of `getattr()` for boolean state
- **Detection**: Search codebase for `hasattr(self, "camera_was_clicking")`
- **Fix**: Replace with `getattr(self, "camera_was_clicking", False)`

**Pattern 3: Callback Setup Issues**
- **Symptom**: Drag analysis prints but no command execution in MCP mode
- **Root Cause**: `set_execution_callback()` not called or called with wrong executor
- **Detection**: Check constructor line 199, verify `interface.set_controller()` called
- **Fix**: Ensure MCP mode sets callback: `self.look_path_tracker.set_execution_callback(self.execute_mcp_action)`

**Pattern 4: Movement Filtering Issues**
- **Symptom**: All movements ignored with "tracking not active" messages
- **Root Cause**: `mouse_tracking_active` flag stuck at `False`
- **Detection**: Check if `start_mouse_tracking()` is being called
- **Fix**: Verify controller drag detection logic and state transitions

#### 10. Step-by-Step Troubleshooting Procedures

**Procedure 1: Diagnose Mode Inconsistency**
1. Test same mouse gesture in both pygame and MCP modes
2. Compare debug output - should be nearly identical
3. If different, check event loop code at lines 796-815 vs 1055-1074
4. Manually diff the two sections and sync any differences
5. Test again to verify consistency

**Procedure 2: Debug "Works First Time Only"**
1. Add debug output: `print(f"camera_was_clicking: {getattr(self, 'camera_was_clicking', 'NOT_SET')}")`
2. Perform first drag - should show transition from `NOT_SET` → `True` → `False`
3. Perform second drag - should show transition from `False` → `True` → `False`
4. If second drag doesn't show `False` → `True`, search for `hasattr()` usage
5. Replace all `hasattr(self, "camera_was_clicking")` with `getattr(self, "camera_was_clicking", False)`

**Procedure 3: Debug Movement Tracking**
1. Enable movement debug: `print(f"🚫 Movement ignored: tracking not active ({movement_x}, {movement_y})")`
2. If seeing ignored movements, check if `start_mouse_tracking()` was called
3. Add debug to controller: `print("🖱️ Mouse pressed in camera area - starting drag tracking")`
4. If start message missing, verify `camera_is_clicking` logic and state detection
5. If start message present but movements still ignored, check LookPathTracker state

**Procedure 4: Verify MCP Integration**
1. Check constructor sets callback: `if self.mode == "mcp": self.look_path_tracker.set_execution_callback(...)`
2. Verify interface connection: `interface.set_controller(controller)` called
3. Test callback: Add debug output in `execute_mcp_action()`
4. Verify tools mapping: Check `chain.tools_mapping` contains expected tools

#### 11. Architecture Maintenance Guidelines

**Code Change Checklist**:
- [ ] If modifying mouse tracking logic, update **both** event loops (lines 796-815 AND 1055-1074)
- [ ] If changing state variables, update **both** state detection blocks
- [ ] If adding debug output, add to **both** locations for consistency
- [ ] Test **both** pygame and MCP modes after any mouse tracking changes
- [ ] Search for `hasattr()` usage when adding new state variables - use `getattr()` instead

**Testing Protocol**:
1. **First Drag Test**: Verify drag detection and command execution work
2. **Second Drag Test**: Verify state resets properly and second drag works identically
3. **Cross-Mode Test**: Verify pygame and MCP modes behave identically
4. **State Persistence Test**: Verify states reset properly between drag sessions
5. **Error Recovery Test**: Verify system recovers from interrupted drags

**Future Architecture Improvements**:
1. **Consolidate Event Loops**: Eliminate code duplication by using single event handler
2. **State Management Class**: Centralize mouse tracking state in dedicated class
3. **Automated Testing**: Add unit tests for state transitions and cross-mode consistency
4. **Event System**: Replace direct method calls with event-driven architecture

**Critical Files to Monitor**:
- `controller_base.py` lines 796-815 (pygame event loop mouse tracking)
- `controller_base.py` lines 1055-1074 (async event loop mouse tracking)  
- `look_path.py` lines 252-272 (start/stop mouse tracking methods)
- `look_path.py` lines 22-27 (movement filtering logic)
- `interface.py` lines 93-96 (MCP executor setup)

## Real-World Debugging Example: Mode Inconsistency Analysis

**Issue**: Same mouse gesture produces different camera behavior in pygame vs MCP mode.

**Debug Output Comparison** (identical mouse gesture):

**Pygame Mode Results**:
```
🖱️ Started drag operation - accumulating movements
Sent command: {'type': 'look', 'movementX': -8, 'movementY': 0}
Sent command: {'type': 'look', 'movementX': -14, 'movementY': 0}
[... 25 total commands sent in real-time ...]
📊 Drag analysis (drag_complete):
   🎯 Camera rotation: -126.4°, -5.2°
   ⚠️  No execution callback set - command not executed
```

**MCP Mode Results**:
```
🖱️ Started drag operation - accumulating movements
[... no individual commands during drag ...]
🖱️ Drag completed (1.0s) - executing command
📊 Drag analysis (drag_complete):
   🎯 Camera rotation: -148.4°, -0.8°
   ✅ Executing MCP command
🎮 Executing: lookAngle({'xAngle': -148.4, 'yAngle': -0.8, 'speed': 'normal'})
```

**Key Finding**: The **angle calculation is working correctly** (only ~22° difference between modes, which is acceptable). 

**Real Root Cause**: **Execution Model Mismatch**
- **Pygame Mode**: Sends **25 individual real-time commands** during drag (`movementX`/`movementY` deltas)
- **MCP Mode**: Accumulates movements, sends **1 batched command** at end (`lookAngle` with total degrees)

**Impact**: 
- Pygame = smooth, continuous camera control
- MCP = jerky, delayed camera control with same final result

**Conclusion**: The mouse tracking and angle accumulation systems are working correctly. The difference comes from **when** commands are executed (real-time vs batched), not **what** angles are calculated.

**Critical Realization**: This is **NOT a bug to fix** - it's the **intended architectural difference** between the two modes.

**Why the Difference is Intentional and Necessary**:

**Pygame Mode = Human Interface Optimization**:
- **Purpose**: Direct, continuous control for smooth human experience
- **Commands**: Raw pixel deltas (`movementX: -8, movementY: 0`)
- **Execution**: 25 micro-commands per drag = buttery smooth camera control
- **Goal**: Optimal human gameplay experience

**MCP Mode = AI Training Optimization**:
- **Purpose**: Discrete, meaningful actions for AI agent training
- **Commands**: Calculated spatial reasoning (`lookAngle: -148.4°, -0.8°`)  
- **Execution**: 1 intentional command per drag = trainable action unit
- **Goal**: High-quality training data for spatial reasoning

**Why We CANNOT "Fix" This by Making MCP Send Real-Time Commands**:

1. **❌ MCP Tool Flood**: 25 separate `lookAngle` tool calls per drag would overwhelm the system
2. **❌ Screenshot Spam**: 25 screenshot captures + processing per drag = performance death
3. **❌ Trajectory Pollution**: AI would learn micro-movements instead of spatial reasoning  
4. **❌ Training Data Ruined**: Message chains flooded with meaningless micro-actions
5. **❌ Research Goal Broken**: Defeats the purpose of teaching discrete spatial reasoning

**Final Determination**: The ~22° difference between modes is **acceptable tolerance** for two fundamentally different execution paradigms processing the same human input. The "inconsistency" in execution timing is actually **correct behavior** - pygame optimized for humans, MCP optimized for AI training.

**Architecture Decision**: Maintain the difference in execution models. Do not attempt to make execution timing identical.

## **SMART SOLUTION**: Auto-Detection Click Handling ✅

**Intelligent Web Client**: The web client now automatically detects context and routes clicks appropriately.

**How it Works**:
1. **Try UI interaction first**: Check if cursor is over a specific UI element (inventory, menus, etc.)
2. **Fall back to game world**: If no UI element detected, use `documentMouseEvent` for reliable world interactions

**Implementation**:
- **Both modes use `leftDown/leftUp` & `rightDown/rightUp`** for consistency
- **Web client smart routing**: `elementAtCursor !== document.body` → UI interaction, else → `documentMouseEvent`
- **Automatic context detection**: No manual context switching needed

**Result**: 
- ✅ **Inventory interactions work perfectly** in both modes
- ✅ **Game world interactions work reliably** in both modes  
- ✅ **Complete parity achieved** with intelligent auto-detection

**Benefits**: No complex hybrid logic in MCP tools, no mode-specific command differences - the web client handles everything automatically based on what's actually under the cursor.

## **SOLVED**: Angle Translation Inconsistency Bug Fixed ✅

**Previous Issue**: The same calculated angles produced different camera movement in Minecraft between pygame and MCP modes, causing a 22° difference for identical mouse input.

**Root Cause Identified**: The bug was in the `stepLook()` function in `minecraft-mcp-server.ts`. It used easing animation with cumulative rounding errors:
- **Pygame mode**: Sent 1 direct command `{"type": "look", "movementX": 200}`
- **MCP mode**: Sent ~20 small commands with easing, causing precision drift

**Solution Applied**: Modified `stepLook()` to use exact division instead of easing curves:
```typescript
// Before: Easing with rounding errors
const weight = progress - prev;
const dx = totalPixelX * weight;  // Accumulated errors

// After: Exact division 
const stepX = totalPixelX / steps;  // Perfect precision
const stepY = totalPixelY / steps;
```

**Result**: ✅ **Both modes now produce identical camera rotation** for identical mouse input while maintaining smooth AI movement.

**Architecture Decision Confirmed**: The execution model differences (real-time vs batched) are intentionally preserved:
- **Pygame mode**: Optimized for smooth human control
- **MCP mode**: Optimized for discrete AI training actions

The angle conversion inconsistency has been eliminated without changing the fundamental dual-mode architecture.

### Operating Modes

#### pygame Mode
- Direct human control via pygame interface
- WebSocket commands sent to Minecraft Web Client
- Real-time input processing and UI feedback
- Manual camera control with mouse drag

#### MCP Mode  
- AI-driven autonomous gameplay
- LLM generates tool calls through message chain
- Human demonstration capture for training
- Automatic look command generation from mouse movements

## Key Features

### 3D Visual SKETCHPAD Tool (Research Core)

The system provides a novel 3D spatial reasoning tool accessed via MCP integration:

**`annotate_3d_position(x, y, z, label, color)`**
- Places colored 3D markers at specific world coordinates
- Uses Three.js scene manipulation for visual annotations
- Enables spatial reasoning about object locations
- Example: `annotate_3d_position(120, 64, 180, "oak_tree", "green")`

**Research Significance**: This tool enables AI agents to reason about 3D space and mark important locations - skills that transfer to web agents, robotics, and other spatial reasoning domains.

### Advanced Camera Control
- **Drag-based look operations**: Mouse drag in camera area accumulates movements
- **Automatic angle calculation**: Converts pixel movements to degrees using configurable sensitivity
- **Smart command generation**: Only executes significant movements (>0.2 degrees)
- **Real-time analysis**: Live angle statistics and compass direction display

### Dual-Mode Architecture
- **Unified UI**: Same interface works for both human and AI control
- **Mode-specific command routing**: pygame commands vs MCP tool calls
- **Seamless switching**: Can switch between modes without restart

### MCP Integration Infrastructure
- **Command processing**: Handles MCP tool calls in real-time
- **Data structure support**: Foundation for PygameMCPAsyncMessageChain integration
- **Development focus**: Building core `annotate_3d_position` functionality
- **Future expansion**: Infrastructure ready for demonstration recording

### Comprehensive Input Handling
- **Multi-input support**: Mouse, keyboard, and virtual controls
- **Hotbar management**: Visual slot selection with state tracking
- **Action buttons**: All essential Minecraft controls (jump, sneak, sprint, inventory, etc.)
- **Movement controls**: Both virtual joystick and WASD keyboard input

## Configuration

### Server Configuration (`servers_config.json`)
```json
{
"mcpServers": {
    "minecraft-controller_stdio": {
    "command": "npx",
    "args": ["tsx", "/path/to/minecraft-mcp-server.ts", "--transport", "stdio"],
    "env": {"NODE_NO_WARNINGS": "1"}
    }
}
}
```

### Constants (`constants.py`)
- Window dimensions: 1600x900
- FPS: 60
- Custom pygame events for MCP integration
- Color definitions for UI theming

## Usage

### Research Workflow (Data Collection)

**Complete setup for collecting spatial reasoning trajectories:**

1. **Start WebSocket server**:
```bash
# Terminal 1: Start the relay server
node server.js
```

2. **Start Minecraft MCP server**:
```bash
# Terminal 2: Start MCP tools server
npx tsx minecraft-mcp-server.ts --transport stdio
```

3. **Start pygame controller in MCP mode**:
```bash
# Terminal 3: Start demonstration interface
python -m mc_pygame_controller.controller --mcp --sensitivity 5.0
```

4. **Open Minecraft Web Client** in browser:
```
http://localhost:8080
```

**Current Development:**
- **Mouse drag in camera area**: Generates `lookAngle` commands automatically
- **UI buttons**: Generate appropriate MCP tool calls
- **Focus**: Implementing `annotate_3d_position` tool for 3D spatial annotations

### pygame Mode (Human Control)
```bash
python -m mc_pygame_controller.controller
```

### MCP Mode (AI-driven)
```bash
python -m mc_pygame_controller.controller --mcp --sensitivity 5.0
```

### Command Line Options
- `--mcp`: Enable MCP mode for AI control
- `--sensitivity`: Mouse sensitivity (pixels per degree, default: 5.0)

## Dependencies

- `pygame`: UI and input handling
- `websockets`: Communication with Minecraft Web Client
- `asyncio`: Asynchronous operation support
- `mcp`: Model Context Protocol client
- `openai`: AI conversation handling
- `httpx`: HTTP client for multimodal content
- `pydantic`: Data validation

## Integration Points

### WebSocket Relay Server (server.js)
- **Central hub** for all client communication on port 8081
- **Three-client architecture**: Routes messages between `bot`, `pygame`, and `mcp` clients
- **Message filtering**: Handles large screenshot data without logging spam
- **Connection management**: Automatic client registration and cleanup
- **HTTP server** on port 8080 serves Minecraft Web Client

### Minecraft Web Client Integration  
- **Three.js scene access**: Direct manipulation via `window.world.scene`
- **3D marker rendering**: Adds colored cubes for spatial annotations
- **Screenshot capture**: Returns base64-encoded images with game state
- **Command execution**: Receives WebSocket commands and updates game world
- **Bot registration**: Connects as `bot` client to relay server

### MCP Server Integration (minecraft-mcp-server.ts)
- **Tool discovery**: Dynamically loads available spatial reasoning tools
- **Command translation**: Converts MCP calls to WebSocket commands
- **Screenshot integration**: Captures visual feedback for each tool execution
- **Error handling**: Robust retry mechanisms and timeout management
- **Multi-modal responses**: Returns text + images for rich AI feedback

### AI Training Pipeline Integration
- **PygameMCPAsyncMessageChain format**: Native compatibility with training workflows  
- **Automatic serialization**: Screenshots base64-encoded, metadata preserved
- **Research development**: Building foundation for future data collection
- **Focus**: Core `annotate_3d_position` tool implementation

### Research Ecosystem
This controller is part of a complete research pipeline:
- **Data Collection** → mc_pygame_controller (this module)
- **Model Training** → OpenAI fine-tuning or local model SFT/GRPO
- **Evaluation** → Web agents, SWE-Bench, spatial reasoning benchmarks
- **Transfer Learning** → Apply 3D reasoning skills to other domains

This architecture provides a robust foundation for both human-controlled and AI-driven Minecraft gameplay, with comprehensive demonstration capture capabilities for training autonomous agents in 3D spatial reasoning.