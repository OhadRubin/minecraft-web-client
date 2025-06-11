## Sneak Toggle Tests
- [✅] Sneak ON generates {"state": true}
- [✅] Sneak OFF generates {"state": false}
- [✅] No duplicate actions for same state
- [N/A] Keyboard and button both work (unit test covers handler only)

## Sprint Toggle Tests
- [✅] Sprint ON generates {"state": true}
- [✅] Sprint OFF generates {"state": false}
- [✅] State tracking works correctly

## State Management Tests
- [✅] Multiple rapid toggles work correctly
- [N/A] States persist across other actions
- [N/A] No conflicts between sneak and sprint

## Integration Tests
- [N/A] Toggle + movement works correctly
- [N/A] Toggle + jumping works correctly
- [N/A] Toggle + clicking works correctly

Automated unit tests in `tests/test_toggle_actions.py` verify that the action handler only issues toggle actions when the state changes and records the correct state values.
