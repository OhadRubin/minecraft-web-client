import { FastMCP } from "fastmcp";
import { z } from "zod";
import WebSocket from "ws";

// Define the command interfaces based on the existing TypeScript code
interface MinecraftCommand {
    type: string;
    [key: string]: any;
}

// Create the MCP server
const server = new FastMCP({
    name: "Minecraft Controller",
    version: "1.0.0",
    description: "Control a Minecraft bot through MCP tools",
    instructions: `This server provides tools to control a Minecraft bot through WebSocket commands. 
  
The bot can perform various actions including:
- Movement (WASD controls)
- Camera control (looking around)
- Mouse actions (left/right click)
- Inventory management (hotbar slots, item dropping)
- Chat messages
- Game controls (jump, sprint, sneak)
- UI interactions

Make sure the Minecraft client is running and the WebSocket server is available on port 8081.`,
});

// WebSocket connection management
let ws: WebSocket | null = null;
let connectionPromise: Promise<void> | null = null;

async function ensureConnection(): Promise<void> {
    if (ws?.readyState === WebSocket.OPEN) {
        return;
    }

    if (connectionPromise) {
        return connectionPromise;
    }

    connectionPromise = new Promise((resolve, reject) => {
        const wsUrl = "ws://localhost:8081";
        ws = new WebSocket(wsUrl);

        const timeout = setTimeout(() => {
            reject(new Error("WebSocket connection timeout"));
        }, 5000);

        ws.on('open', () => {
            clearTimeout(timeout);
            console.log("Connected to Minecraft WebSocket server");
            // Register as MCP client
            ws!.send(JSON.stringify({ init: 'mcp' }));
            resolve();
        });

        ws.on('error', (error) => {
            clearTimeout(timeout);
            connectionPromise = null;
            reject(error);
        });

        ws.on('close', () => {
            console.log("WebSocket connection closed");
            ws = null;
            connectionPromise = null;
        });
    });

    return connectionPromise;
}

async function sendCommand(command: MinecraftCommand): Promise<string> {
    await ensureConnection();

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        throw new Error("WebSocket connection not available");
    }

    ws.send(JSON.stringify(command));
    return `Command sent: ${command.type}`;
}

// Movement controls
server.addTool({
    name: "move",
    description: "Move the player using WASD-style controls",
    parameters: z.object({
        x: z.number().min(-1).max(1).describe("Horizontal movement (-1 to 1, negative = left, positive = right)"),
        z: z.number().min(-1).max(1).describe("Vertical movement (-1 to 1, negative = forward, positive = backward)"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "move",
            x: args.x,
            z: args.z,
        });
    },
});

// Camera control
server.addTool({
    name: "look",
    description: "Control camera rotation/look direction",
    parameters: z.object({
        movementX: z.number().describe("Horizontal mouse movement (negative = left, positive = right)"),
        movementY: z.number().describe("Vertical mouse movement (negative = up, positive = down)"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "look",
            movementX: args.movementX,
            movementY: args.movementY,
        });
    },
});

// Touch-based look control
server.addTool({
    name: "lookTouch",
    description: "Control camera rotation using touch-style input",
    parameters: z.object({
        currentX: z.number().describe("Current X position"),
        lastX: z.number().describe("Previous X position"),
        currentY: z.number().describe("Current Y position"),
        lastY: z.number().describe("Previous Y position"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "lookTouch",
            currentX: args.currentX,
            lastX: args.lastX,
            currentY: args.currentY,
            lastY: args.lastY,
        });
    },
});

// Mouse controls
server.addTool({
    name: "leftClick",
    description: "Perform left mouse click (down and up)",
    parameters: z.object({
        action: z.enum(["down", "up"]).describe("Whether to press down or release the left mouse button"),
    }),
    execute: async (args) => {
        const commandType = args.action === "down" ? "leftDown" : "leftUp";
        return await sendCommand({ type: commandType });
    },
});

server.addTool({
    name: "rightClick",
    description: "Perform right mouse click (down and up)",
    parameters: z.object({
        action: z.enum(["down", "up"]).describe("Whether to press down or release the right mouse button"),
    }),
    execute: async (args) => {
        const commandType = args.action === "down" ? "rightDown" : "rightUp";
        return await sendCommand({ type: commandType });
    },
});

// Document mouse events (for more precise control)
server.addTool({
    name: "mouseEvent",
    description: "Send precise mouse events to the document",
    parameters: z.object({
        button: z.enum([0, 2]).describe("Mouse button (0 = left, 2 = right)"),
        action: z.enum(["down", "up"]).describe("Mouse action"),
        updateMouse: z.boolean().optional().describe("Whether to update mouse state"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "documentMouseEvent",
            button: args.button,
            action: args.action,
            updateMouse: args.updateMouse,
        });
    },
});

// Game controls
server.addTool({
    name: "gameControl",
    description: "Control game states like jumping, sprinting, sneaking, or inventory",
    parameters: z.object({
        control: z.enum(["jump", "sneak", "sprint", "inventory"]).describe("The control to activate"),
        state: z.boolean().describe("Whether to enable (true) or disable (false) the control"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "control",
            control: args.control,
            state: args.state,
        });
    },
});

// Chat
server.addTool({
    name: "chat",
    description: "Send a chat message",
    parameters: z.object({
        message: z.string().max(256).describe("The message to send in chat"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "chat",
            message: args.message,
        });
    },
});

// Hotbar management
server.addTool({
    name: "setHotbarSlot",
    description: "Set the active hotbar slot",
    parameters: z.object({
        slot: z.number().min(0).max(8).describe("Hotbar slot number (0-8)"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "setHotbarSlot",
            slot: args.slot,
        });
    },
});

server.addTool({
    name: "scrollHotbar",
    description: "Scroll the hotbar left or right",
    parameters: z.object({
        direction: z.enum([1, -1]).describe("Scroll direction (1 = right, -1 = left)"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "scrollHotbar",
            direction: args.direction,
        });
    },
});

// Item management
server.addTool({
    name: "dropItem",
    description: "Drop items from the currently selected hotbar slot",
    parameters: z.object({
        amount: z.number().min(1).max(64).describe("Number of items to drop (1-64)"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "dropItem",
            amount: args.amount,
        });
    },
});

server.addTool({
    name: "swapHands",
    description: "Swap items between main hand and off-hand",
    execute: async () => {
        return await sendCommand({ type: "swapHands" });
    },
});

// UI interaction
server.addTool({
    name: "clickElement",
    description: "Click on a UI element using CSS selector",
    parameters: z.object({
        selector: z.string().describe("CSS selector for the element to click"),
        action: z.enum(["click", "down", "up"]).describe("Type of click action"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "clickElement",
            selector: args.selector,
            action: args.action,
        });
    },
});

// Cursor control
server.addTool({
    name: "setCursor",
    description: "Set cursor position on screen",
    parameters: z.object({
        x: z.number().min(0).max(100).describe("X position as percentage (0-100)"),
        z: z.number().min(0).max(100).describe("Y position as percentage (0-100)"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "cursor",
            x: args.x,
            z: args.z,
        });
    },
});

server.addTool({
    name: "moveCursor",
    description: "Move cursor by relative amounts",
    parameters: z.object({
        movementX: z.number().describe("Horizontal movement amount"),
        movementY: z.number().describe("Vertical movement amount"),
    }),
    execute: async (args) => {
        return await sendCommand({
            type: "cursor",
            movementX: args.movementX,
            movementY: args.movementY,
        });
    },
});

// Utility tools for common combinations
server.addTool({
    name: "walkForward",
    description: "Walk forward for a brief moment",
    parameters: z.object({
        duration: z.number().min(100).max(5000).default(1000).describe("Duration in milliseconds"),
    }),
    execute: async (args) => {
        await sendCommand({ type: "move", x: 0, z: -1 });
        await new Promise(resolve => setTimeout(resolve, args.duration));
        await sendCommand({ type: "move", x: 0, z: 0 });
        return `Walked forward for ${args.duration}ms`;
    },
});

server.addTool({
    name: "jump",
    description: "Perform a single jump",
    execute: async () => {
        await sendCommand({ type: "control", control: "jump", state: true });
        await new Promise(resolve => setTimeout(resolve, 100));
        await sendCommand({ type: "control", control: "jump", state: false });
        return "Performed jump";
    },
});

server.addTool({
    name: "leftClickAndHold",
    description: "Hold left click for a specified duration (useful for breaking blocks)",
    parameters: z.object({
        duration: z.number().min(100).max(10000).default(1000).describe("Duration to hold in milliseconds"),
    }),
    execute: async (args) => {
        await sendCommand({ type: "leftDown" });
        await new Promise(resolve => setTimeout(resolve, args.duration));
        await sendCommand({ type: "leftUp" });
        return `Left clicked and held for ${args.duration}ms`;
    },
});

// Connection status tool
server.addTool({
    name: "connectionStatus",
    description: "Check the status of the WebSocket connection to the Minecraft client",
    execute: async () => {
        if (!ws) {
            return "Not connected to Minecraft client";
        }

        const status = {
            0: "CONNECTING",
            1: "OPEN",
            2: "CLOSING",
            3: "CLOSED"
        }[ws.readyState] || "UNKNOWN";

        return `WebSocket connection status: ${status}`;
    },
});

// Start the server
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 4000;

server.start({
    transportType: "httpStream",
    httpStream: {
        port: PORT,
    },
}).then(() => {
    console.log(`Minecraft MCP Server started on port ${PORT}`);
    console.log(`Connect to: http://localhost:${PORT}/stream`);
    console.log(`Health check: http://localhost:${PORT}/health`);
}).catch((error) => {
    console.error("Failed to start server:", error);
    process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('Shutting down Minecraft MCP Server...');
    if (ws) {
        ws.close();
    }
    process.exit(0);
}); 