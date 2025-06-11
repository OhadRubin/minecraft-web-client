# getBotStatus Consistency - Additional Tests

This note documents the latest unit tests added for Agent 3's parsing utilities and explains their relevance to the historic consistency issue.

## What the new tests cover

- **Precision handling**: `test_parse_bot_status_precision` validates that coordinates and rotation angles with many decimal places parse correctly and that hotbar items beyond slot 0 and 1 are captured.
- **Stability recovery**: `test_wait_for_state_stable_recovers` feeds changing output until a repeated value appears, verifying that `wait_for_state_stable` resets its counter on changes and eventually returns when the text stabilizes.

Together with earlier tests (missing fields, wraparound, multiple items, timeout), these ensure the parser and stability helper behave robustly for static input.

## Do these tests confirm the consistency problem?

No. Like the previous suites, they rely on canned strings and do not interact with a real Minecraft instance. They prove only that our parsing code can detect identical results and handle edge cases. They cannot demonstrate whether `getBotStatus` itself ever reports inconsistent data while the game is running.

## Tests needed for a real answer

To actually confirm or disprove the historic inconsistency issue, we would need integration tests that:

1. **Collect live samples**: Continuously call `getBotStatus` from a running server while the bot is idle and check for jitter in successive outputs.
2. **Command-driven checks**: Issue movement or rotation commands, wait for stability, and assert that the reported state matches the expected result every time.
3. **Boundary scenarios**: Run these tests near world edges and with rotations that wrap past ±360° to detect any irregularities.
4. **Statistical evaluation**: Gather many sequences, compute variance, and fail if the spread exceeds a small tolerance.

Only such integration-level testing would definitively reveal whether the consistency problem still exists.
