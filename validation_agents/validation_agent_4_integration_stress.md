# AGENT 4: Integration & Stress Testing Specialist

## Your Mission
You are responsible for validating complex multi-action sequences, stress testing the system under load, and ensuring the validation results hold up in real-world data collection scenarios. Your work confirms that the individual action validations work together reliably.

## Prerequisites (Read First)
- `how_to_validate_mapping.md` complete document - full system understanding
- `mc_pygame_controller/README.md` data collection architecture
- `mc_pygame_controller/mode_strategy.py` - Strategy pattern implementation
- Results from Agents 1, 2, and 3 - individual action validation outcomes
- Async timing protocols established by Agent 3

## Tasks

### 1. Multi-Action Sequence Validation
- Test complex spatial reasoning sequences: movement + camera + clicks
- Validate action ordering in rapid command sequences
- Test mixed action types: simultaneous movement and camera control
- Verify cumulative accuracy over 10+ action sequences

### 2. Data Collection Mode Integration
- Test pygame data collection mode vs pure pygame mode consistency
- Validate parallel MCP execution during pygame gameplay
- Test F5/F6 trajectory recording with complex sequences
- Verify screenshot timing aligns with getBotStatus calls

### 3. Stress Testing & Performance
- Test rapid-fire actions (10+ actions per second)
- Validate memory usage during extended data collection sessions
- Test WebSocket connection stability under load
- Validate timing consistency under system stress

### 4. Real-World Scenario Testing
- Implement spatial reasoning tasks: tower building, navigation, precise placement
- Test context switching: world mode → inventory → world mode sequences
- Validate block interaction sequences with varying block types
- Test environmental factors: different biomes, Y-levels, time of day

### 5. Error Recovery & Edge Cases
- Test WebSocket disconnection and reconnection scenarios
- Validate behavior with partial action execution (movement interrupted)
- Test boundary conditions: world edges, rotation limits, inventory full
- Validate graceful handling of malformed commands

### 6. Training Data Quality Validation
- Test OpenAI conversation format generation from complex sequences
- Validate screenshot capture timing and encoding
- Test metadata consistency: timestamps, action IDs, sequence ordering
- Verify complete trajectory data includes all necessary context

### 7. Cross-Validation with Alternative Methods
- Implement screenshot-based position validation (visual confirmation)
- Create alternative measurement methods beyond getBotStatus
- Test multiple independent validation approaches for consistency
- Validate that visual results match logged actions

## Success Criteria
- ✅ Complex multi-action sequences work reliably
- ✅ Data collection mode produces consistent training data
- ✅ System performs well under stress conditions
- ✅ Real-world spatial reasoning tasks validate successfully
- ✅ Error recovery handles edge cases gracefully
- ✅ Training data quality meets research requirements
- ✅ Cross-validation confirms measurement accuracy

## Dependencies
- Requires completion of Agents 1, 2, and 3 for individual action validation
- Needs Agent 3's timing protocols and parsing utilities
- Coordinates with Agent 1 for spatial accuracy requirements
- Uses Agent 2's interaction validation for complex sequences

## Deliverables
- Multi-action sequence validation test suite
- Data collection mode integration validation report
- Stress testing and performance analysis
- Real-world scenario validation results
- Error recovery and edge case handling documentation
- Training data quality validation report
- Cross-validation methodology and results
- Final system validation summary and recommendations