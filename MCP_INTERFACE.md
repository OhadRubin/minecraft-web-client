# Minecraft MCP Server Interface Documentation

## Overview

The Minecraft MCP (Model Context Protocol) Server provides a standardized interface for controlling a Minecraft web client through WebSocket communication. The server runs on port 4000 (default) and connects to the Minecraft client on `ws://localhost:8081`.

## Connection Architecture

```**
MCP Client (LLM/Agent) **
    ↓ MCP Protocol
MCP Server (TypeScript) 
    ↓ WebSocket (port 8081)
Minecraft Web Client (Browser)
```

## Available MCP Tools

### 1. getBotStatus
**Purpose**: Get comprehensive information about the bot's current state
**Parameters**: None
**Returns**: Text summary with current bot status

```typescript
// No parameters required
```

**Response Format**:
```
Position: (x, y, z) facing Direction (yaw°, pitch°)
Biome: Biome Name
Day X, Y.YY minutes until next_event
Selected slot: N
Hotbar: [slot: item_name xcount] [slot: item_name xcount] ...
Status: Entity states (if any)
Looking at: block_name (can/cannot dig - distance info)
```

**Example Output**:
```
Position: (128.5, 64.0, 256.3) facing North (0°, 15°)
Biome: Plains
Day 3, 8.45 minutes until Dawn
Selected slot: 0
Hotbar: [0: Diamond Sword x1] [1: Cooked Beef x16] [2: Building Blocks x64]
Status: On Ground, Well Fed
Looking at: Oak Log (is close enough to dig)
```

### 2. walk
**Purpose**: Walk forward for specified duration
**Parameters**:
- `duration` (number): Duration in milliseconds (100-50000ms, default: 1000ms)

```typescript
{
  duration: number // 100 ≤ duration ≤ 50000
}
```

**Behavior**:
1. Sends `move` command with `z: -1` (forward)
2. Waits for specified duration
3. Sends `move` command with `z: 0` (stop)
4. Captures screenshot
5. Returns movement confirmation + screenshot

**WebSocket Commands Sent**:
```json
{"type": "move", "x": 0, "z": -1}  // Start walking
// ... wait duration ...
{"type": "move", "x": 0, "z": 0}   // Stop walking
```

### 3. lookAngle
**Purpose**: Smoothly rotate camera by specified yaw and pitch angles
**Parameters**:
- `xAngle` (number): Yaw delta in degrees (positive = right)
- `yAngle` (number): Pitch delta in degrees (positive = down)
- `speed` (enum): "slow" | "normal" | "fast" (default: "normal")

```typescript
{
  xAngle: number,    // Degrees of yaw rotation
  yAngle: number,    // Degrees of pitch rotation  
  speed?: "slow" | "normal" | "fast"
}
```

**Speed Configurations**:
- **slow**: 5px/step, 50ms delay
- **normal**: 10px/step, 30ms delay  
- **fast**: 15px/step, 15ms delay

**Behavior**:
1. Converts angle degrees to pixel movements (5px per degree)
2. Breaks movement into smooth steps with easing
3. Sends multiple `look` commands with calculated `movementX`/`movementY`
4. Uses easeInOutSine curve for natural movement
5. Captures screenshot after completion

**WebSocket Commands Sent**:
```json
{"type": "look", "movementX": dx, "movementY": dy}
// Multiple commands sent in sequence with timing delays
```

### 4. wait
**Purpose**: Wait for specified duration (useful for timing/delays)
**Parameters**:
- `duration` (number): Duration in milliseconds (100-10000ms, default: 1000ms)

```typescript
{
  duration: number // 100 ≤ duration ≤ 10000
}
```

**Behavior**:
1. Pauses execution for specified time
2. Captures screenshot
3. Returns wait confirmation + current state

### 5. rightClick
**Purpose**: Hold right mouse button for specified duration
**Parameters**:
- `duration` (enum): "short" | "medium" | "long" | "very_long" (default: "medium")

```typescript
{
  duration?: "short" | "medium" | "long" | "very_long"
}
```

**Duration Mappings**:
- **short**: 500ms
- **medium**: 1000ms
- **long**: 2000ms
- **very_long**: 5000ms

**Use Cases**: Eating food, using shields, placing blocks, using items

**WebSocket Commands Sent**:
```json
{"type": "documentMouseEvent", "button": 2, "action": "down", "updateMouse": true}
// ... wait duration ...
{"type": "documentMouseEvent", "button": 2, "action": "up", "updateMouse": false}
```

### 6. leftClick
**Purpose**: Hold left mouse button for specified duration
**Parameters**:
- `duration` (enum): "short" | "medium" | "long" | "very_long" (default: "medium")

```typescript
{
  duration?: "short" | "medium" | "long" | "very_long"
}
```

**Duration Mappings**: Same as rightClick

**Use Cases**: Breaking blocks, attacking entities, mining

**WebSocket Commands Sent**:
```json
{"type": "documentMouseEvent", "button": 0, "action": "down", "updateMouse": true}
// ... wait duration ...
{"type": "documentMouseEvent", "button": 0, "action": "up", "updateMouse": false}
```

## Response Format

All tools (except `getBotStatus`) return a structured response with:

```typescript
{
  content: [
    {
      type: "text",
      text: string // Action confirmation + current status
    },
    {
      type: "image", 
      data: string, // Base64 PNG screenshot
      mimeType: "image/png"
    }
  ]
}
```

## WebSocket Command Interface

### Underlying Commands
The MCP tools send these WebSocket commands to the Minecraft client:

**Movement Commands**:
```json
{"type": "move", "x": number, "z": number}
```

**Look Commands**:
```json
{"type": "look", "movementX": number, "movementY": number}
```

**Mouse Commands**:
```json
{
  "type": "documentMouseEvent",
  "button": number, // 0=left, 2=right
  "action": "down" | "up",
  "updateMouse": boolean
}
```

**Screenshot Request**:
```json
{"type": "getScreenshot"}
```

**Status Request**:
```json
{"type": "getBotStatus"}
```

**Client Registration**:
```json
{"init": "mcp"}
```

## Connection Management

### WebSocket Configuration
- **URL**: `ws://localhost:8081` (configurable via `MINECRAFT_WS_URL`)
- **Timeout**: 50 seconds (configurable via `CONNECTION_TIMEOUT`)
- **Auto-reconnection**: Handled automatically
- **Client identification**: Registers as "mcp" client

### Error Handling
- **Connection timeout**: Returns descriptive error after 50s
- **WebSocket errors**: Graceful fallback with error messages
- **Screenshot failures**: Returns 1x1 transparent pixel as fallback
- **Status request timeout**: 5 second timeout with cleanup

### Transport Options
The server supports two transport modes:

**STDIO Transport** (default):
```bash
pnpm mcp-server
# or
pnpm mcp-server -- --transport stdio
```

**HTTP Stream Transport**:
```bash
pnpm mcp-server -- --transport httpStream
```

## Usage Examples

### Basic Movement Sequence
```typescript
// Walk forward for 2 seconds
await mcp.call("walk", { duration: 2000 });

// Look around (45° right, 30° down)
await mcp.call("lookAngle", { xAngle: 45, yAngle: 30 });

// Check current status
await mcp.call("getBotStatus", {});
```

### Block Breaking Sequence
```typescript
// Look at target block
await mcp.call("lookAngle", { xAngle: 15, yAngle: -10 });

// Break block (hold left click)
await mcp.call("leftClick", { duration: "long" });

// Wait for block to break
await mcp.call("wait", { duration: 1500 });
```

### Item Usage
```typescript
// Use item (eat food, use shield)
await mcp.call("rightClick", { duration: "medium" });

// Wait for action to complete
await mcp.call("wait", { duration: 500 });
```

## Integration Notes

### Screenshot Integration
- All action tools automatically capture screenshots
- Images returned as base64-encoded PNG data
- 10-second timeout for screenshot capture
- Fallback transparent pixel on failure

### Status Integration  
- Bot status includes position, rotation, biome, time, inventory
- Hotbar contents shown with item counts
- Entity states (hunger, health, etc.) displayed
- Target block information with interaction capability

### Timing and Coordination
- Tools coordinate with game tick rate
- Smooth camera movements use easing curves
- Configurable speeds for different use cases
- Built-in delays prevent command flooding

This MCP interface provides comprehensive Minecraft control through a standardized protocol, enabling LLM agents to perform complex in-game actions with visual feedback. 