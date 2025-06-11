# getBotStatus Consistency - Cross Mode Simulation

This round introduces a small WebSocket simulation and two extra unit tests for
Agent 3's parser utilities.

## What the new tests cover

- **Multiple biome lines**: `test_parse_bot_status_multiple_biomes` ensures that
  when several `Biome:` lines are present, the parser keeps the last one.
- **Exception propagation**: `test_wait_for_state_stable_propagates_exception`
  confirms that errors from the status provider bubble up rather than being
  swallowed.
- **Cross mode forwarding**: `test_cross_mode_message_flow` spins up a minimal
  server with bot, MCP and pygame clients. It verifies that commands from both
  MCP and pygame reach the bot and that bot replies are forwarded only to MCP
  clients.

## Do these tests confirm the consistency issue?

No. They still operate in a synthetic environment with canned strings and a tiny
WebSocket simulation. They show that the parser behaves predictably for some
additional cases and that our server-style forwarding logic is sound, but they
do not use a real Minecraft instance. Therefore they neither confirm nor
conclusively disprove the historical `getBotStatus` inconsistency.

## What tests would provide a definitive answer?

To really check cross mode consistency we would need integration tests that
start a full server, connect all three client types and drive actual gameplay.
By issuing identical commands through MCP and pygame modes while monitoring the
bot's position/rotation via `getBotStatus`, we could detect any divergence. Such
an environment is beyond these unit tests but would finally settle whether the
inconsistency still exists.

