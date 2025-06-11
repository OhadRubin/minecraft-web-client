# Interaction Consistency Validation

This document summarizes how the new unit tests relate to the known consistency issues between pygame and MCP modes.

## What Was Tested

- **Duration Mapping** – `test_action_handler.py::test_calculate_duration_ranges` verifies that `_calculate_duration()` produces the expected category for a range of press times. This ensures the handler uses a deterministic mapping for converting raw press durations into the `very_short`…`very_very_long` labels.
- **Timed vs Toggle Actions** – `test_action_handler.py::test_left_click_action_short_duration` and `test_action_handler.py::test_toggle_actions` confirm that timed actions (left click) and toggle actions (sneak, sprint) correctly update the internal state and invoke the strategy with the proper parameters.
- **Simple Interactions** – `test_action_handler.py::test_simple_actions` checks that hotbar and inventory commands are passed through without alteration.
- **Action Conversion** – `test_action_converter.py` ensures that basic pygame commands and legacy string actions convert to the expected MCP tool calls.

These tests show that, inside the Python modules, clicks and interactions are translated consistently.

## Remaining Gaps

The tests do **not** verify the full pygame→WebSocket→MCP pipeline or the behavior inside Minecraft. They run in isolation with dummy strategies, so they cannot detect issues like the inventory interaction bug documented in `docs/inventory-interaction-debug-guide.md`.

To fully confirm or disprove the cross‑mode consistency problem we previously observed, additional integration tests are needed:

1. **WebSocket Command Capture** – Run both modes while sending identical input and record the exact WebSocket commands produced. Compare them for differences in structure (`leftDown` vs `documentMouseEvent`) and timing.
2. **Minecraft State Validation** – Use a headless Minecraft client or a mock server to execute the commands and query `getBotStatus` afterward. Ensure that item pickup, hotbar selection, and camera rotations match in both modes.
3. **Real Duration Measurement** – Instrument the UI so that actual press times are captured and verify that the resulting MCP durations (`short`, `long`, etc.) correspond to those times.

Until such end‑to‑end tests are in place, the unit tests only demonstrate that our conversion logic behaves consistently on its own—they cannot conclusively prove that the real client sees the same behavior.
