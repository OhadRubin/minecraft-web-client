# getBotStatus Consistency - Final Round of Tests

The newest suite introduces a few more edge cases and a callback check for the test
WebSocket client.

## What these tests cover

- **Duplicate position lines**: `test_parse_bot_status_duplicate_position` ensures
  the parser uses the last `Position:` line when multiple are present.
- **CRLF newline handling**: `test_parse_bot_status_crlf_newlines` verifies Windows
  style line endings do not break parsing.
- **Unknown lines ignored**: `test_parse_bot_status_unknown_lines` confirms extra
  unrecognised lines are safely skipped.
- **Delayed stability**: `test_wait_for_state_stable_delayed` feeds three different
  status texts before repeating one to check that the stability helper resets its
  counter correctly.
- **WebSocket callbacks**: `test_connect_callbacks` makes sure the lightweight
  `WebSocketClient` triggers its connect and disconnect callbacks.

## Do these tests confirm the consistency problem?

No. Like the previous rounds, they rely on static strings and a dummy websocket.
They show that our parser and helper functions behave predictably for various
synthetic scenarios, but they still do not exercise the real `getBotStatus`
command in a live Minecraft world.

## Tests needed for a real answer

To truly confirm or disprove the historic inconsistency we would need integration
experiments that:

1. Collect consecutive `getBotStatus` samples from an actual server to look for
   jitter while the bot is idle.
2. Issue movement or rotation commands and verify the reported state after waiting
   for stability matches the expected outcome.
3. Run these sequences near world edges and with rotations that wrap around to
   check for boundary bugs.
4. Gather statistics across many runs and fail if the variance exceeds a tight
   tolerance.

Until such integration tests exist, unit tests can only confirm that our parsing
code would notice inconsistent output—they cannot prove whether it actually
occurs.
