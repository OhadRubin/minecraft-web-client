# AGENT 1: Movement & Camera Validation Specialist

## Your Mission
You are responsible for validating the most critical spatial reasoning actions: movement and camera controls. Your work ensures that the core 3D spatial data (position vectors and rotation angles) is accurately captured and converted between pygame and MCP formats.

## Prerequisites (Read First)
- `mc_pygame_controller/README.md` - Complete system architecture
- `mc_pygame_controller/action_handler.py` lines 161-188 - Movement and camera handling
- `mc_pygame_controller/action_converter.py` lines 59-96 - Movement/camera conversion logic
- `how_to_validate_mapping.md` sections on sensitivity and LookPath validation
- `mc_pygame_controller/look_path.py` - Camera tracking implementation

## Tasks

### 1. Movement Direction Consistency Validation
- Implement test for `{"type": "move", "x": 1.0, "z": 0.0}` → `{"tool": "walk", "parameters": {"duration": 1000}}`
- Verify that WebSocket preserves direction vectors but MCP loses them
- Test all 8 cardinal/diagonal directions with precise coordinate validation
- Document the fundamental spatial data loss issue

### 2. Camera Sensitivity Calibration  
- Implement the pixel-to-degree calibration test from validation document
- Test controlled mouse movements (10px, 25px, 50px, 100px) in all directions
- Validate that `SENSITIVITY = 5.0` constant produces correct angle conversions
- Measure and document any systematic rotation errors

### 3. LookPath Tracker Validation
- Test that `look_path_tracker` calculations match `getBotStatus` results
- Implement the camera drag validation test with multiple movement sequences
- Verify cumulative angle calculations don't drift over time
- Validate the special execution path for camera actions

### 4. Async Timing for Movement/Camera
- Implement action completion detection for movement (200ms) and camera (100ms)
- Test state stability validation for position and rotation changes
- Validate that getBotStatus captures state AFTER actions complete
- Test rapid movement+camera sequences for race conditions

## Success Criteria
- ✅ Movement direction loss documented with precise measurements
- ✅ Camera sensitivity constant validated or corrected
- ✅ LookPath calculations confirmed accurate vs getBotStatus
- ✅ Async timing protocol working for spatial actions
- ✅ Complete test suite for movement and camera validation

## Dependencies
- Need Agent 3 to complete getBotStatus parsing utilities
- Will provide spatial accuracy requirements to Agent 2 for click validation
- Must coordinate timing protocols with all other agents

## Deliverables
- Detailed test results showing movement direction preservation/loss
- Sensitivity calibration report with recommended constants
- LookPath validation test suite
- Async timing validation for spatial actions