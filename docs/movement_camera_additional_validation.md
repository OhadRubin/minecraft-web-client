# Additional Movement & Camera Validation

This follow-up document explains the new tests added after feedback on the initial validation report.

## New Tests

### Extended Camera Sensitivity Checks
`test_camera_sensitivity_signed` verifies that negative and vertical mouse deltas are converted using the same `SENSITIVITY = 5.0` constant.  By checking all sign combinations, it confirms our conversion logic is symmetric:

```python
scaled_x = dx * 2
scaled_y = dy * 2
converted = ActionConverter.convert_pygame_action({
    "type": "look", "movementX": scaled_x, "movementY": scaled_y
})
expected = {
    "tool": "lookAngle",
    "parameters": {
        "xAngle": round(scaled_x / 5.0, 1),
        "yAngle": round(-scaled_y / 5.0, 1),
        "speed": "normal",
    },
}
assert converted == expected
```

### LookPath Drift Check
`test_look_path_tracker_multiple_drags` performs two separate drag sequences and ensures the final yaw/pitch match the sum of both drags.  This confirms that `LookPathTracker` resets correctly between drags and does not accumulate unwanted drift.

## Do These Tests Prove Consistency?

The extended tests strengthen confidence that our conversion functions behave as expected.  They show that:

- Camera sensitivity math applies equally to positive and negative deltas.
- `LookPathTracker` produces the correct cumulative angles across multiple drags.

However, they still operate on stubs.  Without comparing to real `getBotStatus` values we cannot guarantee the game reacts the same way.  To fully confirm consistency we would need integration tests that:

1. Capture actual yaw and pitch from the running game before and after executing the same drag sequences.
2. Compare the measured change against the tracker’s predicted change.
3. Validate that MCP commands produce the same in-game movement as WebSocket commands.

Until such integration tests exist, our unit tests demonstrate logical correctness but not full end-to-end accuracy.
