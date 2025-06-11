# getBotStatus Consistency - Extra Tests

The latest test suite introduces a few more edge cases for the parser and the
state stability helper.

## What the extra tests cover

- **Missing position line**: `test_parse_bot_status_missing_position` verifies
  that when no `Position:` line is present, the parser returns default
  coordinates `(0, 0, 0)` and leaves rotation blank.
- **Line order flexibility**: `test_parse_bot_status_line_order` confirms that
  lines can appear in any order and still parse correctly.
- **Multi-line hotbar items**: `test_parse_bot_status_multiline_hotbar` checks
  that hotbar entries are detected even when split across lines.

Together with the previous suites, these tests show that the parser handles
various textual quirks and that `wait_for_state_stable` can cope with immediate
and delayed stability.

## Do these tests confirm the consistency problem?

No. They continue to operate on static strings and dummy async providers. They
demonstrate parser robustness but do not interact with a real `getBotStatus`
command. Therefore they neither confirm nor disprove the historic inconsistency
issue.

## Tests needed for real confirmation

To actually verify consistency we would need integration tests that repeatedly
call `getBotStatus` in a live game environment, comparing consecutive results and
checking commanded movements against reported positions and rotations. Such tests
would reveal whether the output ever jitters or diverges from expected values.
