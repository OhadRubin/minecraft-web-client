/**
 * @file mode_strategy.ts
 * Implements the Strategy Pattern for handling different controller modes (Pygame, MCP)
 * in the MinecraftController. This helps to separate mode-specific logic.
 */

import * as fs from 'fs';
import * as path from 'path';
import { ActionConverter, convert_to_mcp_format } from './action_converter'; // Assuming action_converter.ts is in the same directory
import type { ControllerState } from './controller_state'; // Assuming controller_state.ts
import { MCPClient } from '../../mcp-client/src/MCPClient.js'; // Adjusted path

// Placeholders for types that will be defined elsewhere or imported from libraries
type MinecraftControllerBase = any; // Placeholder for the main controller class
// type Server = any; // Placeholder for MCP Server type - Replaced by MCPClient
type PygameMCPAsyncMessageChain = any; // Placeholder
type McpAction = { tool: string; parameters: Record<string, any> }; // From action_converter.ts

/**
 * Saves a base64 encoded screenshot to a file.
 * @param base64_data - The base64 encoded image data.
 * @param session_id - The ID of the current session, used for subdirectories.
 * @param tool_name - The name of the tool or action that generated the screenshot.
 * @returns The filename of the saved screenshot.
 */
export function save_screenshot_file(base64_data: string, session_id: string, tool_name: string): string {
    const screenshotsDir = path.join("screenshots", session_id);
    if (!fs.existsSync(screenshotsDir)) {
        fs.mkdirSync(screenshotsDir, { recursive: true });
    }
    const filename = `${Date.now()}_${tool_name}.png`;
    const filepath = path.join(screenshotsDir, filename);

    fs.writeFileSync(filepath, Buffer.from(base64_data, 'base64'));
    return filename;
}

/**
 * Extracts text parts from a multimodal output structure.
 * @param output - The multimodal output object.
 * @returns Concatenated string of all text parts.
 */
export function get_text_from_multimodal_output(output: any): string {
    if (output && output.multimodal_content && Array.isArray(output.multimodal_content)) {
        const text_parts = output.multimodal_content
            .filter((item: any) => item && item.type === "text" && typeof item.text === 'string')
            .map((item: any) => item.text);
        return text_parts.join(" ");
    }
    return "";
}

/**
 * Abstract base class for controller mode strategies.
 * Defines the interface for handling actions and state in different modes.
 */
export abstract class ModeStrategy {
    protected controller: MinecraftControllerBase;

    /**
     * Initializes with a reference to the main controller.
     * @param controller - The instance of MinecraftControllerBase.
     */
    constructor(controller: MinecraftControllerBase) {
        this.controller = controller;
    }

    /** Handles movement commands (e.g., walking, strafing). */
    abstract handle_movement(x: number, z: number): void;

    /**
     * Handles timed actions (e.g., clicks, jump) which have a duration.
     * @param action_name - Name of the action (e.g., "leftClick", "jump").
     * @param duration - Duration of the action (e.g., "short", "medium", "long").
     * @param pygame_down_cmd - Optional Pygame-like command for key/button press.
     * @param pygame_up_cmd - Optional Pygame-like command for key/button release.
     * @param kwargs - Additional parameters for the action.
     */
    abstract handle_timed_action(
        action_name: string,
        duration: string,
        pygame_down_cmd?: Record<string, any>,
        pygame_up_cmd?: Record<string, any>,
        kwargs?: Record<string, any>
    ): void;

    /**
     * Handles toggle actions (e.g., sneak, sprint) which have an on/off state.
     * @param action_name - Name of the action (e.g., "sneak", "sprint").
     * @param state - The desired state (true for on, false for off).
     * @param pygame_control - Optional Pygame-like control string.
     */
    abstract handle_toggle_action(action_name: string, state: boolean, pygame_control?: string): void;

    /**
     * Handles simple one-shot actions (e.g., drop item, swap hands, toggle inventory).
     * @param action_name - Name of the action.
     * @param pygame_cmd - Optional Pygame-like command.
     * @param params - Additional parameters for the action.
     */
    abstract handle_simple_action(action_name: string, pygame_cmd?: Record<string, any>, params?: Record<string, any>): void;

    /** Initializes any connections or setup required for this mode. */
    abstract connect(): void;

    /**
     * Processes continuous state updates, like mouse position and held keys/buttons.
     * @param mouse_pos - Current mouse position [x, y].
     * @param mouse_pressed - Array indicating mouse button states [left, middle, right].
     * @param keys_pressed - Object or Map indicating pressed keyboard keys.
     */
    abstract process_continuous_state(mouse_pos: [number, number], mouse_pressed: boolean[], keys_pressed: any): void;

    /** Optional: Start asynchronous operations, if any, for this mode. */
    async start_async_execution(): Promise<boolean> { return true; }

    /** Optional: Stop asynchronous operations and clean up resources. */
    async stop_async_execution(): Promise<boolean> { return true; }
}

/**
 * Strategy for "Pygame mode," which primarily sends WebSocket commands to a Minecraft client
 * and can optionally operate in a "mock + observe" mode for data collection with an MCP server.
 */
export class PygameModeStrategy extends ModeStrategy {
    private was_moving: boolean = false;
    private trajectories_dir: string;
    private current_dir: string;
    private images_dir: string;
    private mcp_server: MCPClient | null;
    private data_collection_enabled: boolean;
    private _mcp_action_queue: McpAction[] = []; // For compatibility/logging
    private _active_tasks: Set<Promise<any>> = new Set(); // For tracking async getBotStatus tasks
    private movement_start_time: number = 0;
    private movement_accumulator: { total_distance: number; last_pos: [number, number] } | null = null;


    constructor(controller: MinecraftControllerBase, mcp_server: MCPClient | null = null, data_collection_enabled: boolean = false) {
        super(controller);

        this.trajectories_dir = "trajectories";
        const timestamp = Math.floor(Date.now() / 1000);
        this.current_dir = path.join(this.trajectories_dir, `trajectory_${timestamp}`);
        this.images_dir = path.join(this.current_dir, "images");

        [this.trajectories_dir, this.current_dir, this.images_dir].forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        });

        if (mcp_server && data_collection_enabled) {
            console.log("🔧 PygameModeStrategy: Initializing MOCK + OBSERVE mode");
            console.log("🎭 Actions will be mocked, only getBotStatus executed for real observation");
            this.mcp_server = mcp_server;
            this.data_collection_enabled = true;
        } else {
            console.log("🔧 PygameModeStrategy: Initializing in PURE WebSocket mode.");
            this.mcp_server = null;
            this.data_collection_enabled = false;
        }
        console.log(`🔧 PygameModeStrategy: Mode=${this.data_collection_enabled ? 'MOCK+OBSERVE' : 'PURE'}, Server=${this.mcp_server ? '✅' : '❌'}, Data Collection=${this.data_collection_enabled ? '✅' : '❌'}`);
    }

    handle_movement(x: number, z: number): void {
        const command = { type: "move", x, z };
        this.controller.send_command_sync(command); // Assuming controller has send_command_sync

        if (this.controller.enable_logging && (Math.abs(x) > 0.1 || Math.abs(z) > 0.1)) {
            const magnitude = Math.sqrt(x ** 2 + z ** 2);
            const duration = Math.round(magnitude * 2000); // Scale to reasonable duration
            this.controller.action_handler._log_mcp_command("walk", { duration });
        }
    }

    handle_timed_action(action_name: string, duration: string, pygame_down_cmd?: Record<string, any>, pygame_up_cmd?: Record<string, any>, kwargs: Record<string, any> = {}): void {
        const commands_sent: Record<string, any>[] = [];
        if (pygame_down_cmd) {
            this.controller.send_command_sync(pygame_down_cmd);
            commands_sent.push(pygame_down_cmd);
        }
        if (pygame_up_cmd) {
            this.controller.send_command_sync(pygame_up_cmd);
            commands_sent.push(pygame_up_cmd);
        }

        if (this.data_collection_enabled && this.mcp_server && commands_sent.length > 0) {
            const task_context = this.controller.state?.current_task_description || "";
            this._queue_parallel_mcp_execution(commands_sent, task_context);
        }
        const mcp_params = { duration, ...kwargs };
        this.controller.action_handler._log_mcp_command(action_name, mcp_params);
    }

    handle_toggle_action(action_name: string, state: boolean, pygame_control?: string): void {
        let command_sent: Record<string, any> | null = null;
        if (pygame_control) {
            const command = { type: "control", control: pygame_control, state };
            this.controller.send_command_sync(command);
            command_sent = command;
        }

        if (this.data_collection_enabled && this.mcp_server && command_sent) {
            const task_context = this.controller.state?.current_task_description || "";
            this._queue_parallel_mcp_execution([command_sent], task_context);
        }
        this.controller.action_handler._log_mcp_command(action_name, { state });
    }

    handle_simple_action(action_name: string, pygame_cmd?: Record<string, any>, params: Record<string, any> = {}): void {
        if (pygame_cmd) {
            this.controller.send_command_sync(pygame_cmd);
            if (this.data_collection_enabled && this.mcp_server) {
                const task_context = this.controller.state?.current_task_description || "";
                this._queue_parallel_mcp_execution([pygame_cmd], task_context);
            }
        }
        this.controller.action_handler._log_mcp_command(action_name, params);
    }

    connect(): void {
        this.controller.start_websocket_connection(); // Assuming controller has this method
    }

    process_continuous_state(mouse_pos: [number, number], mouse_pressed: boolean[], keys_pressed: any): void {
        // This method needs significant adaptation. The Python version relies on
        // `self.controller.ui_manager.keyboard_movement.handle_keyboard(keys_pressed)`
        // and joystick logic. For now, we'll assume movement_x and movement_z are derived
        // or defaulted. This part will need to be connected to the actual UI event system.

        let movement_x = 0; // Placeholder - should come from keyboard/joystick state
        let movement_z = 0; // Placeholder

        // Example: If your controller has a way to get keyboard/joystick state:
        // const keyboard_input = this.controller.get_keyboard_input(keys_pressed);
        // const joystick_input = this.controller.get_joystick_input();
        // movement_x = joystick_input.x || keyboard_input.x;
        // movement_z = joystick_input.z || keyboard_input.z;


        const is_moving = Math.abs(movement_x) > 0.1 || Math.abs(movement_z) > 0.1;

        if (is_moving && !this.was_moving) {
            console.log("🚶‍♂️ Movement started - beginning walk tracking");
            this.movement_start_time = Date.now();
            this.movement_accumulator = { total_distance: 0.0, last_pos: [movement_x, movement_z] };
        }

        if (is_moving) {
            this.handle_movement(movement_x, movement_z); // Send continuous movement
            if (this.movement_accumulator) {
                const [last_x, last_z] = this.movement_accumulator.last_pos;
                const distance = Math.sqrt((movement_x - last_x) ** 2 + (movement_z - last_z) ** 2);
                this.movement_accumulator.total_distance += distance;
                this.movement_accumulator.last_pos = [movement_x, movement_z];
            }
        } else if (this.was_moving && !is_moving) {
            console.log("🚶‍♂️ Movement ended - summarizing walk action");
            this.handle_movement(0, 0); // Send stop command

            if (this.data_collection_enabled && this.movement_accumulator) {
                const duration = Date.now() - this.movement_start_time;
                const distance = this.movement_accumulator.total_distance;
                const [last_x, last_z] = this.movement_accumulator.last_pos;
                const summarized_command: Record<string, any> = {
                    type: "move", x: last_x, z: last_z, duration, distance
                };
                console.log(`📊 Walk summary: direction=(${last_x.toFixed(2)}, ${last_z.toFixed(2)}), distance=${distance.toFixed(2)}, duration=${duration}ms`);
                const task_context = this.controller.state?.current_task_description || "";
                this._queue_parallel_mcp_execution([summarized_command], task_context);
            }
            this.movement_accumulator = null;
        }
        this.was_moving = is_moving;

        // Continuous button holds
        const controllerState = this.controller.state as ControllerState | undefined;
        if (controllerState?.action_states["left_click"]?.active) {
            this.controller.send_command_sync({
                type: "documentMouseEvent", button: 0, action: "down", updateMouse: true
            });
        }
        if (controllerState?.action_states["right_click"]?.active) {
            this.controller.send_command_sync({ type: "rightDown" });
        }
    }

    async initialize_async_components(): Promise<boolean> {
        if (this.data_collection_enabled) {
            console.log("✅ Mock+observe data collection mode initialized");
            console.log("🎭 Actions will be mocked, getBotStatus will be executed for real observation");
        }
        return true;
    }

    async cleanup_async_components(): Promise<boolean> {
        if (this.data_collection_enabled) {
            const remaining_tasks = this._active_tasks.size;
            if (remaining_tasks > 0) {
                console.log(`🧹 Cancelling ${remaining_tasks} remaining getBotStatus tasks`);
                // Cancellation in JS/TS for promises is not direct like Python's asyncio.tasks.
                // This would depend on how tasks are structured (e.g., AbortController).
                // For now, we just clear the set. Proper cancellation would need more infrastructure.
                this._active_tasks.clear();
            }
            console.log("✅ Mock+observe data collection mode cleaned up");
        }
        return true;
    }

    private _queue_parallel_mcp_execution(actions: any[], task_context: string = ""): void {
        if (!this.data_collection_enabled || !this.mcp_server) {
            return;
        }
        const mcp_actions = ActionConverter.pygame_to_mcp_simple(actions);
        console.log(`🎭 Mock actions: ${mcp_actions.map(a => a.tool).join(', ')}`);

        const task = this._always_execute_getbotstatus(actions, mcp_actions, task_context)
            .finally(() => {
                this._active_tasks.delete(task);
            });
        this._active_tasks.add(task);
    }

    private async _always_execute_getbotstatus(pygame_actions: any[], mcp_actions: McpAction[], task_context: string): Promise<void> {
        if (!this.mcp_server) {
            console.error("❌ MCP Server is not available for getBotStatus.");
            return;
        }
        try {
            // Assuming this.mcp_server.execute_tool returns a promise
            const real_response = await (this.mcp_server as MCPClient).callTool({ name: "getBotStatus", arguments: {} });

            // Ensure real_response and its content are valid before accessing
            if (!real_response || !real_response.content || real_response.content.length < 2) {
                console.error("❌ getBotStatus response is invalid:", real_response);
                return;
            }

            const tool_text = real_response.content[0]?.text || "No text content";
            const base64_string = real_response.content[1]?.data;

            if (!base64_string) {
                 console.error("❌ getBotStatus response missing screenshot data.");
                 // still log text if available
                 if(tool_text !== "No text content") {
                    console.log(`📊 RUNTIME getBotStatus result (text only):\n====\n${tool_text}\n====\n\n`);
                 }
                 return;
            }
            console.log(`📊 RUNTIME getBotStatus result:\n====\n${tool_text}\n====\n\n`);


            const timestamp = Date.now();
            const screenshot_filename = `${timestamp}_screenshot.png`;
            const screenshot_path = path.join(this.images_dir, screenshot_filename);
            fs.writeFileSync(screenshot_path, Buffer.from(base64_string, 'base64'));

            const latest_screenshot_path = "latest_screenshot.png"; // At project root or a configured path
            fs.writeFileSync(latest_screenshot_path, Buffer.from(base64_string, 'base64'));

            let trace_data = `📊 RUNTIME getBotStatus result:\n====\n${tool_text}\n====\n\n`;
            trace_data += `📊 pygame_actions: ${JSON.stringify(pygame_actions)}\n`;
            trace_data += `📊 mcp_actions: ${JSON.stringify(mcp_actions)}\n\n`;

            const trace_file_path = path.join(this.current_dir, "trace.txt");
            if (!fs.existsSync(trace_file_path)) {
                console.log(`Creating trace file at ${trace_file_path}`);
            }
            fs.appendFileSync(trace_file_path, trace_data);

            console.log(`📊 pygame_actions: ${JSON.stringify(pygame_actions)}`);
            console.log(`📊 mcp_actions: ${JSON.stringify(mcp_actions)}`);

        } catch (e: any) {
            console.error(`❌ getBotStatus failed: ${e.message}`, e);
        }
    }
}

/**
 * Strategy for "MCP mode," which converts all actions into MCP (Minecraft Control Protocol)
 * tool calls to be sent to an MCP server.
 */
export class MCPModeStrategy extends ModeStrategy {
    constructor(controller: MinecraftControllerBase) {
        super(controller);
    }

    handle_movement(x: number, z: number): void {
        // Assumes controller.last_moved_in_mcp_mode exists and is a timestamp
        if (Date.now() - (this.controller.state?.last_moved_in_mcp_mode || 0) > 2000) {
            // const magnitude = Math.sqrt(x ** 2 + z ** 2);
            // Duration can be fixed or calculated based on magnitude
            this.handle_simple_action("walk", undefined, { duration: 1000 });
            if (this.controller.state) {
                 this.controller.state.last_moved_in_mcp_mode = Date.now();
            }
        }
    }

    handle_timed_action(action_name: string, duration: string, pygame_down_cmd?: Record<string, any>, pygame_up_cmd?: Record<string, any>, kwargs: Record<string, any> = {}): void {
        // pygame_down_cmd and pygame_up_cmd are ignored in MCP mode
        const params = { duration, ...kwargs };
        // Assumes controller.handle_other_commands exists
        this.controller.handle_other_commands(action_name, params);
    }

    handle_toggle_action(action_name: string, state: boolean, pygame_control?: string): void {
        // pygame_control is ignored in MCP mode
        this.controller.handle_other_commands(action_name, { state });
    }

    handle_simple_action(action_name: string, pygame_cmd?: Record<string, any>, params: Record<string, any> = {}): void {
        // pygame_cmd is ignored in MCP mode
        this.controller.handle_other_commands(action_name, params);
    }

    connect(): void {
        console.log("MCP mode ready. No WebSocket connection needed.");
    }

    process_continuous_state(mouse_pos: [number, number], mouse_pressed: boolean[], keys_pressed: any): void {
        // MCP mode generally relies on discrete actions rather than continuous state streaming.
        // This method can be left empty or used for specific MCP continuous interactions if any.
    }
}
