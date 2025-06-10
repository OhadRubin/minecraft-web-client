import * as fs from 'fs';
import * as path from 'path';

// --- INTERFACE DEFINITIONS ---

export interface Controller {
  send_command_sync(command: Record<string, any>): void;
  enable_logging: boolean;
  action_handler: {
    _log_mcp_command(action_name: string, params: Record<string, any>): void;
  };
  state: {
    action_states: { [key: string]: boolean }; // e.g., left_click_held
    player_pos?: [number, number]; // Optional, for movement accumulation
    [key: string]: any; // For other potential state properties
  };
  ui_manager: {
    keyboard_movement: boolean;
    movement_joystick?: { // Assuming joystick might be optional
      get_axis(index: number): number;
    };
    [key: string]: any; // For other potential ui_manager properties
  };
  start_websocket_connection(): void;
  handle_other_commands(action_name: string, params: Record<string, any>): void;
  last_moved_in_mcp_mode: number;
  session_id: string; // Used in PygameModeStrategy
  current_task_description?: string; // Potentially used for logging context
}

export interface ServerExecuteToolResponse {
  multimodal_content?: Array<{ // Made optional as per Python hint (None)
    type: string;
    text?: string;
    image_base64?: string; // For screenshots
    [key: string]: any; 
  }>;
  // Other potential fields from a tool execution
  [key: string]: any;
}


export interface Server {
  execute_tool(tool_name: string, ...args: any[]): Promise<ServerExecuteToolResponse>;
}

export interface PygameMCPAsyncMessageChain {
  // Basic interface, to be expanded later if needed
  // Based on its name, it likely processes messages and returns promises
  process_message(message: any): Promise<any>; 
}

export interface MousePos {
  x: number;
  y: number;
}

export interface MousePressed {
  [button: number]: boolean; // e.g., 0 for left, 1 for middle, 2 for right
                            // Or could be { left: boolean, right: boolean ... }
                            // Using number index for flexibility as in original `mouse_pressed[0]`
}

export interface KeysPressed {
  [key: string]: boolean; // e.g., keys_pressed.w, keys_pressed.a
}

export interface MovementAccumulator {
  total_distance: number;
  last_pos: [number, number];
}

export interface MultimodalOutput {
  multimodal_content: Array<{
    type: string;
    text?: string;
    [key: string]: any; // Allow other properties like image_base64
  }>;
}

// --- UTILITY FUNCTIONS ---

export function save_screenshot_file(base64_data: string, session_id: string, tool_name: string): string {
  const screenshotsDir = path.join('screenshots', session_id);
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  // Return only the filename, not the full path
  const filename = `${timestamp}_${tool_name}.png`;
  const filepath = path.join(screenshotsDir, filename);

  const buffer = Buffer.from(base64_data, 'base64');
  fs.writeFileSync(filepath, buffer);

  return filename; // Changed to return filename only
}

export function get_text_from_multimodal_output(output: MultimodalOutput): string {
  let text = '';
  if (output && output.multimodal_content && Array.isArray(output.multimodal_content)) {
    for (const part of output.multimodal_content) {
      if (part.type === 'text' && part.text) {
        text += part.text;
      }
    }
  }
  return text;
}

// --- ABSTRACT CLASS FOR CONTROL MODE STRATEGY ---

export abstract class ModeStrategy {
  protected controller: Controller;

  constructor(controller: Controller) {
    this.controller = controller;
  }

  abstract handle_movement(x: number, z: number): void;
  abstract handle_timed_action(action_name: string, duration: string, pygame_down_cmd?: Record<string, any>, pygame_up_cmd?: Record<string, any>, ...kwargs: any[]): void;
  abstract handle_toggle_action(action_name: string, state: boolean, pygame_control?: string): void;
  abstract handle_simple_action(action_name: string, pygame_cmd?: Record<string, any>, params?: Record<string, any>): void;
  abstract connect(): void;
  abstract process_continuous_state(mouse_pos: MousePos, mouse_pressed: MousePressed, keys_pressed: KeysPressed): void;
}

// --- PYGAME MODE STRATEGY IMPLEMENTATION ---

export class PygameModeStrategy extends ModeStrategy {
  private was_moving: boolean = false;
  private trajectories_dir: string;
  public current_dir: string;
  private images_dir: string;
  private mcp_server?: Server;
  private data_collection_enabled: boolean;
  private _mcp_action_queue: Record<string, any>[] = [];
  private _active_tasks: Set<Promise<any>> = new Set();
  
  private movement_start_time: number = 0;
  private movement_accumulator?: MovementAccumulator;

  constructor(controller: Controller, mcp_server?: Server, data_collection_enabled: boolean = false) {
    super(controller);
    this.mcp_server = mcp_server;
    this.data_collection_enabled = data_collection_enabled;

    this.trajectories_dir = "trajectories";
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    this.current_dir = path.join(this.trajectories_dir, `trajectory_${timestamp}`);
    this.images_dir = path.join(this.current_dir, "images");

    if (this.data_collection_enabled) {
        fs.mkdirSync(this.images_dir, { recursive: true });
        console.log(`[PygameModeStrategy] Data collection enabled. Saving trajectories to: ${this.current_dir}`);
    } else {
        console.log("[PygameModeStrategy] Data collection disabled.");
    }
    
    console.log(`[PygameModeStrategy] Initialized for session: ${this.controller.session_id}`);
  }

  handle_movement(x: number, z: number): void {
    const command = { action: "move", x, z };
    this.controller.send_command_sync(command);

    if (this.controller.enable_logging) {
        if (x !== 0 || z !== 0) {
            if (!this.was_moving) {
                this.controller.action_handler._log_mcp_command("walk", { direction: { x, z } });
                this.was_moving = true;
            }
        } else {
            if (this.was_moving) {
                this.controller.action_handler._log_mcp_command("stop_walk", {});
                this.was_moving = false;
            }
        }
    }
  }

  handle_timed_action(action_name: string, duration: string, pygame_down_cmd?: Record<string, any>, pygame_up_cmd?: Record<string, any>, ...kwargs: any[]): void {
    if (pygame_down_cmd) {
      this.controller.send_command_sync(pygame_down_cmd);
    }
    if (pygame_up_cmd) {
      this.controller.send_command_sync(pygame_up_cmd);
    }
    
    const mcp_args = { duration, ...Object.assign({}, ...kwargs) };
    if (this.controller.enable_logging) {
      this.controller.action_handler._log_mcp_command(action_name, mcp_args);
    }

    if (this.data_collection_enabled && this.mcp_server) {
        const actions: Record<string, any>[] = [];
        if (pygame_down_cmd) actions.push(pygame_down_cmd);
        if (pygame_up_cmd) actions.push(pygame_up_cmd);
        this._queue_parallel_mcp_execution(actions, `timed_action: ${action_name}`);
    }
  }

  handle_toggle_action(action_name: string, state: boolean, pygame_control?: string): void {
    if (pygame_control) {
      const command = { action: "control", control: pygame_control, state };
      this.controller.send_command_sync(command);
    }

    if (this.controller.enable_logging) {
      this.controller.action_handler._log_mcp_command(action_name, { state });
    }
    
    if (this.data_collection_enabled && this.mcp_server && pygame_control) {
        const actions = [{ action: "control", control: pygame_control, state }];
        this._queue_parallel_mcp_execution(actions, `toggle_action: ${action_name}`);
    }
  }

  handle_simple_action(action_name: string, pygame_cmd?: Record<string, any>, params?: Record<string, any>): void {
    if (pygame_cmd) {
      this.controller.send_command_sync(pygame_cmd);
    }
    if (this.controller.enable_logging) {
      this.controller.action_handler._log_mcp_command(action_name, params || {});
    }

    if (this.data_collection_enabled && this.mcp_server && pygame_cmd) {
        this._queue_parallel_mcp_execution([pygame_cmd], `simple_action: ${action_name}`);
    }
  }

  connect(): void {
    this.controller.start_websocket_connection();
  }

  process_continuous_state(mouse_pos: MousePos, mouse_pressed: MousePressed, keys_pressed: KeysPressed): void {
    let movement_x = 0;
    let movement_z = 0;

    if (this.controller.ui_manager.keyboard_movement) {
        if (keys_pressed['w']) movement_z += 1;
        if (keys_pressed['s']) movement_z -= 1;
        if (keys_pressed['a']) movement_x -= 1;
        if (keys_pressed['d']) movement_x += 1;
    }

    if (this.controller.ui_manager.movement_joystick && 
        (this.controller.ui_manager.movement_joystick.get_axis(0) !== 0 || // Check if axis is non-zero before using it
         this.controller.ui_manager.movement_joystick.get_axis(1) !== 0)) {
        const joystick_x = this.controller.ui_manager.movement_joystick.get_axis(0);
        const joystick_y = this.controller.ui_manager.movement_joystick.get_axis(1);
        movement_x += joystick_x;
        movement_z -= joystick_y;
    }
    
    if (movement_x !== 0 && movement_z !== 0) {
        const norm = Math.sqrt(movement_x * movement_x + movement_z * movement_z);
        movement_x /= norm;
        movement_z /= norm;
    }

    if (movement_x !== 0 || movement_z !== 0) {
        if (!this.was_moving && this.data_collection_enabled) {
            this.movement_start_time = Date.now();
            const current_pos: [number, number] = this.controller.state?.player_pos || [0,0]; 
            this.movement_accumulator = { total_distance: 0, last_pos: current_pos };
        }
        this.was_moving = true;
        this.handle_movement(movement_x, movement_z);

        if (this.data_collection_enabled && this.movement_accumulator && this.controller.state?.player_pos) {
             const current_pos: [number, number] = this.controller.state.player_pos;
             const dist = Math.sqrt(Math.pow(current_pos[0] - this.movement_accumulator.last_pos[0], 2) + Math.pow(current_pos[1] - this.movement_accumulator.last_pos[1], 2));
             this.movement_accumulator.total_distance += dist;
             this.movement_accumulator.last_pos = current_pos;
        }

    } else {
        if (this.was_moving) {
            this.handle_movement(0, 0);
            this.was_moving = false;
            if (this.data_collection_enabled && this.movement_start_time && this.movement_accumulator) {
                const duration_ms = Date.now() - this.movement_start_time;
                const log_entry = {
                    timestamp: new Date().toISOString(),
                    event: "summarized_movement",
                    duration_ms: duration_ms,
                    total_distance: this.movement_accumulator.total_distance,
                };
                fs.appendFileSync(path.join(this.current_dir, "trace.txt"), JSON.stringify(log_entry) + "\n");
                this.movement_start_time = 0;
                this.movement_accumulator = undefined;
            }
        }
    }
    
    if (mouse_pressed[0]) { // Assuming 0 is left click
        if (!this.controller.state.action_states.left_click_held) {
            this.controller.state.action_states.left_click_held = true;
            this.handle_simple_action("attack", { action: "attack" });
        }
    } else {
        if (this.controller.state.action_states.left_click_held) {
            this.controller.state.action_states.left_click_held = false;
        }
    }
  }

  async start_async_execution(): Promise<boolean> {
    console.log("[PygameModeStrategy] Starting async execution.");
    return true;
  }

  async stop_async_execution(): Promise<boolean> {
    console.log("[PygameModeStrategy] Stopping async execution. Waiting for tasks to complete...");
    await Promise.allSettled(Array.from(this._active_tasks));
    this._active_tasks.clear();
    console.log("[PygameModeStrategy] All async tasks completed.");
    return true;
  }
  
  async initialize_async_components(): Promise<boolean> {
    console.log("[PygameModeStrategy] Initializing async components.");
    this._active_tasks = new Set();
    return true;
  }

  async cleanup_async_components(): Promise<void> {
    console.log("[PygameModeStrategy] Cleaning up async components.");
    await this.stop_async_execution();
    console.log("[PygameModeStrategy] Async components cleaned up.");
  }

  private _queue_parallel_mcp_execution(actions: Record<string, any>[], task_context: string = ""): void {
    if (!this.data_collection_enabled || !this.mcp_server) {
      return;
    }

    const mcp_actions = this._convert_actions_to_mcp_format(actions);
    
    const task = this._always_execute_getbotstatus(actions, mcp_actions, task_context);
    this._active_tasks.add(task);
    task.finally(() => {
      this._active_tasks.delete(task);
    });
  }

  private async _always_execute_getbotstatus(pygame_actions: Record<string, any>[], mcp_actions: Record<string, any>[], task_context: string): Promise<void> {
    if (!this.mcp_server) return;

    const server = this.mcp_server;
    let bot_status: ServerExecuteToolResponse | null = null;
    let saved_screenshot_filename: string | null = null; // Changed from screenshot_path
    let error_message: string | null = null;

    try {
      console.log(`[PygameModeStrategy] Executing getBotStatus for task: ${task_context}`);
      bot_status = await server.execute_tool("getBotStatus");

      if (bot_status && bot_status.multimodal_content && Array.isArray(bot_status.multimodal_content)) {
        const image_part = bot_status.multimodal_content.find(part => part.type === 'image_base64' && part.image_base64);
        if (image_part && image_part.image_base64) {
          saved_screenshot_filename = save_screenshot_file(image_part.image_base64, this.controller.session_id, task_context.replace(/[:\s]/g, '_') || "action");
        }
      }
    } catch (e: any) {
      error_message = e.message || String(e);
      console.error(`[PygameModeStrategy] Error during getBotStatus/screenshot for ${task_context}: ${error_message}`);
    }

    const log_entry = {
      timestamp: new Date().toISOString(),
      task_context,
      pygame_actions,
      mcp_actions,
      bot_status_result: bot_status,
      screenshot_filename: saved_screenshot_filename, // Changed from screenshot_path
      error: error_message,
    };

    try {
      fs.appendFileSync(path.join(this.current_dir, "trace.txt"), JSON.stringify(log_entry) + "\n");
    } catch (e:any) {
        console.error(`[PygameModeStrategy] FATAL: Could not write to trace.txt at ${this.current_dir}. Error: ${e.message}`);
    }
  }

   _convert_actions_to_mcp_format(pygame_actions: Record<string, any>[]): Record<string, any>[] {
    // Placeholder for ActionConverter.pygame_to_mcp_simple
    // TODO: Replace with actual ActionConverter import and usage
    console.warn("[PygameModeStrategy] Using placeholder _convert_actions_to_mcp_format");
    // Example conversion: Assumes actions have a 'type' and other properties become 'params'
    return pygame_actions.map(action => ({ 
        tool: action.action || action.control || "unknown_action", // try to get a name
        params: { ...action } 
    }));
  }
}

// --- MCP MODE STRATEGY IMPLEMENTATION ---

export class MCPModeStrategy extends ModeStrategy {

    constructor(controller: Controller) {
        super(controller);
        if (this.controller.last_moved_in_mcp_mode === undefined) {
            this.controller.last_moved_in_mcp_mode = 0;
        }
    }

    handle_movement(x: number, z: number): void {
        const now = Date.now();
        if (now - this.controller.last_moved_in_mcp_mode > 1000) { 
            console.log(`[MCPModeStrategy] Handling movement (x=${x}, z=${z}). Calling simple_action 'walk'.`);
            // Pass x and z if the MCP "walk" tool can use them, otherwise, it might be implicit based on camera
            this.handle_simple_action("walk", undefined, { duration: "1000ms", x, z }); 
            this.controller.last_moved_in_mcp_mode = now;
        }
    }

    handle_timed_action(action_name: string, duration: string, pygame_down_cmd?: Record<string, any>, pygame_up_cmd?: Record<string, any>, ...kwargs: any[]): void {
        const params = { duration, ...Object.assign({}, ...kwargs) };
        console.log(`[MCPModeStrategy] Handling timed action: ${action_name} with params:`, params);
        this.controller.handle_other_commands(action_name, params);
    }

    handle_toggle_action(action_name: string, state: boolean, pygame_control?: string): void {
        const params = { state };
        console.log(`[MCPModeStrategy] Handling toggle action: ${action_name} with params:`, params);
        this.controller.handle_other_commands(action_name, params);
    }

    handle_simple_action(action_name: string, pygame_cmd?: Record<string, any>, params?: Record<string, any>): void {
        console.log(`[MCPModeStrategy] Handling simple action: ${action_name} with params:`, params);
        this.controller.handle_other_commands(action_name, params || {});
    }

    connect(): void {
        console.log("[MCPModeStrategy] MCP mode ready. No WebSocket connection needed.");
    }

    process_continuous_state(mouse_pos: MousePos, mouse_pressed: MousePressed, keys_pressed: KeysPressed): void {
        // Intentionally empty
    }
}
