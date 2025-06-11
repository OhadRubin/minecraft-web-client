# getBotStatus Consistency - Latest Tests

This note describes the newest unit tests for Agent 3's parser and explains how they relate to the historic consistency issue.

## What the latest tests cover

- **Negative rotation values**: `test_parse_bot_status_negative_rotation` ensures yaw and pitch below ±360° parse correctly and that the `looking_at` field captures additional text.
- **Empty hotbar line**: `test_parse_bot_status_no_hotbar_items` verifies that the parser gracefully handles a `Hotbar:` line with no items and leaves `selected_slot` unset.
- **Immediate stability detection**: `test_wait_for_state_stable_immediate` confirms that the stability helper returns after a single call when `attempts=1`.

These extend previous edge case coverage (precision, wraparound, state recovery, timeout) and help prove that the parser and stability helper behave predictably when fed representative strings.

## Do these tests confirm the consistency problem?

No. Like earlier suites, they operate purely on canned text and do not interact with a live Minecraft instance. They show that our parsing code would correctly recognise stable output, but they don't test whether `getBotStatus` itself ever produces inconsistent data during real gameplay.

## What tests would provide a definitive answer?

To truly confirm or disprove the historic inconsistency issue we would need integration tests that:

1. **Collect live samples** of consecutive `getBotStatus` calls while the bot is idle to look for jitter.
2. **Drive actions** (movement or rotation commands), wait for stability and compare the final state to expected outcomes.
3. **Probe boundary scenarios** such as world edges or rotations beyond 360° to detect wraparound bugs.
4. **Measure variance** across many runs and fail if observed spread exceeds a tight tolerance.

Implementing such tests requires a running server environment and orchestration code, but only they can resolve the open question about real-world consistency.
