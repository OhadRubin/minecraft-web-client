import { FastMCP } from "fastmcp";
import { z } from "zod";
import WebSocket from "ws";
import { UserError } from "fastmcp";

// Define the command interfaces based on the existing TypeScript code
interface MinecraftCommand {
    type: string;
    [key: string]: any;
}

// Create the MCP server
const server = new FastMCP({
    name: "Minecraft Controller",
    version: "1.0.0",
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

// Configuration constants
const WEBSOCKET_URL = process.env.MINECRAFT_WS_URL || "ws://localhost:8081";
const CONNECTION_TIMEOUT = parseInt(process.env.CONNECTION_TIMEOUT || "50000"); // Increased to 15 seconds

async function ensureConnection(): Promise<void> {
    if (ws?.readyState === WebSocket.OPEN) {
        return;
    }

    if (connectionPromise) {
        return connectionPromise;
    }

    connectionPromise = new Promise((resolve, reject) => {
        const wsUrl = WEBSOCKET_URL;
        ws = new WebSocket(wsUrl);

        const timeout = setTimeout(() => {
            reject(new Error(`WebSocket connection timeout after ${CONNECTION_TIMEOUT}ms. Make sure Minecraft client is running and WebSocket server is available on ${wsUrl}`));
        }, CONNECTION_TIMEOUT);

        ws.on('open', () => {
            clearTimeout(timeout);
            // console.log("Connected to Minecraft WebSocket server");
            // Register as MCP client
            ws!.send(JSON.stringify({ init: 'mcp' }));
            resolve();
        });

        ws.on('error', (error) => {
            clearTimeout(timeout);
            connectionPromise = null;
            reject(new Error(`WebSocket connection failed: ${error.message}`));
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
    try {
        await ensureConnection();

        if (!ws || ws.readyState !== WebSocket.OPEN) {
            throw new UserError("Minecraft client is not connected. Please ensure the game is running and WebSocket server is available on port 8081.");
        }

        ws.send(JSON.stringify(command));
        return `Command sent: ${command.type}`;
    } catch (error) {
        if (error instanceof UserError) {
            throw error;
        }
        throw new UserError(`Failed to send command to Minecraft: ${error.message || 'Unknown error'}`);
    }
}

async function sendCommandWithScreenshot(command: MinecraftCommand, actionDescription: string) {
    await ensureConnection();

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        throw new Error("WebSocket connection not available");
    }

    ws.send(JSON.stringify(command));
    const screenshotResponse = await captureScreenshot();

    return {
        content: [
            {
                type: "text",
                text: `${actionDescription}\n\nCurrent Status:\n${screenshotResponse.status}`,
            },
            {
                type: "image",
                data: screenshotResponse.image,
                mimeType: "image/png",
            },
        ],
    };
}

async function captureScreenshot(): Promise<{ image: string; status: string; statusData: any }> {
    try {
        // Send screenshot command to the web client and wait for response
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            throw new Error("WebSocket connection not available");
        }

        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                cleanup();
                reject(new Error("Screenshot timeout"));
            }, 10000); // Increased timeout to 10 seconds

            let resolved = false;

            const cleanup = () => {
                if (ws && handleMessage) {
                    ws.off('message', handleMessage);
                }
                clearTimeout(timeout);
            };

            const handleMessage = (data: Buffer) => {
                if (resolved) return; // Prevent multiple resolutions

                try {
                    const message = JSON.parse(data.toString());
                    // console.log('MCP Server received message:', message.type);

                    if (message.type === 'screenshot') {
                        resolved = true;
                        cleanup();

                        if (message.error) {
                            reject(new Error(`Screenshot failed: ${message.error}`));
                        } else if (message.data) {
                            resolve({
                                image: message.data,
                                status: message.status || "Status unavailable",
                                statusData: message.statusData || {}
                            });
                        } else {
                            reject(new Error("Screenshot response missing data"));
                        }
                    }
                } catch (error) {
                    // Ignore parsing errors for other messages
                    // console.log('Failed to parse WebSocket message:', error);
                }
            };

            if (ws) {
                ws.on('message', handleMessage);

                // Add a small delay before sending the command to ensure listener is ready
                setTimeout(() => {
                    if (ws && !resolved) {
                        // console.log('MCP Server requesting screenshot...');
                        ws.send(JSON.stringify({ type: "getScreenshot" }));
                    }
                }, 100);
            } else {
                cleanup();
                reject(new Error("WebSocket connection lost"));
            }
        });
    } catch (error) {
        // console.error("Failed to capture screenshot:", error);
        // Return a small transparent pixel as fallback
        return {
            image: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
            status: "Status unavailable",
            statusData: {}
        };
    }
}

async function requestBotStatus(): Promise<any> {
    await ensureConnection();
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        throw new Error("WebSocket connection not available");
    }

    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            cleanup();
            reject(new Error("Bot status timeout"));
        }, 5000);

        const cleanup = () => {
            if (ws && handleMessage) {
                ws.off('message', handleMessage);
            }
            clearTimeout(timeout);
        };

        const handleMessage = (data: Buffer) => {
            try {
                const message = JSON.parse(data.toString());
                if (message.type === 'botStatus') {
                    cleanup();
                    resolve(message.data);
                }
            } catch {
                // ignore
            }
        };

        ws.on('message', handleMessage);
        setTimeout(() => {
            if (ws) {
                ws.send(JSON.stringify({ type: 'getBotStatus' }));
            }
        }, 100);
    });
}

function prettyPrintBotStatus(status: any): string {
    const lines: string[] = [];
    const pos = status.position;
    const rot = status.rotation;
    lines.push(`Position: (${pos.x}, ${pos.y}, ${pos.z}) facing ${rot.cardinalDirection} (${rot.yaw}°, ${rot.pitch}°)`);
    lines.push(`Biome: ${status.biome.displayName}`);
    const time = status.time;
    const minutes = time.timeUntilNext.minutes.toFixed(2);
    lines.push(`Day ${time.day}, ${minutes} minutes until ${time.timeUntilNext.event}`);
    lines.push(`Selected slot: ${status.inventory.currentSlot}`);
    const hotbarItems = status.inventory.hotbarItems;
    if (Object.keys(hotbarItems).length > 0) {
        const itemStrings = Object.entries(hotbarItems).map(([slot, item]: [string, any]) => `[${slot}: ${item.displayName} x${item.count}]`);
        lines.push(`Hotbar: ${itemStrings.join(' ')}`);
    } else {
        lines.push('Hotbar: Empty');
    }
    const entityStates = Object.keys(status.entityState);
    if (entityStates.length > 0) {
        const stateNames = entityStates.map(state => state.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()));
        lines.push(`Status: ${stateNames.join(', ')}`);
    }
    if (status.targetBlock.message) {
        lines.push(`Looking at: ${status.targetBlock.message}`);
    } else {
        const block = status.targetBlock;
        const canDigText = block.canDig ? 'is close enough to dig' : 'cannot dig - too far away';
        lines.push(`Looking at: ${block.displayName} (${canDigText})`);
    }
    return lines.join('\n');
}


server.addTool({
    name: "getBotStatus",
    description: "Get comprehensive information about the bot's current state",
    parameters: z.object({}),
    execute: async () => {
        const status = await requestBotStatus();
        const readable = prettyPrintBotStatus(status);
        return {
            content: [
                {
                    type: "text",
                    text: readable,
                },
            ],
        };
    },
});

// Helper to send a smooth sequence of look commands based on desired angle deltas
async function stepLook(xAngle: number, yAngle: number, speed: "slow" | "normal" | "fast" = "normal") {
    // Approximate pixels required for a single degree of rotation. These values
    // were derived empirically and may need calibration for different setups.
    const SENSITIVITY_X = 5; // yaw sensitivity
    const SENSITIVITY_Y = 5; // pitch sensitivity

    const config = {
        slow: { avgPixelsPerStep: 5, delay: 50 },
        normal: { avgPixelsPerStep: 10, delay: 30 },
        fast: { avgPixelsPerStep: 15, delay: 15 },
    }[speed];

    const totalPixelX = xAngle * SENSITIVITY_X;
    const totalPixelY = -yAngle * SENSITIVITY_Y;  // Invert Y to match pygame controller's coordinate system

    const maxDisplacement = Math.max(Math.abs(totalPixelX), Math.abs(totalPixelY));
    const steps = Math.max(1, Math.ceil(maxDisplacement / config.avgPixelsPerStep));

    // Use exact division instead of easing to eliminate cumulative rounding errors
    const stepX = totalPixelX / steps;  // Exact float division
    const stepY = totalPixelY / steps;  // Exact float division

    for (let i = 0; i < steps; i++) {
        await sendCommand({ type: "look", movementX: stepX, movementY: stepY });
        await new Promise((resolve) => setTimeout(resolve, config.delay));
    }
}

// Utility tools for common combinations
server.addTool({
    name: "walk",
    description: "Walk forward for the duration",
    parameters: z.object({
        duration: z.number().min(100).max(50000).default(1000).describe("Duration in milliseconds"),
    }),
    execute: async (args) => {
        await sendCommand({ type: "move", x: 0, z: -1 });
        await new Promise(resolve => setTimeout(resolve, args.duration));
        await sendCommand({ type: "move", x: 0, z: 0 });

        const screenshotResponse = await captureScreenshot();
        return {
            content: [
                {
                    type: "text",
                    text: `Walked forward for ${args.duration}ms\n\nCurrent Status:\n${screenshotResponse.status}`,
                },
                {
                    type: "image",
                    data: screenshotResponse.image,
                    mimeType: "image/png",
                },
            ],
        };
    },
});

server.addTool({
    name: "lookAngle",
    description: "Smoothly rotate the camera by the given yaw and pitch angles",
    parameters: z.object({
        xAngle: z.number().describe("Yaw delta in degrees (positive = right)"),
        yAngle: z.number().describe("Pitch delta in degrees (positive = down)"),
        speed: z.enum(["slow", "normal", "fast"]).optional().default("normal"),
    }),
    execute: async (args) => {
        await stepLook(args.xAngle, args.yAngle, args.speed);

        const screenshotResponse = await captureScreenshot();
        return {
            content: [
                {
                    type: "text",
                    text: `Looked ${args.xAngle}° yaw and ${args.yAngle}° pitch\n\nCurrent Status:\n${screenshotResponse.status}`,
                },
                {
                    type: "image",
                    data: screenshotResponse.image,
                    mimeType: "image/png",
                },
            ],
        };
    },
});


// Screenshot tool
server.addTool({
    name: "wait",
    description: "Wait for a specified duration",
    parameters: z.object({
        duration: z.number().min(100).max(10000).default(1000).describe("Duration to wait in milliseconds"),
    }),
    execute: async (args) => {
        await new Promise(resolve => setTimeout(resolve, args.duration));
        const screenshotResponse = await captureScreenshot();
        return {
            content: [
                {
                    type: "text",
                    text: `You waited for ${args.duration}ms.\n\nCurrent Status:\n${screenshotResponse.status}`,
                },
                {
                    type: "image",
                    data: screenshotResponse.image,
                    mimeType: "image/png",
                },
            ],
        };
    },
});



server.addTool({
    name: "rightClick",
    description: "Hold right click for a specified duration (useful for actions like eating or using a shield)",
    parameters: z.object({
        duration: z.enum(["very_short","short", "medium", "long", "very_long","very_very_long"]).optional().default("medium").describe("Duration to hold: very_short (100ms), short (500ms), medium (1000ms), long (2000ms), very_long (5000ms), very_very_long (10000ms)"),
    }),
    execute: async (args) => {
        const durationMs = {
            "very_short": 100,
            "short": 500,
            "medium": 1000,
            "long": 2000,
            "very_long": 5000,
            "very_very_long": 10000,
        }[args.duration];

        // Use documentMouseEvent commands (same as working pygame implementation)
        await sendCommand({
            type: "documentMouseEvent",
            button: 2,
            action: "down",
            updateMouse: true
        });
        await new Promise(resolve => setTimeout(resolve, durationMs));
        await sendCommand({
            type: "documentMouseEvent",
            button: 2,
            action: "up",
            updateMouse: false
        });

        const screenshotResponse = await captureScreenshot();
        return {
            content: [
                {
                    type: "text",
                    text: `Right clicked and held for ${args.duration} (${durationMs}ms)\n\nCurrent Status:\n${screenshotResponse.status}`,
                },
                {
                    type: "image",
                    data: screenshotResponse.image,
                    mimeType: "image/png",
                },
            ],
        };
    },
});

server.addTool({
    name: "leftClick",
    description: "Hold left click for a specified duration (useful for actions like breaking blocks or attacking)",
    parameters: z.object({
        duration: z.enum(["very_short","short", "medium", "long", "very_long","very_very_long"]).optional().default("medium").describe("Duration to hold: very_short (100ms), short (500ms), medium (1000ms), long (2000ms), very_long (5000ms), very_very_long (10000ms)"),
    }),
    execute: async (args) => {
        const durationMs = {
            "very_short": 100,
            "short": 500,
            "medium": 1000,
            "long": 2000,
            "very_long": 5000,
            "very_very_long": 10000,
        }[args.duration];

        // Use documentMouseEvent commands (same as working pygame implementation)
        await sendCommand({
            type: "documentMouseEvent",
            button: 0,
            action: "down",
            updateMouse: true
        });
        await new Promise(resolve => setTimeout(resolve, durationMs));
        await sendCommand({
            type: "documentMouseEvent",
            button: 0,
            action: "up",
            updateMouse: false
        });

        const screenshotResponse = await captureScreenshot();
        return {
            content: [
                {
                    type: "text",
                    text: `Left clicked and held for ${args.duration} (${durationMs}ms)\n\nCurrent Status:\n${screenshotResponse.status}`,
                },
                {
                    type: "image",
                    data: screenshotResponse.image,
                    mimeType: "image/png",
                },
            ],
        };
    },
});

server.addTool({
    name: "annotate_3d_position",
    description: "Place a colored marker at the specified world coordinates",
    parameters: z.object({
        worldX: z.number(),
        worldY: z.number(),
        worldZ: z.number(),
        label: z.string().optional(),
        color: z.string().optional(),
        markerId: z.string().optional(),
    }),
    execute: async (args) => {
        await sendCommand({
            type: "annotate_3d_position",
            worldX: args.worldX,
            worldY: args.worldY,
            worldZ: args.worldZ,
            label: args.label || "",
            color: args.color || "red",
            markerId: args.markerId,
        });
        const screenshotResponse = await captureScreenshot();
        return {
            content: [
                {
                    type: "text",
                    text: `Added 3D marker at (${args.worldX}, ${args.worldY}, ${args.worldZ})\n\nCurrent Status:\n${screenshotResponse.status}`,
                },
                {
                    type: "image",
                    data: screenshotResponse.image,
                    mimeType: "image/png",
                },
            ],
        };
    },
});


// Start the server
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 4000;

// Parse command line arguments for transport type
function parseArgs() {
    const args = process.argv.slice(2);
    let transportType: "httpStream" | "stdio" = "stdio"; // default

    for (let i = 0; i < args.length; i++) {
        if (args[i] === "--transport" || args[i] === "-t") {
            const nextArg = args[i + 1];
            if (nextArg === "httpStream" || nextArg === "stdio") {
                transportType = nextArg;
            } else {
                // console.error(`Invalid transport type: ${nextArg}. Use 'httpStream' or 'stdio'.`);
                process.exit(1);
            }
            i++; // Skip the next argument since we consumed it
        } else if (args[i] === "--help" || args[i] === "-h") {
            process.exit(0);
        }
    }

    return { transportType };
}

const { transportType } = parseArgs();

// if (transportType !== "stdio") {
//     console.log(`Starting Minecraft MCP Server with ${transportType} transport...`);
// }

// pnpm mcp-server -- --transport stdio
// pnpm mcp-server 
const startConfig = transportType === "httpStream"
    ? {
        transportType: transportType,
        httpStream: {
            port: PORT,
        },
    }
    : {
        transportType: transportType,
    };

server.start(startConfig).then(() => {
}).catch((error) => {
    // console.error("Failed to start server:", error);
    process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', () => {
    if (ws) {
        ws.close();
    }
    process.exit(0);
}); 