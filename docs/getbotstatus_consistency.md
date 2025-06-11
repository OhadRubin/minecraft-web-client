# getBotStatus Consistency Tests

The repository currently includes unit tests for Agent 3's parsing utilities. This note explains whether those tests confirm the historical consistency issues with `getBotStatus`.

## What the existing tests check

- **Parser correctness**: `test_parse_bot_status_basic` feeds a sample status string to `parse_bot_status()` and verifies that position, rotation, biome, inventory and looking-at data are extracted correctly.
- **State stability helper**: `test_wait_for_state_stable` uses a dummy async getter that always returns the same text. The helper waits until the same parsed status is observed multiple times.

These tests ensure the parser works and that the stability helper returns when identical text is repeated. They do **not** involve a running game instance or the real `getBotStatus` command. As such they cannot reveal whether `getBotStatus` sometimes reports inconsistent values in practice.

## Why the consistency problem remains unconfirmed

The historical "consistency problem" refers to `getBotStatus` occasionally reporting different positions or rotations for the same game state due to async timing issues. Because our tests rely on a static string and a dummy provider, they don't exercise the real data path where that inconsistency was observed. Therefore the tests neither confirm nor disprove the problem—they merely verify that our parsing logic would notice if the same text repeats.

## Ideas for tests that would confirm/disprove it

1. **Live server integration**: Spin up a headless Minecraft instance (or use mineflayer) and repeatedly call `getBotStatus` while the bot is idle. Expect three identical results in a row.
2. **Action sequences**: Issue known movement or rotation commands, then call `wait_for_state_stable()` and verify the final position/rotation matches what the commands should produce. Repeat to ensure results are consistent across runs.
3. **Edge cases**: Test near world boundaries and with yaw wrapping (e.g., rotating past 359°) to see if values jitter.
4. **Statistical analysis**: Collect many sequences and compute variance in reported positions/rotations. Any non-zero variance when repeating the same commands would indicate inconsistency.

Implementing these integration tests would require a running game environment and more complex orchestration, but they would directly address whether the consistency problem still exists.
