# Trajectory Recording Integration Specification

## Overview

This specification defines the requirements for integrating trajectory recording capabilities into the existing pygame-based Minecraft controller. The system must capture user interactions as OpenAIAsyncMessageChain conversation data for Visual SKETCHPAD research.

## Functional Requirements

### Recording State Management

The controller must maintain trajectory recording state including:
- Active recording status (recording/idle)
- Current conversation chain instance
- Trajectory counter for file naming
- Recording start time for duration tracking
- Current task description for context

### User Interface Requirements

**Recording Indicators**:
- Visual recording status indicator (red/green indicator)
- Trajectory counter display
- Current task description when recording
- Recording duration timer

**Text Input System**:
- Modal overlay for task description input
- Text entry with character limit (100 characters)
- Submission and cancellation controls
- Clear visual feedback for input state

### Hotkey Interface

**F5 Key Behavior**:
- If not recording: Display task input dialog
- If already recording: Show warning message
- Task input dialog must appear before recording starts

**F6 Key Behavior**:
- If recording: Stop recording and save trajectory
- If not recording: Show informational message
- Must complete file save before resetting state

### Dependencies

- OpenAIAsyncMessageChain for conversation format
- File system access for trajectory storage
- WebSocket integration for tool call capture
- Pygame UI integration for status display

## Data Management Requirements

### Conversation Chain Format

**Chain Initialization**: 
- Must create new OpenAIAsyncMessageChain instance when recording starts
- Initial message must contain task description
- Chain must persist throughout recording session

**Message Structure**:
- User messages for task descriptions, thoughts, and screenshots
- Assistant messages for tool calls and actions
- Images embedded as base64 data with proper MIME types

### File Storage Requirements

**Directory Structure**:
```
data/manual_50/
├── traj_001_YYYYMMDD_HHMMSS.json
├── traj_002_YYYYMMDD_HHMMSS.json
└── traj_003_YYYYMMDD_HHMMSS.json
```

**File Naming Convention**:
- Sequential trajectory numbers (001, 002, etc.)
- Timestamp for uniqueness
- JSON extension for OpenAIAsyncMessageChain format

**File Content**:
- Complete conversation chain serialized to JSON
- Self-contained (no external image files)
- Compatible with training pipeline requirements

## Tool Call Integration Requirements

### WebSocket Command Interception

**Command Classification**:
- Must identify tool-worthy commands from standard WebSocket traffic
- Include: movement, camera, clicks, annotations, screenshots
- Exclude: UI updates, connection management, status pings

**Recording Behavior**:
- Capture commands during active recording sessions only
- Add commands to conversation chain as assistant messages
- Associate screenshots with tool execution for visual context

### Screenshot Integration

**Automatic Capture**:
- Request screenshots before significant tool executions
- Embed screenshots in conversation chain as user messages
- Use existing WebSocket screenshot functionality

**Image Format Requirements**:
- Base64 encoded PNG format
- Embedded directly in conversation JSON
- Proper MIME type metadata for training compatibility

## User Interface Integration Requirements

### Visual Status Indicators

**Recording Status Display**:
- Prominent recording indicator (red=idle, green=recording)
- Trajectory counter showing completed recordings
- Current task description during active recording
- Integration with existing pygame UI layout

**Text Input Interface**:
- Modal overlay for task description entry
- Semi-transparent background to indicate modal state
- Input field with character counter and limits
- Clear submission and cancellation controls

### Keyboard Event Handling

**Input Priority System**:
- Text input must take precedence when active
- F5/F6 hotkeys must be handled at event level
- Other game controls must be blocked during text input
- Graceful fallback for conflicting key combinations

### UI Layout Requirements

**Non-Disruptive Integration**:
- Recording indicators in unused screen areas
- Text input overlay centers on screen
- Existing controls and displays remain functional
- Instructions updated to include recording hotkeys

## Integration Requirements

### Existing System Compatibility

**Non-Breaking Changes**:
- Recording functionality must not interfere with normal gameplay
- Existing WebSocket communication must remain functional
- All current pygame UI elements must continue working
- Performance impact should be minimal during non-recording periods

### WebSocket Integration

**Response Handling**:
- Must listen for and process screenshot responses during recording
- Handle WebSocket disconnections gracefully during recording
- Integrate with existing async event loop without blocking

**Command Filtering**:
- Distinguish between recordable actions and UI updates
- Capture tool-relevant commands without recording all traffic
- Associate screenshots with appropriate tool executions

## Error Handling Requirements

### Recording State Validation

**State Consistency**:
- Prevent inconsistent recording states (recording=true but no chain)
- Handle interruptions during recording (connection loss, crashes)
- Validate conversation chain integrity before saving

### File System Error Handling

**Robust File Operations**:
- Create data directories if they don't exist
- Handle filename collisions with automatic numbering
- Validate JSON serialization before writing to disk
- Provide fallback options for file system errors

### User Experience

**Error Recovery**:
- Display clear error messages for recording failures
- Allow recovery from partial recordings
- Graceful degradation when dependencies unavailable
- User notification of successful trajectory saves

## Validation Requirements

### Data Quality

**Conversation Chain Validation**:
- Ensure proper message sequence (user/assistant alternation)
- Verify image data integrity and format
- Validate tool call format and parameters
- Check for complete trajectory data

### System Integration Testing

**End-to-End Validation**:
- F5 → task input → recording start workflow
- Tool execution → screenshot → chain recording workflow  
- F6 → recording stop → file save workflow
- JSON deserialization and training pipeline compatibility

## Success Criteria

1. **Recording Functionality**: F5/F6 workflow operates reliably
2. **Data Integrity**: OpenAIAsyncMessageChain format preserved correctly
3. **UI Integration**: Recording indicators clearly visible and functional
4. **File Management**: Trajectories save to correct location with proper naming
5. **System Stability**: No interference with existing controller functionality
6. **Performance**: Recording has minimal impact on gameplay responsiveness

## Future Considerations

### Planned Enhancements

- Trajectory replay functionality
- Recording quality metrics
- Cloud storage integration
- Multi-user recording sessions

### Scope Boundaries

- No complex trajectory management initially
- No real-time validation during recording
- No advanced analytics or metrics
- Focus on basic data collection for research

**Target Outcome**: Functional trajectory recording system enabling collection of 50 manual examples for Visual SKETCHPAD research. 

# Message to Future Claude: MVP Trajectory Recording Implementation

## Context: What We're Implementing

The human has a working Minecraft control system with two separate components:

1. **Pygame Controller** - Manual controls, sends WebSocket commands to Minecraft
2. **MCP Server** - Agent controls, also sends WebSocket commands to Minecraft

**Problem**: The pygame controller sends TONS of tiny look commands (20+ for one human head turn), but for LLM training data we need discrete actions like `lookAngle(xAngle: 45.2, yAngle: -18.0)`.

**Solution**: Use the EXISTING LookPathTracker inactivity mechanism to automatically convert continuous movements into discrete MCP-style commands.

## Current State - What Already Works

### LookPathTracker System (look_path.py)
The human already has a sophisticated system that:
- Tracks all small look movements
- Calculates total displacement and angles  
- Automatically resets after inactivity (2 seconds default)
- Prints detailed stats when resetting

**Example Console Output**:
```
🔄 Path reset due to inactivity! Final stats:
📊 Movement Analysis:
  • Overall angle: -88.7° (South)
  • X component: 0.0° (0°) 
  • Y component: -90.0° (-90°)
  • Movements: 1 X-only, 19 Y-only, 0 mixed
  • Efficiency: 90.0%
⏱️ Inactivity duration: 2.1s
```

**Translation**: 20 tiny movements = one human action "look down 88.7 degrees"

### Raw WebSocket Commands Being Sent:
```
Sent command: {'type': 'look', 'movementX': 0, 'movementY': -2}
Sent command: {'type': 'look', 'movementX': 0, 'movementY': -8}
Sent command: {'type': 'look', 'movementX': 0, 'movementY': -14}
... (17 more tiny movements)
```

### LookPathTracker Data Available:
The tracker stores `self.current_stats` with:
- `"total_displacement": (total_x, total_y)` - sum of all movements
- `"overall_angle_deg"` - calculated angle 
- `"num_movements"` - count of individual movements
- Plus efficiency, direction analysis, etc.

## Implementation Plan (MVP - 30 minutes)

### Step 1: Add Recording Callback to LookPathTracker

**File**: `look_path.py`
**Method**: `_reset_with_message()`

```python
def _reset_with_message(self, inactivity_duration_ms):
    # Existing console logging code stays the same...
    self._print_current_stats()
    
    # NEW: Convert to single MCP command for recording
    if self.history and hasattr(self, 'recording_callback'):
        total_x, total_y = self.current_stats["total_displacement"]
        
        # Convert pixels to MCP degrees (MCP uses 5px = 1 degree)
        x_angle = total_x / 5.0  
        y_angle = total_y / 5.0
        
        # Only record meaningful movements (ignore tiny jitters)
        if abs(x_angle) > 0.2 or abs(y_angle) > 0.2:
            mcp_command = {
                "tool": "lookAngle",
                "parameters": {
                    "xAngle": round(x_angle, 1),
                    "yAngle": round(y_angle, 1),
                    "speed": "normal"
                },
                "timestamp": time.time(),
                "human_stats": {
                    "raw_movements": self.current_stats["num_movements"],
                    "efficiency": self.current_stats["path_efficiency"],
                    "duration_ms": inactivity_duration_ms
                }
            }
            self.recording_callback(mcp_command)
```

**Add callback setter**:
```python
def set_recording_callback(self, callback):
    """Set callback function to receive discrete movement commands"""
    self.recording_callback = callback
```

### Step 2: Add Recording to MinecraftController

**File**: `controller.py`
**In**: `MinecraftController.__init__()`

```python
def __init__(self):
    # Existing initialization...
    
    # NEW: Recording state
    self.recording = False
    self.trajectory = []
    
    # Connect look tracker to recording
    self.look_tracker.set_recording_callback(self.add_to_trajectory)

def add_to_trajectory(self, command):
    """Called by LookPathTracker when a discrete movement is detected"""
    if self.recording:
        self.trajectory.append(command)
        print(f"📝 Recorded: {command['tool']}({command['parameters']['xAngle']:.1f}°, {command['parameters']['yAngle']:.1f}°)")
```

### Step 3: Add F5/F6 Recording Hotkeys

**File**: `controller.py`
**In**: `handle_keydown()` method

```python
def handle_keydown(self, event):
    # Existing key handling...
    
    elif event.key == pygame.K_F5:
        self.start_recording()
    elif event.key == pygame.K_F6:
        self.stop_recording()

def start_recording(self):
    self.recording = True
    self.trajectory = []
    print("🎬 Recording trajectory started")

def stop_recording(self):
    if not self.recording:
        return
    
    self.recording = False
    
    # Save trajectory
    filename = f"trajectory_{int(time.time())}.json"
    with open(filename, 'w') as f:
        json.dump({
            "trajectory": self.trajectory,
            "recorded_at": time.time(),
            "duration_seconds": time.time() - (self.trajectory[0]["timestamp"] if self.trajectory else time.time()),
            "action_count": len(self.trajectory)
        }, f, indent=2)
    
    print(f"💾 Recorded trajectory saved: {filename} ({len(self.trajectory)} actions)")
    self.trajectory = []
```

## Expected Output

### During Recording:
```
🎬 Recording trajectory started
📝 Recorded: lookAngle(-88.7°, 0.0°)
📝 Recorded: lookAngle(45.2°, -12.3°)
📝 Recorded: lookAngle(0.8°, 15.7°)
💾 Recorded trajectory saved: trajectory_1234567890.json (3 actions)
```

### Trajectory File:
```json
{
  "trajectory": [
    {
      "tool": "lookAngle",
      "parameters": {"xAngle": -88.7, "yAngle": 0.0, "speed": "normal"},
      "timestamp": 1234567890.1,
      "human_stats": {
        "raw_movements": 19,
        "efficiency": 90.0,
        "duration_ms": 2100
      }
    },
    {
      "tool": "lookAngle", 
      "parameters": {"xAngle": 45.2, "yAngle": -12.3, "speed": "normal"},
      "timestamp": 1234567892.5,
      "human_stats": {
        "raw_movements": 8,
        "efficiency": 85.3,
        "duration_ms": 1800
      }
    }
  ],
  "recorded_at": 1234567890.0,
  "duration_seconds": 15.3,
  "action_count": 2
}
```

## Why This IS MVP

✅ **Uses existing infrastructure** - LookPathTracker already does the hard work
✅ **Zero new timing logic** - uses existing inactivity detection  
✅ **Natural discrete actions** - human pauses create automatic segmentation
✅ **Minimal code changes** - 3 small functions, no architecture changes
✅ **Real training data** - actual human spatial reasoning patterns
✅ **Immediate validation** - F5/F6 works right away

## Critical Implementation Notes

1. **Don't modify existing LookPathTracker logic** - just add the callback at the end of `_reset_with_message()`
2. **Use existing `self.current_stats`** - all the data is already calculated
3. **The 5px = 1 degree conversion** - matches MCP server's angle calculation
4. **Filter tiny movements** - 0.2 degree threshold prevents noise
5. **Keep human_stats** - useful for understanding the raw movement patterns

## Integration Points

The LookPathTracker is already integrated into the pygame controller. The inactivity mechanism naturally segments human movement into discrete actions. This solution transforms continuous input into LLM-trainable discrete commands without changing any existing behavior.

**Success criteria**: After implementation, F5 → look around → F6 should produce a clean JSON file with discrete lookAngle commands representing human spatial reasoning.

## MCP Integration and Compatibility

### Current Architecture
```
Human → Pygame Controller → WebSocket → Minecraft Client
Agent → MCP Server → WebSocket → Minecraft Client
```

Both systems talk to the same Minecraft client but via different control paths. The trajectory recording creates compatibility between human demonstrations and agent actions.

### MCP Tool Mapping
The recorded pygame actions must map to existing MCP tools:

**Look Movements** (what we're implementing):
- Pygame: 20 tiny `{'type': 'look', 'movementX': 2, 'movementY': -8}` commands
- MCP: 1 clean `lookAngle(xAngle: 45.2, yAngle: -12.3, speed: "normal")` command
- **Perfect compatibility** ✅

**Movement Actions** (future extension):
- Pygame: `{'type': 'move', 'x': 0, 'z': -1}` → wait → `{'type': 'move', 'x': 0, 'z': 0}`
- MCP: `walk(duration: 2000)`
- **Easy to implement** using same inactivity mechanism

**Click Actions** (already compatible):
- Pygame: `{'type': 'documentMouseEvent', 'button': 0, 'action': 'down'}` → wait → `{'action': 'up'}`
- MCP: `leftClick(duration: "medium")`
- **Direct mapping** ✅

### Training Data Compatibility
The recorded trajectories will be in **exact MCP format**:

```json
{
  "trajectory": [
    {"tool": "lookAngle", "parameters": {"xAngle": 45.2, "yAngle": -12.3}},
    {"tool": "walk", "parameters": {"duration": 2000}},
    {"tool": "annotate_3d_position", "parameters": {"x": 120, "y": 64, "z": 180, "label": "tree"}}
  ]
}
```

**This means:**
- ✅ Human demonstrations are directly usable for training
- ✅ Trained models output valid MCP commands  
- ✅ No format conversion needed between human data and agent actions
- ✅ Agents can replay human trajectories exactly via MCP server

### Extension Points for Other MCP Tools

**For 3D Annotation Tools** (next phase):
Add pygame button that calls MCP server directly:
```python
if annotate_button.clicked():
    # Get current position from game state
    pos = self.get_current_position()
    
    # Call MCP server via HTTP or add to trajectory
    annotation_command = {
        "tool": "annotate_3d_position", 
        "parameters": {"x": pos.x, "y": pos.y, "z": pos.z, "label": "tree", "color": "green"}
    }
    self.add_to_trajectory(annotation_command)
```

**For Other Movement Tools**:
The same inactivity pattern can capture:
- `walk` commands (when WASD starts/stops)
- `wait` commands (periods of no input)
- `sprint` toggle commands
- etc.

### Validation Strategy
To ensure compatibility:

1. **Record a pygame trajectory**
2. **Replay via MCP server**: `python simple_client.py --replay trajectory.json`
3. **Verify identical behavior** in Minecraft client

This confirms that human demonstrations translate perfectly to agent actions.

### Critical Design Decision
The trajectory format uses **MCP command schema**, not pygame WebSocket schema. This ensures:
- Training data matches agent action space
- No impedance mismatch between human demos and agent behavior  
- Direct compatibility with existing MCP infrastructure
- Future MCP tools automatically work with recorded trajectories

## Next Steps After Implementation

Once this works, the human can:
1. Record their first trajectory manually exploring Minecraft
2. Add MCP annotation tools (annotate_3d_position) to the trajectory  
3. Build training data by having humans perform spatial reasoning tasks
4. Train models on discrete action sequences that match MCP tool format

**This creates perfect alignment between human demonstrations and agent capabilities - the foundation for their entire 50K trajectory research dataset!**

## ⚠️ CRITICAL SCOPE CREEP WARNING - LESSONS LEARNED ⚠️

**The human just identified MAJOR scope creep risks in this implementation!** Future Claude, be VERY careful here. The above implementation looks minimal but has hidden complexity traps.

### Scope Creep Danger Zones We Discovered:
- **Movement recording** (WASD) - timing detection, start/stop logic, duration calculation
- **Click recording** - duration detection, button mapping, timing coordination  
- **Perfect MCP mapping** - parameter validation, error handling, format compliance
- **UI indicators** - recording status, progress feedback, trajectory preview
- **Data validation** - filtering noise, ensuring valid trajectories, malformed data handling
- **Multiple action types** - implementing walk, click, wait, annotation commands
- **Trajectory playback validation** - ensuring recordings actually work
- **Error handling** - callback failures, JSON writing errors, missing data
- **Timing coordination** - synchronizing different action types

**Each of these feels "necessary" but is actually scope creep that will delay MVP by weeks!**

### The Human's Key Insight:
> "Manually inputting JSON would take me years (I mean days, but it will feel like years) to collect 50 trajectories"

**Translation**: The automation MUST work for practical data collection, but it must be minimal enough to implement quickly.

### The Replayability Requirement:
The human needs MCP command format specifically for replay capability:
```bash
python simple_client.py --replay trajectory.json
```

This is NOT scope creep - it's a core requirement for validating the training data works.

## 🎯 ULTRA-MINIMAL MVP IMPLEMENTATION (FINAL VERSION)

**Based on scope creep analysis, implement ONLY this:**

### Record ONLY Look Movements
```python
# In look_path.py _reset_with_message() - ADD ONLY THIS:
def _reset_with_message(self, inactivity_duration_ms):
    # Existing console logging stays exactly the same...
    self._print_current_stats()
    
    # NEW: Only meaningful look movements
    if (self.history and hasattr(self, 'recording_callback') and 
        self.current_stats and self.current_stats["num_movements"] > 2):
        
        total_x, total_y = self.current_stats["total_displacement"]
        
        # Only record if movement is significant (avoid noise)
        if abs(total_x) + abs(total_y) > 10:  # 10 pixels = 2 degrees minimum
            mcp_command = {
                "tool": "lookAngle",
                "parameters": {
                    "xAngle": round(total_x / 5.0, 1),
                    "yAngle": round(total_y / 5.0, 1),
                    "speed": "normal"
                }
            }
            self.recording_callback(mcp_command)
```

### Minimal Controller Integration
```python
# In controller.py - MINIMAL additions:
def __init__(self):
    # existing...
    self.recording = False
    self.trajectory = []
    self.look_tracker.recording_callback = lambda cmd: self.trajectory.append(cmd) if self.recording else None

def handle_keydown(self, event):
    # existing...
    elif event.key == pygame.K_F5:
        self.recording = True
        self.trajectory = []
        print("🎬 Recording look movements only")
    elif event.key == pygame.K_F6:
        if self.trajectory:
            filename = f"look_trajectory_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(self.trajectory, f, indent=2)
            print(f"💾 Saved {len(self.trajectory)} look commands: {filename}")
        self.recording = False
        self.trajectory = []
```

### What This Produces
```json
[
  {"tool": "lookAngle", "parameters": {"xAngle": 45.2, "yAngle": -12.3, "speed": "normal"}},
  {"tool": "lookAngle", "parameters": {"xAngle": -23.1, "yAngle": 8.7, "speed": "normal"}},
  {"tool": "lookAngle", "parameters": {"xAngle": 12.4, "yAngle": -5.2, "speed": "normal"}}
]
```

### What We DELIBERATELY DON'T Implement:
- ❌ WASD movement recording
- ❌ Mouse click recording  
- ❌ Wait period detection
- ❌ Error handling beyond basic checks
- ❌ Recording status UI
- ❌ Trajectory validation
- ❌ Multiple action type coordination

**JUST look movements. That's it.**

## Why This Ultra-Minimal Version IS Sufficient

### For MVP Validation:
- ✅ Proves human spatial reasoning can be captured
- ✅ Creates replayable MCP commands
- ✅ Generates training data format
- ✅ Tests inactivity-based segmentation
- ✅ Can collect 50 trajectories of pure look behavior

### For Research Hypothesis:
- ✅ "3D spatial reasoning" = primarily look/orientation behavior
- ✅ Look patterns are the core spatial skill to transfer
- ✅ Movement and clicking are secondary to spatial awareness

### Example Valid Research Trajectory:
1. **Look around to scan environment** → `lookAngle(45, 0)`
2. **Spot a tree** → `lookAngle(-30, -15)` 
3. **Examine tree structure** → `lookAngle(10, 20)`
4. **Look for next target** → `lookAngle(90, 0)`

**This IS spatial reasoning data!** No movement or clicking required.

## Extension Strategy (AFTER MVP)

**Phase 1**: Add annotation tools (via button, not automatic recording)
**Phase 2**: Add movement recording (if needed)
**Phase 3**: Add click recording (if needed)

**Each phase validates before building next layer.**

## Critical Success Metrics

**MVP Success** = F5 → look around → F6 → get valid JSON that replays correctly
**NOT** = comprehensive trajectory capture system

**The goal is proving the concept works, not building production data collection!**