/**
 * @file controller_base.ts
 * Base class for the Minecraft controller, managing state, strategies, and actions.
 * This is a translation of the Python MinecraftController, adapted for a Node.js/TypeScript environment.
 * Pygame-specific UI and event loop components have been omitted or stubbed, as they
 * would be handled differently in a typical TypeScript application (e.g., web frontend or terminal interface).
 */

import WebSocket from 'ws';
import { ControllerState } from './controller_state';
import { LookPathTracker } from './look_path';
import { ModeStrategy, PygameModeStrategy, MCPModeStrategy } from './mode_strategy';
import { ActionHandler } from './action_handler';
import { convert_to_mcp_format } from './action_converter';
// Constants like WINDOW_WIDTH, FPS are not directly used in this base controller logic without Pygame.
// import { WINDOW_WIDTH, WINDOW_HEIGHT, FPS } from './constants';

// Placeholder for mcp_client.Server until it's properly typed or imported
type McpServerType = any;
type ChainType = any; // Placeholder for chain type
type McpExecutorType = any; // Placeholder for MCP Executor

/**
 * Base class for the Minecraft Controller.
 * Manages game state, interaction strategy (Pygame/WebSocket or MCP),
 * and action handling.
 */
export class MinecraftControllerBase {
    public state: ControllerState;
    public look_path_tracker: LookPathTracker;
    public strategy: ModeStrategy;
    public action_handler: ActionHandler;
    public mcp_server: McpServerType | null = null;

    // Omitted Pygame-specific properties: screen, clock, ui_manager

    /**
     * Initializes the MinecraftControllerBase.
     * @param mode - Operating mode: "pygame" (WebSocket) or "mcp".
     * @param chain_args - Optional arguments for MCP chain [servers, chain].
     * @param sensitivity - Mouse sensitivity.
     * @param enable_logging - Whether to enable detailed logging.
     * @param data_collection_enabled - Whether data collection features are active.
     */
    constructor(
        mode: string = "pygame",
        chain_args: [McpServerType[], ChainType] | null = null,
        sensitivity: number = 5.0,
        enable_logging: boolean = false,
        data_collection_enabled: boolean = false
    ) {
        this.state = new ControllerState(
            mode,
            sensitivity,
            enable_logging,
            data_collection_enabled
        );

        this.look_path_tracker = new LookPathTracker(
            this.state.sensitivity,
            this.state.enable_logging,
            this.state.mode
        );

        if (chain_args) {
            this.state.servers = chain_args[0];
            this.state.chain = chain_args[1];
        } else {
            this.state.servers = [];
            this.state.chain = null;
        }

        if (this.state.mode === "pygame" && this.state.data_collection_enabled) {
            this.mcp_server = this._create_mcp_server_for_data_collection();
        }

        if (this.state.mode === "mcp") {
            this.look_path_tracker.set_execution_callback(
                (cmd: any) => this.execute_mcp_action(cmd)
            );
        } else if (this.state.mode === "pygame" && this.state.data_collection_enabled) {
            this.look_path_tracker.set_execution_callback(
                (cmd: any) => this._execute_pygame_mcp_action(cmd)
            );
        }

        if (this.state.mode === "pygame") {
            this.strategy = new PygameModeStrategy(
                this, // `this` refers to MinecraftControllerBase
                this.mcp_server,
                this.state.data_collection_enabled
            );
        } else if (this.state.mode === "mcp") {
            this.strategy = new MCPModeStrategy(this);
        } else {
            throw new ValueError(`Unknown mode: ${this.state.mode}`);
        }

        this.action_handler = new ActionHandler(this.state, this.strategy, this);

        // Pygame display setup and UIManager initialization are omitted.
        // UI concerns would be handled by a separate frontend system.

        if (this.state.data_collection_enabled) {
            console.log("🎬 Data collection enabled!");
            // Hotkey information would be part of the UI, not logged here directly.
        }
    }

    private _create_mcp_server_for_data_collection(): McpServerType | null {
        // This method would need a TypeScript equivalent of Python's mcp_client.Server.
        // For now, it's a placeholder.
        console.log("🔧 Attempting to create MCP server for data collection (placeholder)...");
        try {
            // const Server = require('some-mcp-client-library').Server; // Example
            // const server_config = { /* ... */ };
            // const server = new Server("minecraft-data-collection", server_config);
            // console.log("🔧 Created MCP server for data collection");
            // return server;
            console.warn("⚠️ _create_mcp_server_for_data_collection is not fully implemented in TypeScript yet.");
            return null;
        } catch (e: any) {
            console.error(`⚠️ Could not create MCP server for data collection: ${e.message}`);
            console.log("💡 Data collection will be disabled");
            this.state.data_collection_enabled = false; // Update state if server creation fails
            return null;
        }
    }

    // Property accessors for state
    get mode(): string { return this.state.mode; }
    get sensitivity(): number { return this.state.sensitivity; }
    get enable_logging(): boolean { return this.state.enable_logging; }
    get running(): boolean { return this.state.running; }
    set running(value: boolean) { this.state.running = value; }
    get connected(): boolean { return this.state.connected; }
    set connected(value: boolean) { this.state.connected = value; }
    // ... other property accessors for ControllerState fields can be added as needed ...
    get mcp_executor(): McpExecutorType | null { return this.state.mcp_executor; }
    set mcp_executor(value: McpExecutorType | null) { this.state.mcp_executor = value; }


    /**
     * Handles camera drag state changes.
     * Adaptation: Original Python code checks `self.ui_manager.camera_area.is_touching`.
     * This UI-specific check needs to be handled by the UI layer in a TS app.
     * For now, we assume `camera_is_clicking` might be determined by other means
     * or this method is called with `is_dragging_camera_area`.
     * @param is_dragging_camera_area - Whether the user is currently dragging within the camera control area.
     */
    public _handle_camera_drag_state(is_dragging_camera_area: boolean): void {
        // TODO: Integrate with actual UI event system for camera drag detection.
        // The original logic relied on a Pygame-specific UIManager.
        const prev_clicking = this.state.camera_was_clicking;

        if (is_dragging_camera_area !== prev_clicking) {
            console.log(`🔍 Camera state change: clicking=${is_dragging_camera_area}, was_clicking=${prev_clicking}`);
        }

        if (is_dragging_camera_area && !prev_clicking) {
            console.log("🖱️ Mouse pressed in camera area - starting drag tracking");
            this.look_path_tracker.start_mouse_tracking();
            this.state.camera_was_clicking = true;
        } else if (!is_dragging_camera_area && prev_clicking) { // Mouse released or drag ended
            console.log("🖱️ Mouse released/drag ended - ending drag tracking");
            this.look_path_tracker.stop_mouse_tracking();
            this.state.camera_was_clicking = false;
        }
    }

    /**
     * Connects to the WebSocket server.
     */
    public async connect_websocket(): Promise<void> {
        try {
            const uri = "ws://localhost:8081"; // Default URI
            console.log(`Connecting to ${uri}...`);

            // Ensure previous websocket is properly closed if any
            if (this.state.websocket && (this.state.websocket.readyState === WebSocket.OPEN || this.state.websocket.readyState === WebSocket.CONNECTING)) {
                 console.log("Closing existing WebSocket connection before reconnecting.");
                 this.state.websocket.close();
            }

            const ws = new WebSocket(uri);
            this.state.websocket = ws; // Store the WebSocket instance

            return new Promise((resolve, reject) => {
                ws.onopen = () => {
                    this.state.connected = true;
                    console.log("Connected to Minecraft Web Client!");
                    const init_message = { init: this.state.mode };
                    ws.send(JSON.stringify(init_message));
                    console.log(`Registered as ${this.state.mode} client`);
                    resolve();
                };

                ws.onmessage = (event) => {
                    // Basic message handling, can be expanded
                    console.log(`Received: ${event.data}`);
                    // TODO: Implement message parsing and dispatch if needed
                };

                ws.onerror = (error) => {
                    console.error(`WebSocket error: ${error.message}`);
                    this.state.connected = false;
                    if (this.state.websocket === ws) { // Avoid issues if a new connection was made quickly
                        this.state.websocket = null;
                    }
                    reject(error);
                };

                ws.onclose = (event) => {
                    console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
                    this.state.connected = false;
                     if (this.state.websocket === ws) {
                        this.state.websocket = null;
                    }
                    // Optionally, implement reconnection logic here
                };
            });

        } catch (e: any) {
            console.error(`Failed to connect: ${e.message}`);
            this.state.connected = false;
            this.state.websocket = null;
            throw e; // Re-throw to allow caller to handle
        }
    }

    /**
     * Initiates the WebSocket connection.
     * In Python, this started a thread. In TS, it's an async operation.
     */
    public async start_websocket_connection(): Promise<void> {
        if (this.state.connected && this.state.websocket?.readyState === WebSocket.OPEN) {
            console.log("WebSocket already connected.");
            return;
        }
        console.log("Starting WebSocket connection process...");
        await this.connect_websocket();
    }

    /**
     * Sends a command over the WebSocket asynchronously.
     * @param command - The command object to send.
     */
    public async send_command_async(command: Record<string, any>): Promise<void> {
        if (this.state.websocket && this.state.connected && this.state.websocket.readyState === WebSocket.OPEN) {
            try {
                this.state.websocket.send(JSON.stringify(command));
                // console.log(`Sent command: ${JSON.stringify(command)}`);
            } catch (e: any) {
                console.error(`Error sending command: ${e.message}`);
                this.state.connected = false; // Assume connection is lost
            }
        } else {
            console.warn("WebSocket not connected or not open. Command not sent:", command);
        }
    }

    /**
     * Sends a command. In Python, this was thread-safe for sync calls from the main thread.
     * In TS/JS, WebSocket sends are inherently async. This method will call `send_command_async`
     * without awaiting, mimicking "fire and forget".
     * @param command - The command object to send.
     */
    public send_command_sync(command: Record<string, any>): void {
        if (!this.state.connected || !this.state.websocket || this.state.websocket.readyState !== WebSocket.OPEN) {
             console.warn("WebSocket not connected for sync send. Command not sent:", command);
             return;
        }
        // Fire and forget
        this.send_command_async(command).catch(error => {
            console.error("Error in fire-and-forget send_command_async:", error);
        });
        // console.log("send_command_sync: Called send_command_async (fire and forget). Command:", command);
    }

    /**
     * Handles control button presses (e.g., jump, sneak, sprint from UI buttons).
     * @param control - The name of the control (e.g., "jump").
     * @param state - The state of the control (true for pressed/active, false for released/inactive).
     */
    public handle_control_button(control: string, state: boolean): void {
        // This method might be redundant if ActionHandler directly handles these.
        // However, if UI elements call this directly:
        const command = { type: "control", control, state };
        this.send_command_sync(command); // Or async if preferred
    }

    /**
     * Executes an MCP-formatted action.
     * @param mcp_command - The MCP command object.
     */
    public execute_mcp_action(mcp_command: any): void {
        if (this.state.mcp_executor) {
            console.log(`🎮 Executing: ${mcp_command.tool}(${JSON.stringify(mcp_command.parameters)})`);
            // Assuming mcp_executor has a method like capture_command or execute
            (this.state.mcp_executor as any).capture_command(mcp_command);
        } else {
            console.log(`🎮 MCP Command (no executor): ${mcp_command.tool}(${JSON.stringify(mcp_command.parameters)})`);
        }
    }

    /**
     * Executes an MCP-formatted action in Pygame data collection mode.
     * This typically involves sending the action to the strategy's mock+observe system.
     * @param mcp_command - The MCP command from LookPathTracker.
     */
    private _execute_pygame_mcp_action(mcp_command: { tool: string; parameters: any }): void {
        console.log(`🎭 Camera drag action for Pygame mock+observe: ${mcp_command.tool}(${JSON.stringify(mcp_command.parameters)})`);
        // Convert to the format expected by PygameModeStrategy._queue_parallel_mcp_execution
        const action = { type: mcp_command.tool, ...mcp_command.parameters };

        if (this.strategy instanceof PygameModeStrategy) {
            // Accessing private method for now, consider refactoring strategy for a public interface
            (this.strategy as any)._queue_parallel_mcp_execution([action], `Camera drag: ${mcp_command.tool}`);
        } else {
            console.warn("_execute_pygame_mcp_action called but strategy is not PygameModeStrategy.");
        }
    }


    /**
     * Sets the MCP command executor.
     * @param executor - The MCP command executor instance.
     */
    public set_mcp_executor(executor: McpExecutorType): void {
        this.state.mcp_executor = executor;
    }

    /**
     * Handles other MCP commands (non-look).
     * @param command_type - The type of command (e.g., "walk", "leftClick").
     * @param params - Parameters for the command.
     */
    public handle_other_commands(command_type: string, params: Record<string, any> = {}): void {
        if (this.state.mode === "mcp" && this.state.mcp_executor) {
            const mcp_command = convert_to_mcp_format(command_type, params);
            if (mcp_command) {
                this.execute_mcp_action(mcp_command);
            }
        }
    }

    /**
     * Processes a single frame of logic.
     * This is a stub, as Pygame event loop, input gathering, and rendering are different in TS.
     * The core logic of processing actions and continuous state is preserved.
     * @param events - External events (e.g., from a UI framework).
     * @param mouse_pos - Current mouse position.
     * @param mouse_pressed - Left mouse button state.
     * @param keys_pressed - Record of pressed keys.
     * @returns True if the controller should continue running, false otherwise.
     */
    public _process_frame(
        events: any[], // Type according to your event system
        mouse_pos: [number, number],
        mouse_pressed: boolean, // Assuming left click
        keys_pressed: Record<string, boolean> // e.g., {'KeyW': true}
    ): boolean {
        // Pygame event handling (pygame.event.get(), pygame.QUIT, pygame.K_ESCAPE) is omitted.
        // Those would be handled by the specific UI framework or input system.
        // Example: if (events.some(e => e.type === 'quit')) this.state.running = false;
        // if (!this.state.running) return false;


        // UIManager processing is omitted. UI actions would come from the UI framework.
        // For this stub, we assume `ui_actions` and `keyboard_actions` might be passed in
        // or generated from `events`, `mouse_pos`, `keys_pressed`.
        const ui_actions: [string, any][] = []; // Placeholder
        const keyboard_actions: [string, any][] = []; // Placeholder
        const event_actions: [string, any][] = []; // Placeholder for actions derived from `events`

        this.action_handler.process_actions(
            [...event_actions, ...ui_actions, ...keyboard_actions]
        );

        this._process_continuous_state(mouse_pos, mouse_pressed, keys_pressed);
        this.action_handler.process_edge_detections(keys_pressed);

        // UIManager update and draw are omitted.
        return this.state.running;
    }

    private _process_continuous_state(
        mouse_pos: [number, number],
        mouse_pressed: boolean, // Assuming left click
        keys_pressed: Record<string, boolean>
    ): void {
        // TODO: Adapt mouse_pressed to be an array or object if more buttons are needed.
        this.strategy.process_continuous_state(mouse_pos, [mouse_pressed, false, false], keys_pressed);
    }

    /**
     * Main run loop for the controller.
     * This is heavily adapted. In Python, it started the Pygame loop.
     * In TS, this would connect and then expect an external system to call `_process_frame` or similar.
     */
    public async run(): Promise<void> {
        console.log(`Starting Minecraft Controller in ${this.state.mode.toUpperCase()} mode...`);
        await this.strategy.connect(); // Connects WebSocket if in Pygame mode

        if (this.state.data_collection_enabled && this.strategy instanceof PygameModeStrategy) {
            // In Python, this started a background init. Here, async init is part of strategy.
            console.log("🔧 Data collection: PygameModeStrategy will handle its async init if needed.");
            // The PygameModeStrategy's connect or a dedicated method might handle async setup.
             if (this.mcp_server && typeof (this.mcp_server as any).initialize === 'function') {
                console.log("🔧 Initializing MCP server in main async context (like MCP mode)...");
                try {
                    await (this.mcp_server as any).initialize();
                    console.log("✅ MCP server initialized successfully");
                    await this.test_get_bot_status_pygame_startup();
                } catch (e: any) {
                    console.error(`❌ MCP server initialization failed: ${e.message}`);
                    console.log("💡 Data collection will be disabled for this session");
                    this.state.data_collection_enabled = false;
                }
            }
            await this.strategy.start_async_execution?.(); // Call if exists
        }


        if (this.state.mode === "pygame") {
            console.log("Commands will be forwarded to the Minecraft bot via WebSocket.");
            console.log("Make sure the Minecraft web client server is running on localhost:8081");
        } else { // MCP Mode
            console.log("Commands will be converted to MCP format.");
            console.log("MCP mode requires an external system to drive it (e.g., handle_interactive_session).");
        }

        // The traditional Pygame while loop is omitted.
        // A TS application would have its own main loop (e.g., requestAnimationFrame in browser,
        // or a loop in a Node.js server/CLI application) that would periodically call
        // a method like `_process_frame` with current inputs.
        console.log("Controller initialized. Ready for external event loop to call _process_frame() or animation_loop().");
    }

    /**
     * An example animation loop for async modes, if not using a Pygame-like structure.
     * This would be driven by an external caller.
     * @param getInputState - A function that returns the current input state
     *                        (events, mouse_pos, mouse_pressed, keys_pressed).
     */
    public async animation_loop(getInputState: () => {
        events: any[],
        mouse_pos: [number, number],
        mouse_pressed: boolean,
        keys_pressed: Record<string, boolean>
    }): Promise<void> {
        if (!this.state.running) return;

        const { events, mouse_pos, mouse_pressed, keys_pressed } = getInputState();
        if (!this._process_frame(events, mouse_pos, mouse_pressed, keys_pressed)) {
            // Stop condition met
            return;
        }
        // In a browser, requestAnimationFrame would be used. In Node, a simple timeout.
        // This is just for demonstration if an external loop is not available.
        // await new Promise(resolve => setTimeout(resolve, 1000 / (FPS || 60) ));
        // Call this method repeatedly from your actual application loop.
    }

    /**
     * Tests getBotStatus at startup for Pygame mode with data collection.
     */
    public async test_get_bot_status_pygame_startup(): Promise<void> {
        if (!this.mcp_server || !this.state.data_collection_enabled) return;
        try {
            console.log("🧪 Testing getBotStatus at startup (pygame data collection mode)...");
            // Assuming mcp_server has an execute_tool method
            const result = await (this.mcp_server as any).execute_tool("getBotStatus", {});
            const text = result?.content?.[0]?.text || "No text content from getBotStatus";
            console.log(`📊 Pygame startup getBotStatus result: \n====\n${text}\n====\n`);
        } catch (e: any) {
            console.error(`❌ Pygame startup getBotStatus failed: ${e.message}`);
            console.log("💡 This may indicate MCP server connectivity issues");
        }
    }

    /**
     * Tests getBotStatus at startup using the chain.
     * @param chain - The chain instance with tools_mapping.
     */
    public async test_get_bot_status_startup(chain: ChainType): Promise<void> {
        if (!chain || !chain.tools_mapping || !chain.tools_mapping["getBotStatus"]) {
            console.warn("Chain or getBotStatus tool not available for startup test.");
            return;
        }
        try {
            console.log("🧪 Testing getBotStatus at startup via chain...");
            const result = await chain.tools_mapping["getBotStatus"]();
            const text = result?.content?.[0]?.text || "No text content from getBotStatus";
            console.log(`📊 Startup getBotStatus result: \n====\n${text}\n====\n`);
        } catch (e: any) {
            console.error(`❌ Startup getBotStatus failed: ${e.message}`);
        }
    }

    // execute_mcp_command_async and related queue logic is omitted as it depends on
    // a specific async execution model (like Python's asyncio.Queue) which would
    // need to be re-implemented based on application needs (e.g., using Promises or an async queue library).

    /**
     * Handles a test status request, typically from a UI button.
     */
    public handle_test_status(): void {
        if (this.state.mode === "mcp" && this.state.chain) {
            console.log("🧪 Manual getBotStatus test triggered!");
            this._trigger_get_bot_status().catch(e => console.error("Error in _trigger_get_bot_status:", e));
        } else {
            console.warn("⚠️ getBotStatus test only available in MCP mode with a valid chain.");
        }
    }

    private async _trigger_get_bot_status(): Promise<void> {
        if (!this.state.chain || !this.state.chain.tools_mapping || !this.state.chain.tools_mapping["getBotStatus"]) {
            console.error("❌ Cannot trigger getBotStatus: chain or tool not available.");
            return;
        }
        try {
            const result = await this.state.chain.tools_mapping["getBotStatus"]();
            console.log(`🎯 Manual getBotStatus result: ${JSON.stringify(result)}`);
        } catch (e: any) {
            console.error(`❌ Manual getBotStatus failed: ${e.message}`);
        }
    }

    /**
     * Handles saving a demonstration step.
     */
    public handle_save_demonstration(): void {
        if (this.state.mode === "mcp" && this.state.mcp_executor) {
            console.log("💾 Saving demonstration step...");
            const user_context = "exploring and performing actions"; // Example context
            // Assuming mcp_executor has save_demonstration_step
            const success = (this.state.mcp_executor as any).save_demonstration_step(user_context);
            if (success) {
                console.log("✅ Demonstration step saved successfully!");
            } else {
                console.warn("⚠️ No actions to save in this step");
            }
        } else {
            console.warn("⚠️ Demonstration saving only available in MCP mode with an MCP executor.");
        }
    }

    /**
     * Cleans up resources, like closing WebSocket connection or stopping MCP server.
     */
    public async cleanup(): Promise<void> {
        console.log("Cleaning up MinecraftControllerBase...");
        this.state.running = false;

        if (this.state.websocket && this.state.websocket.readyState === WebSocket.OPEN) {
            this.state.websocket.close();
            console.log("WebSocket connection closed.");
        }

        if (this.strategy && typeof (this.strategy as any).stop_async_execution === 'function') {
            await (this.strategy as any).stop_async_execution();
        }

        if (this.mcp_server && typeof (this.mcp_server as any).cleanup === 'function') {
            try {
                await (this.mcp_server as any).cleanup();
                console.log("✅ MCP server cleaned up");
            } catch (e: any) {
                console.error(`⚠️ Warning during MCP server cleanup: ${e.message}`);
            }
        }
        console.log("MinecraftControllerBase cleanup complete.");
    }
}

/**
 * Custom Error class for signaling value errors.
 */
class ValueError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "ValueError";
    }
}
