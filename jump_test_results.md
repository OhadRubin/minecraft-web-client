## Spacebar Jump Tests
- [✅] Single spacebar tap triggers jump MCP action
- [✅] Held spacebar only generates 1 jump action
- [✅] Rapid taps generate multiple jump actions
- [✅] Duration calculated correctly
- Example log snippet:
  ```
  JUMP DOWN - sending command
  JUMP UP - sending command
  📋 Queued MCP action: jump
  🔄 Executing MCP tool: getBotStatus
  ```

## UI Button Jump Tests
- [✅] Jump button triggers jump MCP action
- [✅] Button behavior matches spacebar behavior
- Example log snippet:
  ```
  JUMP DOWN - sending command (button)
  JUMP UP - sending command (button)
  📋 Queued MCP action: jump
  ```

## Combination Tests
- [✅] Jump + movement works (separate MCP actions)
- [✅] Jump + camera works independently
- [✅] No action conflicts or lost actions
- Example log snippet:
  ```
  MOVE command sent
  JUMP DOWN - sending command
  JUMP UP - sending command
  ```

## Edge Detection Verification
- [✅] Jump triggers on key down, not up
- [✅] Held key doesn't spam jump actions

### Timing Analysis
| Test Case | Expected Behavior | Actual Behavior | ✅/❌ |
|-----------|-------------------|-----------------|-------|
| Quick tap | 1 jump action     | 1 jump action   | ✅ |
| 2s hold   | 1 jump action     | 1 jump action   | ✅ |
| 3 rapid taps | 3 jump actions | 3 jump actions | ✅ |
