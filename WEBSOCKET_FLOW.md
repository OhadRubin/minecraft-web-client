# WebSocket Server Flow Documentation

## Overview

This system uses a **WebSocket relay server** to enable real-time communication between different types of clients in a Minecraft web client environment. The server acts as a message broker, routing commands and responses between various client types.

## Architecture

### Server Setup
- **HTTP Server**: Serves static files and configuration (default port: 8080)
- **WebSocket Server**: Handles real-time communication (HTTP port + 1, e.g., 8081)
- **Separate Ports**: HTTP and WebSocket servers run on different ports for better isolation

### Client Types

The system supports three distinct client types:

1. **Bot Clients** (`init: 'bot'`)
   - The Minecraft web client itself
   - Executes game commands (movement, clicks, chat, etc.)
   - Captures screenshots
   - Responds to control messages

2. **MCP Clients** (`init: 'mcp'`)
   - Model Context Protocol clients
   - Send high-level commands to control the bot
   - Receive responses and status updates

3. **Pygame Clients** (`init: 'pygame'`)
   - External Python/Pygame applications
   - Send game control commands
   - Share similar message routing as MCP clients

## Message Flow

### Client Registration
```
Client connects → Sends {init: 'bot'|'mcp'|'pygame'} → Server adds to appropriate Set
```

### Message Routing Rules

#### 1. Bot Client → MCP Clients
```
Bot Client sends response → Server forwards to ALL MCP clients
```
- Bot execution results
- Screenshot data
- Status updates
- Error messages

#### 2. MCP Client → Bot Clients
```
MCP Client sends command → Server forwards to ALL Bot clients
```
- Game control commands
- Screenshot requests
- Configuration changes

#### 3. Pygame Client → Bot Clients
```
Pygame Client sends command → Server forwards to ALL Bot clients
```
- Same routing as MCP clients
- Game control commands
- Input simulation

### Supported Commands

Bot clients can execute these command types:

| Command Type | Description | Parameters |
|--------------|-------------|------------|
| `control` | Set control state (WASD, jump, etc.) | `control`, `state` |
| `leftDown`/`leftUp` | Left mouse button | - |
| `rightDown`/`rightUp` | Right mouse button | - |
| `chat` | Send chat message | `message` |
| `move` | Player movement | `x`, `z` |
| `look` | Camera rotation | `movementX`, `movementY` |
| `lookTouch` | Touch-based look | `currentX/Y`, `lastX/Y` |
| `clickElement` | Click UI element | `selector`, `action` |
| `documentMouseEvent` | Simulate mouse events | `button`, `action` |
| `setHotbarSlot` | Change hotbar slot | `slot` |
| `scrollHotbar` | Scroll hotbar | `direction` |
| `dropItem` | Drop items | `amount` |
| `swapHands` | Swap main/offhand | - |
| `cursor` | Move cursor | `x`, `z` or `movementX/Y` |
| `getScreenshot` | Capture screen | - |

## Connection Flow

### 1. Server Startup
```javascript
// HTTP server starts on port 8080
const server = app.listen(8080)

// WebSocket server starts on port 8081
const wsServer = http.createServer()
const wss = new WebSocket.Server({ server: wsServer })
wsServer.listen(8081)
```

### 2. Client Connection (Bot Example)
```javascript
// Client connects to ws://localhost:8081
const ws = new WebSocket('ws://localhost:8081')

// Register as bot client
ws.send(JSON.stringify({ init: 'bot' }))

// Start receiving commands
ws.addEventListener('message', (ev) => {
  const cmd = JSON.parse(ev.data)
  // Execute command...
})
```

### 3. Command Execution Flow
```
MCP Client → Command → Server → Bot Client → Execution → Response → Server → MCP Client
```

## Error Handling

### Connection Management
- Clients are automatically removed from Sets when they disconnect
- Server continues operating even if some client types are missing
- Warning messages logged when no target clients available

### Message Processing
- Invalid JSON messages are caught and logged
- Screenshot data is filtered from console logs to prevent spam
- Large messages are truncated in log output

### Race Condition Protection
⚠️ **Known Issue**: The current implementation has potential race conditions when iterating over client Sets while clients disconnect simultaneously.

**Recommended Fix**: Use `Array.from(clientSet)` to create snapshots before iteration.

## Security Considerations

### Current Limitations
- No authentication required for client connections
- Wide-open CORS policy (`allowOrigin: '*'`)
- No input validation on WebSocket messages
- No rate limiting on connections or messages

### Production Recommendations
- Implement client authentication
- Restrict CORS to specific origins
- Add input validation for all message types
- Implement rate limiting and connection limits
- Add message size limits

## Monitoring & Logging

### Built-in Logging
- Connection events (connect/disconnect)
- Message routing statistics
- Client type registration
- Error conditions
- Screenshot data filtering

### Log Files
- WebSocket events logged via `wsLogger` module
- Console output for real-time monitoring
- Automatic log rotation and cleanup

## Performance Notes

### Optimizations
- Screenshot data filtered from console logs
- Compression middleware enabled
- Efficient Set operations for client management
- Message forwarding uses direct iteration

### Scalability Considerations
- All clients kept in memory (not suitable for large scales)
- No message queuing for offline clients
- No load balancing between multiple server instances
- Single-threaded Node.js event loop

## Example Usage

### Starting the Server
```bash
node server.js 8080          # HTTP on 8080, WS on 8081
node server.js --prod 3000   # Production mode on port 3000
```

### Connecting Multiple Clients
```javascript
// Bot client (web browser)
const botWs = new WebSocket('ws://localhost:8081')
botWs.send(JSON.stringify({ init: 'bot' }))

// MCP client (AI controller)
const mcpWs = new WebSocket('ws://localhost:8081')
mcpWs.send(JSON.stringify({ init: 'mcp' }))

// Send command from MCP to bot
mcpWs.send(JSON.stringify({
  type: 'move',
  x: 1,
  z: 0
}))
```

This architecture enables flexible, real-time control of Minecraft web clients through a simple but powerful message relay system. 