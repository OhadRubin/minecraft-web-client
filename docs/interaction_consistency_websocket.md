# Interaction Consistency – WebSocket Validation

This document summarises the latest tests and the included WebSocket simulation script.
It clarifies how these additions help confirm or disprove the original cross‑mode
consistency issue between pygame and MCP modes.

## New Unit Tests

- **Jump Long Duration** – `test_jump_action_long_duration` holds the jump
  action for over three seconds and verifies it is categorised as a `long`
  duration.
- **Movement Thresholds** – `test_handle_movement_threshold` checks that small
  joystick movements are ignored and larger deltas dispatch movement commands.
- **Camera Drag Tracking** – `test_camera_drag_tracking_respects_active` ensures
  camera look movements are only recorded when mouse drag tracking is active.
- **WebSocket Cross Mode** – `test_ws_cross_mode_consistency` spins up a simple
  relay server and asserts that identical input sequences from `pygame` and `mcp`
  clients produce the same messages for the bot receiver.

These tests extend the existing coverage so that timed actions, movement
filters and WebSocket dispatch behaviour are all validated.

## WebSocket Simulation Code

The new script `scripts/ws_cross_mode_simulation.py` runs a lightweight
WebSocket relay and sends the same commands from both client types. It prints the
resulting message sequences so developers can quickly spot differences.
Running this alongside the unit tests offers a small integration check without
launching the full server stack.

## Confirmation Status

These additions further confirm that our Python logic treats pygame and MCP modes
consistently for the covered scenarios. The WebSocket simulation shows that
basic command sequences look identical at the protocol level. However, the tests
still mock the game world, so they cannot prove that real Minecraft state changes
are identical. To fully disprove the inconsistency we observed earlier, we would
need end‑to‑end tests that:

1. Capture the actual WebSocket traffic of the full server while executing
   complex interactions.
2. Query `getBotStatus` in each mode to compare inventory state, player
   position and camera angles.
3. Measure real input durations from the UI and verify the resulting MCP
   parameters.

Until then, the new tests and simulation script provide additional confidence
but do not completely rule out subtle differences.
