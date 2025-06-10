# AGENT 3: getBotStatus Parsing & Ground Truth Specialist

## Your Mission
You are responsible for creating bulletproof getBotStatus parsing and validation utilities. Your work provides the "ground truth" foundation that all other validation depends on. You must ensure getBotStatus accurately captures game state and create robust parsing for positions, rotations, and context.

## Prerequisites (Read First)
- `how_to_validate_mapping.md` getBotStatus validation protocol section
- `minecraft-mcp-server.ts` - getBotStatus implementation
- `how_to_validate_mapping.md` getBotStatus output format example (line 550)
- `mc_pygame_controller/controller_base.py` lines 542-558 - getBotStatus usage examples
- Async timing validation section for state stability requirements

## Tasks

### 1. getBotStatus Parser Implementation
- Create robust parsing for position coordinates: `Position: (30, 63, -18)`
- Implement rotation parsing for yaw/pitch: `facing East (-288.15°, -2.55°)`
- Parse biome, time, inventory state, and interaction context
- Handle edge cases: angle wraparound, coordinate precision, missing fields

### 2. State Stability Validation
- Implement `wait_for_state_stable()` function from validation document
- Test that getBotStatus returns consistent results (3 consecutive identical)
- Validate state settling times for different action types
- Create timing calibration for reliable state capture

### 3. Position & Rotation Accuracy Validation
- Implement coordinate system validation tests
- Test boundary conditions: world edges, Y-level variations, chunk boundaries
- Validate rotation wraparound handling (359° → 1°)
- Test precision limits: smallest detectable movement/rotation

### 4. Context State Detection
- Parse and validate inventory vs world context states
- Detect block interaction states and selected hotbar slots
- Validate UI state capture for modal detection
- Test context switching consistency

### 5. Ground Truth Establishment
- Create comprehensive getBotStatus accuracy validation suite
- Test that reported positions match actual movement commands
- Validate that reported rotations match camera commands
- Establish confidence intervals for measurement precision

### 6. Async Race Condition Prevention
- Implement action completion detection methods
- Create network latency handling for variable timing
- Test command queue ordering validation
- Provide reliable timing recommendations for all other agents

## Success Criteria
- ✅ Robust getBotStatus parser handling all output formats
- ✅ State stability validation working reliably
- ✅ Position/rotation accuracy confirmed within acceptable tolerances
- ✅ Context state detection working for all game modes
- ✅ Ground truth validation establishing measurement confidence
- ✅ Async timing utilities working for all action types

## Dependencies
- Independent work - provides foundation for other agents
- Must establish timing protocols before other agents can validate
- Will provide parsing utilities to Agents 1, 2, and 4

## Deliverables
- Complete getBotStatus parsing library with error handling
- State stability validation utilities
- Ground truth accuracy validation report
- Async timing calibration data and recommendations
- Coordinate system and precision validation results
- Context state detection utilities