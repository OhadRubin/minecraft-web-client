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