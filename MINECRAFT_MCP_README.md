# Minecraft MCP Server

A Model Context Protocol (MCP) server that allows AI assistants to control a Minecraft bot through WebSocket commands. This server exposes all Minecraft bot controls as MCP tools, enabling seamless integration with AI assistants like Claude.

## Features

- **Movement Controls**: WASD-style movement with precise control
- **Camera Control**: Look around using mouse-like controls
- **Mouse Actions**: Left/right click with precise timing
- **Game Controls**: Jump, sprint, sneak, inventory management
- **Chat Integration**: Send messages to the game chat
- **Hotbar Management**: Switch slots, scroll, and manage items
- **UI Interaction**: Click on game UI elements using CSS selectors
- **Cursor Control**: Set cursor position or move relatively
- **Utility Actions**: High-level actions like walking forward, jumping, block breaking

## Prerequisites

1. **Minecraft Web Client**: The main Minecraft web client must be running
2. **WebSocket Server**: The WebSocket server (typically on port 8081) must be active
3. **Node.js**: Node.js 18+ with pnpm package manager

## Installation

1. Install dependencies:
```bash
pnpm install
```

2. The server is already configured in the project's `package.json` with these scripts:
   - `pnpm mcp-server` - Run the MCP server directly
   - `pnpm mcp-dev` - Run with FastMCP CLI for testing
   - `pnpm mcp-inspect` - Run with MCP Inspector for web UI testing
   - `pnpm mcp-test` - Test the MCP server connection and tools

## Running the Server

### Option 1: Direct Server Mode
```bash
pnpm mcp-server
```
This starts the MCP server on port 4000 with HTTP streaming support.

### Option 2: Development/Testing Mode
```bash
pnpm mcp-dev
```
This runs the server with the FastMCP CLI for interactive testing.

### Option 3: Web Inspector Mode
```bash
pnpm mcp-inspect
```
This opens the MCP Inspector web interface for testing tools.

### Option 4: Testing Mode
```bash
pnpm mcp-test
```
This runs a test script to verify the server is working and lists all available tools.

## Server Endpoints

When running the server directly (default port 4000):
- **MCP Stream**: `http://localhost:4000/stream`
- **Health Check**: `http://localhost:4000/health`

> **Note**: The default port is 4000 to avoid conflicts with other development servers. You can change it by setting the `PORT` environment variable: `PORT=3000 pnpm mcp-server`

## Available Tools

### Movement Controls

#### `move`
Move the player using WASD-style controls.
- `x`: Horizontal movement (-1 to 1, negative = left, positive = right)
- `z`: Vertical movement (-1 to 1, negative = forward, positive = backward)

#### `walkForward`
Walk forward for a specified duration.
- `duration`: Duration in milliseconds (100-5000, default: 1000)

### Camera Controls

#### `look`
Control camera rotation/look direction.
- `movementX`: Horizontal mouse movement (negative = left, positive = right)
- `movementY`: Vertical mouse movement (negative = up, positive = down)

#### `lookTouch`
Control camera rotation using touch-style input.
- `currentX`, `lastX`: Current and previous X positions
- `currentY`, `lastY`: Current and previous Y positions

### Mouse Actions

#### `leftClick`
Perform left mouse click.
- `action`: "down" or "up"

#### `rightClick`
Perform right mouse click.
- `action`: "down" or "up"

#### `leftClickAndHold`
Hold left click for a specified duration (useful for breaking blocks).
- `duration`: Duration to hold in milliseconds (100-10000, default: 1000)

#### `mouseEvent`
Send precise mouse events to the document.
- `button`: Mouse button (0 = left, 2 = right)
- `action`: "down" or "up"
- `updateMouse`: Whether to update mouse state (optional)

### Game Controls

#### `gameControl`
Control game states like jumping, sprinting, sneaking, or inventory.
- `control`: "jump", "sneak", "sprint", or "inventory"
- `state`: true to enable, false to disable

#### `jump`
Perform a single jump (utility function).

### Chat

#### `chat`
Send a message to the game chat.
- `message`: The message to send (max 256 characters)

### Hotbar Management

#### `setHotbarSlot`
Set the active hotbar slot.
- `slot`: Hotbar slot number (0-8)

#### `scrollHotbar`
Scroll the hotbar left or right.
- `direction`: 1 for right, -1 for left

### Item Management

#### `dropItem`
Drop items from the currently selected hotbar slot.
- `amount`: Number of items to drop (1-64)

#### `swapHands`
Swap items between main hand and off-hand.

### UI Interaction

#### `clickElement`
Click on a UI element using CSS selector.
- `selector`: CSS selector for the element to click
- `action`: "click", "down", or "up"

### Cursor Control

#### `setCursor`
Set cursor position on screen.
- `x`: X position as percentage (0-100)
- `z`: Y position as percentage (0-100)

#### `moveCursor`
Move cursor by relative amounts.
- `movementX`: Horizontal movement amount
- `movementY`: Vertical movement amount

### Utility Tools

#### `connectionStatus`
Check the status of the WebSocket connection to the Minecraft client.

## Usage Examples

### Basic Movement
```typescript
// Walk forward for 2 seconds
await walkForward({ duration: 2000 });

// Move diagonally (forward-right)
await move({ x: 0.5, z: -0.5 });
```

### Combat Actions
```typescript
// Look at a target and attack
await look({ movementX: 10, movementY: -5 });
await leftClickAndHold({ duration: 500 });
```

### Building Actions
```typescript
// Select the right tool
await setHotbarSlot({ slot: 2 });

// Look down and place a block
await look({ movementX: 0, movementY: 20 });
await rightClick({ action: "down" });
await rightClick({ action: "up" });
```

### Exploration
```typescript
// Jump and move forward
await jump();
await walkForward({ duration: 1000 });

// Look around
await look({ movementX: 90, movementY: 0 }); // Look right
await look({ movementX: -180, movementY: 0 }); // Look left
```

## Integration with AI Assistants

### Claude Desktop Configuration

To use this server with Claude Desktop, add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "minecraft-controller": {
      "command": "pnpm",
      "args": ["mcp-server"],
      "cwd": "/path/to/minecraft-web-client",
      "env": {
        "PORT": "4000"
      }
    }
  }
}
```

### Using with Other MCP Clients

For other MCP clients that support HTTP streaming:

```typescript
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";

const client = new Client(
  {
    name: "minecraft-client",
    version: "1.0.0",
  },
  {
    capabilities: {},
  }
);

const transport = new StreamableHTTPClientTransport(
  new URL("http://localhost:4000/stream")
);

await client.connect(transport);
```

## Architecture

The MCP server acts as a bridge between AI assistants and the Minecraft web client:

```
AI Assistant (Claude) 
    ↓ (MCP Protocol)
Minecraft MCP Server 
    ↓ (WebSocket)
Minecraft Web Client 
    ↓ (Game Commands)
Minecraft Game
```

1. **AI Assistant** sends tool requests via MCP
2. **MCP Server** translates requests to WebSocket commands
3. **WebSocket Server** forwards commands to the game client
4. **Game Client** executes the commands in Minecraft

## Troubleshooting

### Connection Issues

1. **WebSocket connection failed**: Ensure the Minecraft web client is running and the WebSocket server is active on port 8081.

2. **MCP server won't start**: Check that port 3000 is available, or set a different port using the `PORT` environment variable.

3. **Commands not working**: Use the `connectionStatus` tool to check the WebSocket connection status.

### Performance Tips

1. **Batch related commands**: For complex actions, send multiple commands in sequence rather than one at a time.

2. **Use utility functions**: Functions like `walkForward` and `leftClickAndHold` are optimized for common actions.

3. **Monitor connection**: Check connection status periodically for long-running sessions.

## Development

### Adding New Tools

To add new tools to the MCP server:

1. Define the tool parameters using Zod schema
2. Implement the execute function
3. Add the tool to the server using `server.addTool()`

Example:
```typescript
server.addTool({
  name: "myNewTool",
  description: "Description of what this tool does",
  parameters: z.object({
    param1: z.string().describe("Description of parameter"),
  }),
  execute: async (args) => {
    return await sendCommand({
      type: "myCommandType",
      param1: args.param1,
    });
  },
});
```

### Testing

Use the FastMCP development tools:

```bash
# Interactive CLI testing
pnpm mcp-dev

# Web-based testing
pnpm mcp-inspect
```

## License

This project is part of the Minecraft Web Client and follows the same MIT license. 