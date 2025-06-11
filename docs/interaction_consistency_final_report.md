# Interaction Consistency – Final Checks

This note documents the last set of unit tests written for validating click and interaction handling.
It also explains how these tests relate to the original cross‑mode consistency problem.

## New Tests

- **Right Click Keyboard/Button** – `test_right_click_keyboard_or_button` mirrors
  the left‑click test to ensure right click actions combine keyboard and button
  states so either input triggers the correct timed action.
- **Inventory Context Toggle** – `test_inventory_toggle_context` verifies that
  `handle_inventory` switches context between `world` and `inventory` and that
  each toggle emits a `toggleInventory` command.
- **Rapid Sneak Toggle** – `test_rapid_sneak_toggle_sequence` checks that quick
  successive sneak toggles preserve ordering and state in the strategy calls.
- **Unknown Action Handling** – `test_process_actions_unknown_action` confirms
  that `process_actions` safely ignores unrecognised actions without touching the
  strategy.
- **Conversion Defaults & Filtering** – `test_convert_to_mcp_defaults` and
  `test_ignore_unknown_pygame_action` ensure the converter provides reasonable
  defaults for optional parameters and skips unconvertible actions.

## Confirmation Status

Like the earlier tests, these additions show that the Python logic for handling
clicks and interactions is self‑consistent. They demonstrate that toggle states
and default mappings behave predictably, even for rapid sequences or unknown
inputs. However, the tests still operate solely at the module level. They do not
capture WebSocket traffic or observe in‑game effects, so they cannot fully prove
that pygame and MCP modes behave identically.

## Remaining Work

To conclusively rule out inconsistencies, integration tests should:

1. Record WebSocket commands in both modes for identical user actions.
2. Use `getBotStatus` to verify world state after each interaction.
3. Measure real input durations to validate the mapping thresholds.

Until such end‑to‑end checks exist, the unit tests provide strong internal
coverage but stop short of guaranteeing complete cross‑mode parity.
