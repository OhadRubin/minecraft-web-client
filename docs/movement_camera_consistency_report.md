# Movement & Camera Consistency Validation

This document explains how the tests in `tests/test_movement_camera_validation.py` demonstrate the state of the movement and camera conversion pipeline.

## Movement Direction Loss

`test_movement_direction_loss` sends the same movement vector through both the `PygameModeStrategy` (WebSocket path) and the `MCPModeStrategy` (MCP conversion path). The WebSocket path forwards the original `(x, z)` direction while the MCP path emits a `walk` command with only a `duration` parameter.

```python
controller = DummyController()
strat = PygameModeStrategy(controller)
strat.handle_movement(x, z)
assert controller.sent_commands[-1] == {"type": "move", "x": x, "z": z}

controller = DummyController()
strat = MCPModeStrategy(controller)
strat.handle_movement(x, z)
assert controller.sent_commands[-1] == {
    "tool": "walk",
    "parameters": {"duration": 1000},
}
```

Because no direction data survives the MCP conversion, the test confirms the **direction vector is discarded**. The client receiving only a duration cannot reproduce the same movement, which matches the inconsistency described in `how_to_validate_mapping.md`.

## Camera Sensitivity Calibration

`test_camera_sensitivity_conversion` applies several pixel deltas and verifies that the converted MCP command uses `SENSITIVITY = 5.0` for pixel‑to‑degree conversion:

```python
scaled = delta * 2
action = {"type": "look", "movementX": scaled, "movementY": 0}
converted = ActionConverter.convert_pygame_action(action)
expected = {
    "tool": "lookAngle",
    "parameters": {"xAngle": round(scaled / 5.0, 1), "yAngle": 0.0, "speed": "normal"},
}
assert converted == expected
```

These checks ensure that camera deltas are scaled and divided consistently. However, they do not prove that 20 pixels actually results in a 4° rotation inside the game—only that our conversion math is internally consistent.

## LookPath Tracker Accuracy

`test_look_path_tracker_matches_environment` feeds a sequence of mouse movements into `LookPathTracker` and executes the resulting `lookAngle` command. The environment stub accumulates yaw and pitch, and the test verifies that the total rotation matches the tracker’s expectation.

```python
tracker.start_mouse_tracking()
for dx, dy in [(10, 0), (10, 0), (0, -5), (15, 0)]:
    tracker.add_movement(dx, dy)
tracker.stop_mouse_tracking()
...
status = asyncio.get_event_loop().run_until_complete(env.get_status())
assert round(status["yaw"], 1) == 7.0
assert round(status["pitch"], 1) == 1.0
```

This shows the tracker’s pixel‑to‑degree math is coherent with our conversion constant. But without real `getBotStatus` values we cannot confirm that the in‑game camera ends up at those angles.

## Async Timing Validation

`test_async_action_timing` ensures that movement and camera commands respect the expected timing (200 ms for movement, 100 ms for camera). It confirms that our async stubs behave correctly, but again does not validate timing against an actual running game.

```python
await env.walk(200)
assert time.time() - start >= 0.2
await env.look_angle(5.0, 0.0, delay_ms=100)
assert time.time() - start >= 0.3
```

## Do the Tests Prove Consistency?

The tests confirm the **conversion logic** in isolation but cannot fully prove in‑game consistency. Specifically:

- They show that movement direction is lost when converting to MCP format.
- They verify that our pixel‑to‑degree constant is applied consistently in the code.
- They validate LookPath tracking math against a stubbed environment.
- They check that async delays are respected by the stubs.

However, we still lack integration tests that compare WebSocket output, MCP commands, and actual game state via `getBotStatus`. To conclusively prove or disprove consistency we would need tests that:

1. **Record real game state** before and after sending a WebSocket command and the equivalent MCP command, verifying that both produce the same position/rotation changes.
2. **Capture actual yaw/pitch** returned by `getBotStatus` after controlled mouse movements to confirm the sensitivity constant matches the game’s behavior.
3. **Measure movement timing** in a live environment to ensure actions complete within the expected windows.

Until those integration tests exist, these unit tests only demonstrate the internal logic—not the external consistency with Minecraft itself.
