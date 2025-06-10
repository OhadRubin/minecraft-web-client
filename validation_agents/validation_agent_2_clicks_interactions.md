# AGENT 2: Click & Interaction Validation Specialist

## Your Mission
You are responsible for validating all click actions, button presses, and game interactions. Your work ensures that timed actions (left/right clicks, jump) and toggle actions (sneak, sprint) are accurately converted and that duration calculations are consistent between pygame and MCP modes.

## Prerequisites (Read First)
- `mc_pygame_controller/README.md` - System architecture overview
- `mc_pygame_controller/action_handler.py` lines 190-291 - Click and interaction handling
- `mc_pygame_controller/action_converter.py` lines 99-106, 274-303 - Click/interaction conversion
- `how_to_validate_mapping.md` action mapping table for medium/low risk actions
- `mc_pygame_controller/action_handler.py` lines 84-103 - Duration calculation logic

## Tasks

### 1. Click Duration Mapping Validation
- Test left/right click duration calculations from pygame button holds
- Validate `_calculate_duration()` logic against actual button press times
- Test all duration categories: very_short, short, medium, long, very_long, very_very_long
- Verify WebSocket `leftDown`/`leftUp` vs MCP `leftClick` with duration parameter

### 2. Timed Action Consistency (Jump)
- Test jump button holds vs space key presses
- Validate that pygame `{"type": "control", "control": "jump", "state": true/false}` converts correctly
- Test duration vs state inconsistency in WebSocket vs MCP formats
- Verify Y-coordinate changes match expected jump behavior

### 3. Toggle Action Validation (Sneak/Sprint)
- Test sneak and sprint toggle states in both pygame and MCP modes
- Validate that toggle state is preserved correctly in conversion
- Test rapid toggle sequences for state synchronization
- Verify WebSocket control states match MCP parameter states

### 4. Inventory & Hotbar Interactions
- Test inventory toggle (E key) in both world and inventory contexts
- Validate hotbar slot selection (1-9 keys) with precise slot mapping
- Test drop item (Q key) and swap hands (F key) actions
- Verify context-dependent behavior consistency

### 5. Action Timing & State Validation
- Implement async timing validation for click actions (150ms completion)
- Test that block interaction state changes are captured by getBotStatus
- Validate inventory context changes are detected properly
- Test rapid click sequences for proper ordering

## Success Criteria
- ✅ Click duration calculations validated across all time ranges
- ✅ Timed vs toggle action inconsistencies documented and measured
- ✅ All simple actions (inventory, hotbar, drop, swap) working correctly
- ✅ Context-dependent behavior validated for world vs inventory modes
- ✅ Async timing working for all interaction types

## Dependencies
- Need Agent 3's getBotStatus parsing for block interaction detection
- Will coordinate with Agent 1 on overall timing protocol
- Need Agent 4's integration testing for complex action sequences

## Deliverables
- Duration calculation validation report
- Toggle vs timed action consistency analysis
- Complete test suite for all click and interaction actions
- Context-dependent behavior validation results
- Async timing validation for interactions