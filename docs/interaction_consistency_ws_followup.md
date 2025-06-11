# Interaction Consistency – WebSocket Follow Up

This note explains the latest tests and simulation helper that further inspect the cross‑mode behaviour between **pygame** and **MCP** modes.

## New Tests

- **Strategy Equivalence** – `tests/test_mode_strategy.py` creates dummy controllers and runs the same timed and toggle actions through `PygameModeStrategy` and `MCPModeStrategy`. The test converts the pygame WebSocket messages to the MCP format and asserts that both strategies ultimately produce identical MCP commands.

These tests expand on the previous handler checks by exercising the mode strategies directly and verifying their outputs match at the command level.

## New Simulation Code

The script `scripts/ws_cross_mode_strategy_sim.py` runs both strategies against a lightweight WebSocket relay and prints the sequences of messages produced. By comparing the output of each strategy side by side, we can manually confirm that the messages sent in each mode are equivalent.

Run it with:

```bash
python scripts/ws_cross_mode_strategy_sim.py
```

## Confirmation Status

The new unit tests confirm that our strategies map the same high‑level actions to equivalent MCP commands. Combined with the earlier handler and converter tests, this strongly suggests internal consistency. However, these checks still operate in isolation from a real Minecraft client. To fully disprove subtle inconsistencies we would need integration tests that:

1. Capture actual WebSocket traffic while interacting with the game in both modes.
2. Query `getBotStatus` to compare resulting world state.
3. Measure real input durations and validate the duration labels used.

Until such integration tests run, the current tests provide confidence but not conclusive proof that gameplay is identical across modes.
