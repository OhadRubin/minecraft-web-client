import { ActionConverter, convert_to_mcp_format } from "./action_converter.js";
import { BrowserFileHandler } from "./porting.js";

// === START_OF: mode_strategy.py
// =======================================================================

// Type definitions
interface Controller {
    mcp_executor?: (command: MCPCommand) => void;
    state: ControllerState;
    send_command_sync: (command: WebSocketCommand) => void;
    start_websocket_connection: () => void;
    action_handler: ActionHandler;
    ui_manager: UIManager;
}

interface ControllerState {
    enable_logging: boolean;
    connected: boolean;
}

interface ActionHandler {
    _log_mcp_command: (actionName: string, params: Record<string, any>) => void;
}

interface UIManager {
    keyboard_movement: KeyboardMovement;
    movement_joystick: MovementJoystick;
}

interface KeyboardMovement {
    handle_keyboard: (keys: { [key: string]: boolean }) => [number, number];
}

interface MovementJoystick {
    knob_x: number;
    knob_y: number;
    center_x: number;
    center_y: number;
    radius: number;
}

interface MCPCommand {
    tool: string;
    parameters: Record<string, any>;
}

interface WebSocketCommand {
    type: string;
    [key: string]: any;
}

interface MCPServer {
    execute_tool: (toolName: string, params: Record<string, any>) => Promise<MCPResponse>;
}

interface MCPResponse {
    content: Array<{
        text?: string;
        data?: string;
    }>;
}

interface MousePosition {
    x: number;
    y: number;
}

abstract class ModeStrategy {
    protected controller: Controller;

    constructor(controller: Controller) {
        this.controller = controller;
    }

    abstract handle_movement(x: number, z: number): void;
    abstract handle_timed_action(
        action_name: string, 
        duration: number, 
        pygame_down_cmd: WebSocketCommand | null, 
        pygame_up_cmd: WebSocketCommand | null, 
        kwargs: Record<string, any>
    ): void;
    abstract handle_toggle_action(action_name: string, state: boolean, pygame_control: string | null): void;
    abstract handle_simple_action(action_name: string, pygame_cmd: WebSocketCommand | null, params?: Record<string, any>): void;
    abstract connect(): void;
    abstract process_continuous_state(mouse_pos: MousePosition, mouse_pressed: boolean, keys_pressed: Set<string>): void;
}

class MCPModeStrategy extends ModeStrategy {
    // A basic implementation for MCP mode, which focuses on converting to MCP format.
    constructor(controller: Controller) {
        super(controller);
        console.log("🔧 MCPModeStrategy: Initializing in MCP mode.");
    }
    
    private _execute(mcp_command: MCPCommand): void {
        if (this.controller.mcp_executor) {
            this.controller.mcp_executor(mcp_command);
        } else if (this.controller.state.enable_logging) {
            console.log(`MCP EXECUTE (no executor): ${JSON.stringify(mcp_command)}`);
        }
    }

    handle_movement(x: number, z: number): void {
        const mcp_command = ActionConverter._convert_move_action({type: 'move', x, z});
        if(mcp_command) this._execute(mcp_command);
    }
    
    handle_timed_action(
        action_name: string, 
        duration: number, 
        pygame_down_cmd: WebSocketCommand | null, 
        pygame_up_cmd: WebSocketCommand | null, 
        kwargs: Record<string, any>
    ): void {
        const params = { duration, ...kwargs };
        const mcp_command = convert_to_mcp_format(action_name, params);
        if (mcp_command) this._execute(mcp_command);
    }

    handle_toggle_action(action_name: string, state: boolean, pygame_control: string | null): void {
        const mcp_command = convert_to_mcp_format(action_name, { state });
        if (mcp_command) this._execute(mcp_command);
    }

    handle_simple_action(action_name: string, pygame_cmd: WebSocketCommand | null, params: Record<string, any> = {}): void {
        const mcp_command = convert_to_mcp_format(action_name, params);
        if (mcp_command) this._execute(mcp_command);
    }
    
    connect(): void {
        console.log("MCP mode does not require a WebSocket connection.");
        this.controller.state.connected = true; // Mark as "connected" conceptually
    }
    
    process_continuous_state(mouse_pos: MousePosition, mouse_pressed: boolean, keys_pressed: Set<string>): void {
        // MCP mode is event-driven, less reliant on continuous state processing.
    }
}

class PygameModeStrategy extends ModeStrategy {
    private was_moving: boolean = false;
    private data_collection_enabled: boolean;
    private mcp_server: MCPServer | null;
    public traceLog: string[] = [];
    private trajectory_id: string;

    constructor(controller: Controller, mcp_server: MCPServer | null, data_collection_enabled: boolean) {
        super(controller);
        this.data_collection_enabled = data_collection_enabled;
        this.mcp_server = mcp_server;
        this.trajectory_id = `trajectory_${Math.floor(Date.now() / 1000)}`;

        if (this.mcp_server && this.data_collection_enabled) {
            console.log("🔧 PygameModeStrategy: Initializing MOCK + OBSERVE mode");
            const logContainer = document.getElementById('data-collection-log-container');
            if (logContainer) {
                logContainer.style.display = 'block';
            }
        } else {
            console.log("🔧 PygameModeStrategy: Initializing in PURE WebSocket mode.");
        }
    }

    handle_movement(x: number, z: number): void {
        const command: WebSocketCommand = { type: "move", x, z };
        this.controller.send_command_sync(command);

        if (this.controller.state.enable_logging && (Math.abs(x) > 0.1 || Math.abs(z) > 0.1)) {
            const magnitude = Math.hypot(x, z);
            const duration = Math.floor(magnitude * ActionConverter.MAGNITUDE_DURATION_SCALE);
            this.controller.action_handler._log_mcp_command("walk", { duration });
        }
    }

    handle_timed_action(
        action_name: string, 
        duration: number, 
        pygame_down_cmd: WebSocketCommand | null, 
        pygame_up_cmd: WebSocketCommand | null, 
        kwargs: Record<string, any>
    ): void {
        const commands_sent: WebSocketCommand[] = [];
        if (pygame_down_cmd) {
            this.controller.send_command_sync(pygame_down_cmd);
            commands_sent.push(pygame_down_cmd);
        }
        if (pygame_up_cmd) {
            this.controller.send_command_sync(pygame_up_cmd);
            commands_sent.push(pygame_up_cmd);
        }

        if (this.data_collection_enabled && this.mcp_server && commands_sent.length > 0) {
            this._queue_parallel_mcp_execution(commands_sent, `Timed Action: ${action_name}`);
        }
        
        const mcp_params = { duration, ...kwargs };
        this.controller.action_handler._log_mcp_command(action_name, mcp_params);
    }
    
    handle_toggle_action(action_name: string, state: boolean, pygame_control: string | null): void {
        if (pygame_control) {
            const command: WebSocketCommand = { type: "control", control: pygame_control, state };
            this.controller.send_command_sync(command);
            if (this.data_collection_enabled && this.mcp_server) {
                this._queue_parallel_mcp_execution([command], `Toggle Action: ${action_name}`);
            }
        }
        this.controller.action_handler._log_mcp_command(action_name, { state });
    }

    handle_simple_action(action_name: string, pygame_cmd: WebSocketCommand | null, params: Record<string, any> = {}): void {
        if (pygame_cmd) {
            this.controller.send_command_sync(pygame_cmd);
            if (this.data_collection_enabled && this.mcp_server) {
                this._queue_parallel_mcp_execution([pygame_cmd], `Simple Action: ${action_name}`);
            }
        }
        this.controller.action_handler._log_mcp_command(action_name, params);
    }

    connect(): void {
        this.controller.start_websocket_connection();
    }
    
    process_continuous_state(mouse_pos: MousePosition, mouse_pressed: boolean, keys_pressed: Set<string>): void {
        // Convert Set<string> to Record<string, boolean>
        const keys_state: { [key: string]: boolean } = {};
        keys_pressed.forEach(key => keys_state[key] = true);
        const keyboard_move = this.controller.ui_manager.keyboard_movement.handle_keyboard(keys_state);
        const joystick = this.controller.ui_manager.movement_joystick;
        const joystick_move: [number, number] = [
            (joystick.knob_x - joystick.center_x) / joystick.radius,
            (joystick.knob_y - joystick.center_y) / joystick.radius
        ];

        let movement_x = 0.0, movement_z = 0.0;
        if (Math.abs(joystick_move[0]) < 0.1 && Math.abs(joystick_move[1]) < 0.1) {
            if (Math.abs(keyboard_move[0]) > 0.1 || Math.abs(keyboard_move[1]) > 0.1) {
                [movement_x, movement_z] = keyboard_move;
            }
        } else {
            [movement_x, movement_z] = joystick_move;
        }

        const is_moving = Math.abs(movement_x) > 0.1 || Math.abs(movement_z) > 0.1;
        
        if (is_moving) {
            const command: WebSocketCommand = { type: "move", x: movement_x, z: movement_z };
            this.controller.send_command_sync(command);
        } else if (this.was_moving) {
             const command: WebSocketCommand = { type: "move", x: 0.0, z: 0.0 };
             this.controller.send_command_sync(command);
        }
        this.was_moving = is_moving;

        if (this.data_collection_enabled) {
            // In the original, this was more complex. Here, we simplify and just
            // queue MCP execution for any significant movement at the end.
            // A more faithful port would require a movement accumulator.
        }
    }
    
    public _queue_parallel_mcp_execution(actions: WebSocketCommand[], task_context: string): void {
        if (!this.data_collection_enabled || !this.mcp_server) return;

        const mcp_actions = ActionConverter.pygame_to_mcp_simple(actions);
        this.logToDom(`🎭 Mock actions: ${mcp_actions.map(a => a.tool).join(', ')}`);
        
        // Use an async IIFE to call the async method from this sync context
        (async () => {
            await this._always_execute_getbotstatus(actions, mcp_actions, task_context);
        })();
    }

    private async _always_execute_getbotstatus(pygame_actions: WebSocketCommand[], mcp_actions: MCPCommand[], task_context: string): Promise<void> {
        try {
            if (!this.mcp_server) return;
            
            const real_response = await this.mcp_server.execute_tool("getBotStatus", {});
            
            const tool_text = real_response.content[0].text || '';
            const base64_string = real_response.content[1].data || '';
            this.logToDom(`📊 getBotStatus result received.`);
            
            BrowserFileHandler.saveScreenshotFile(base64_string, this.trajectory_id, 'getBotStatus');
            
            const trace_data = `====\n` +
                               `Context: ${task_context}\n` +
                               `Observation:\n${tool_text}\n` +
                               `Pygame Actions: ${JSON.stringify(pygame_actions)}\n` +
                               `MCP Actions: ${JSON.stringify(mcp_actions)}\n` +
                               `====\n\n`;

            this.traceLog.push(trace_data);
            this.logToDom("Trace data captured.");

        } catch (e) {
            this.logToDom(`❌ getBotStatus failed: ${e}`, 'error');
            console.error(e);
        }
    }

    private logToDom(message: string, type: 'info' | 'error' = 'info'): void {
        const logArea = document.getElementById('data-collection-log');
        if (!logArea) return;
        
        const entry = document.createElement('div');
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        if (type === 'error') entry.style.color = 'red';
        logArea.appendChild(entry);
        logArea.scrollTop = logArea.scrollHeight;
    }
}

// =======================================================================
export { ModeStrategy, MCPModeStrategy, PygameModeStrategy };
// === END_OF: mode_strategy.py