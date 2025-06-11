# getBotStatus Consistency - Additional Round of Tests

This update introduces two more parser cases and two WebSocket tests. A new script
`ws_cross_mode_consistency_extended.py` demonstrates how multiple MCP clients
and reconnecting bots communicate through the `CrossModeServer`.

## What the new tests cover

- **Multiple `Day` lines**: `test_parse_bot_status_multiple_day_lines` confirms
  that the parser keeps the last day/time line when several appear.
- **Trailing whitespace**: `test_parse_bot_status_trailing_whitespace` verifies
  that extra spaces at the ends of lines do not break parsing.
- **Multiple MCP clients**: `test_cross_mode_multiple_mcp_clients` checks that
  acknowledgements from bots are broadcast to every MCP connection.
- **Bot reconnect**: `test_cross_mode_reconnect_bot` ensures a bot can
  disconnect and reconnect while the server properly forwards subsequent
  commands.

These additions expand coverage but still use static strings and a minimal
WebSocket simulation. They show the parser and forwarding logic behave as
expected, yet they cannot reveal whether real `getBotStatus` output is always
consistent.

## Future testing needed

To conclusively confirm or disprove the historical inconsistency issue we would
need integration tests running against a live game instance. Those tests should
collect repeated `getBotStatus` samples while issuing commands and compare the
results for variance.

