# Cross Mode Movement & Camera Validation

This document explains the new tests added to check how movement and camera commands behave when sent through the WebSocket path compared to the MCP conversion path.

## Cross Mode Simulation Test

`run_cross_mode_sequence` (see `simulate_cross_mode_ws.py`) feeds a short sequence of user actions through a dummy WebSocket server. The WebSocket messages retain the original direction vectors, but the MCP tool calls only contain a `duration` parameter:

```python
sequence = [
    {"type": "move", "x": 1.0, "z": 0.0},
    {"type": "look", "movementX": 40, "movementY": 0},
]
messages, conversions = await run_cross_mode_sequence(sequence)
```

The collected messages are:

```json
{"type": "move", "x": 1.0, "z": 0.0}
{"type": "look", "movementX": 40, "movementY": 0}
```

The MCP conversions become:

```json
{"tool": "walk", "parameters": {"duration": 2000}}
{"tool": "lookAngle", "parameters": {"xAngle": 8.0, "yAngle": 0.0, "speed": "normal"}}
```

Because the direction vector is lost in the MCP command, the two modes cannot be guaranteed to move the player the same way. The look command is converted consistently but still relies on the hard coded `SENSITIVITY = 5.0` constant.

## Environment Comparison Test

`test_cross_mode_environment_difference` sends the same actions to two stub environments. The WebSocket path moves the environment by applying the `(x, z)` offsets directly, while the MCP path executes the converted tool calls. After the sequence, the WebSocket environment has moved to `(1.0, 0.0)` while the MCP environment remains at `(0.0, 0.0)` due to missing direction data. This confirms the consistency gap.

## What Remains Unproven

These tests demonstrate that our internal conversion logic is consistent but they do **not** prove the Minecraft client reacts the same way. To fully confirm cross mode consistency we would need integration tests that:

1. Record real game state via `getBotStatus` before and after each action.
2. Send the WebSocket command and the equivalent MCP command.
3. Compare the actual position and rotation changes reported by the game.

Until those integration tests exist, the unit tests only show that direction data is discarded and that the sensitivity constant is applied consistently in code.
