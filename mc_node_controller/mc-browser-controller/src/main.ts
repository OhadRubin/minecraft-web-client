// src/main.ts

import { MinecraftController } from './controller';
import { Server, createToolFunctions } from './mcp-client';
import { MinecraftControllerInterface } from './interface';
import { MCPMessageChain } from './message-chain';
import { McpServerConfig } from './types';

/**
 * Port of mc_pygame_controller/controller.py (main execution block)
 * This is the entry point for the browser application.
 */

class App {
    private controller: MinecraftController | null = null;
    private servers: Server[] = [];
    private interface: MinecraftControllerInterface | null = null;

    constructor() {
        document.addEventListener('DOMContentLoaded', this.init);
    }

    private init = async () => {
        const canvas = document.getElementById('controller-canvas') as HTMLCanvasElement;
        if (!canvas) {
            console.error("Canvas element with id 'controller-canvas' not found.");
            return;
        }

        try {
            // -- Server Configuration --
            // In a real app, this would come from a config file or user input.
            // NOTE: The MCP server must be running and accessible from the browser,
            // with CORS enabled for the client's origin.
            const serverConfigs: McpServerConfig[] = [
                {
                    name: "minecraft-controller-sse",
                    url: "http://localhost:8000", // URL of the MCP server
                }
            ];
            
            this.servers = serverConfigs.map(cfg => new Server(cfg.name, cfg));

            // -- Initialize Servers --
            console.log("🔧 Initializing MCP servers...");
            await Promise.all(this.servers.map(s => s.initialize()));
            console.log("✅ All servers initialized.");

            // -- Create Tools --
            const { toolSchemas, toolMapping } = await createToolFunctions(this.servers);

            // -- Setup Chain and Interface --
            this.interface = new MinecraftControllerInterface('mcp');
            this.interface.toolsMapping = toolMapping;

            const chain = new MCPMessageChain({ verbose: true })
                .withTools(toolSchemas, toolMapping)
                .system(
`You are a *very* ambitious minecraft player.
Your goal is to find and aquire dirt, wood, stone, iron and diamonds. All in your quest to kill the Ender dragon.
Follow Minecraft progression - wood first for tools, then stone, then dig deep for iron and diamonds.
You are autonomous and you can do anything you want.
I suggest making rotations of plus/minus 45 degrees at a time.
Craft wooden tools before trying to mine harder materials like stone or terracotta (remember that they take a while to mine).
Look for surface stone exposures, caves, or ravines rather than digging through hard blocks with bare hands
Don't call multiple tools at once.`
                )
                .clone({ persistentInterface: this.interface }); // Set the interface for the chain

            // -- Setup Controller --
            this.controller = new MinecraftController(canvas, 5.0);
            this.interface.setController(this.controller);
            this.controller.start();
            
            this.interface.startTrajectoryRecording("human_demo_session");
            
            // Add a button to stop recording and download the trajectory
            const stopButton = document.getElementById('stop-recording');
            if (stopButton) {
                stopButton.onclick = () => {
                    if (this.interface) {
                        this.interface.stopTrajectoryRecording();
                    }
                };
            }

        } catch (error) {
            console.error("🔥 Failed to initialize the application:", error);
            // Cleanup servers if initialization fails
            await this.cleanup();
        }
    }

    private async cleanup() {
        console.log("🔧 Cleaning up servers...");
        for (const server of this.servers) {
            await server.cleanup();
        }
    }
}

// Instantiate the app
new App();
