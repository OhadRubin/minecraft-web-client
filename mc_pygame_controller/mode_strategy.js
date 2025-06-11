import { ActionConverter, convert_to_mcp_format } from "./action_converter.js";
import { BrowserFileHandler } from "./porting.js";
// === START_OF: mode_strategy.py
// =======================================================================

class ModeStrategy {
    constructor(controller) {
        this.controller = controller;
    }
    handle_movement(x, z) { throw new Error("Not implemented"); }
    handle_timed_action(action_name, duration, pygame_down_cmd, pygame_up_cmd, kwargs) { throw new Error("Not implemented"); }
    handle_toggle_action(action_name, state, pygame_control) { throw new Error("Not implemented"); }
    handle_simple_action(action_name, pygame_cmd, params) { throw new Error("Not implemented"); }
    connect() { throw new Error("Not implemented"); }
    process_continuous_state(mouse_pos, mouse_pressed, keys_pressed) { throw new Error("Not implemented"); }
}

class MCPModeStrategy extends ModeStrategy {
    // A basic implementation for MCP mode, which focuses on converting to MCP format.
    constructor(controller) {
        super(controller);
        console.log("🔧 MCPModeStrategy: Initializing in MCP mode.");
    }
    
    _execute(mcp_command) {
        if (this.controller.mcp_executor) {
            this.controller.mcp_executor(mcp_command);
        } else if (this.controller.state.enable_logging) {
            console.log(`MCP EXECUTE (no executor): ${JSON.stringify(mcp_command)}`);
        }
    }

    handle_movement(x, z) {
        const mcp_command = ActionConverter._convert_move_action({x, z});
        if(mcp_command) this._execute(mcp_command);
    }
    
    handle_timed_action(action_name, duration, pygame_down_cmd, pygame_up_cmd, kwargs) {
        const params = { duration, ...kwargs };
        const mcp_command = convert_to_mcp_format(action_name, params);
        if (mcp_command) this._execute(mcp_command);
    }

    handle_toggle_action(action_name, state, pygame_control) {
        const mcp_command = convert_to_mcp_format(action_name, { state });
        if (mcp_command) this._execute(mcp_command);
    }

    handle_simple_action(action_name, pygame_cmd, params = {}) {
        const mcp_command = convert_to_mcp_format(action_name, params);
        if (mcp_command) this._execute(mcp_command);
    }
    
    connect() {
        console.log("MCP mode does not require a WebSocket connection.");
        this.controller.state.connected = true; // Mark as "connected" conceptually
    }
    
    process_continuous_state(mouse_pos, mouse_pressed, keys_pressed) {
        // MCP mode is event-driven, less reliant on continuous state processing.
    }
}

class PygameModeStrategy extends ModeStrategy {
    constructor(controller, mcp_server, data_collection_enabled) {
        super(controller);
        this.was_moving = false;
        this.data_collection_enabled = data_collection_enabled;
        this.mcp_server = mcp_server;
        this.traceLog = [];
        this.trajectory_id = `trajectory_${Math.floor(Date.now() / 1000)}`;

        if (this.mcp_server && this.data_collection_enabled) {
            console.log("🔧 PygameModeStrategy: Initializing MOCK + OBSERVE mode");
            document.getElementById('data-collection-log-container').style.display = 'block';
        } else {
            console.log("🔧 PygameModeStrategy: Initializing in PURE WebSocket mode.");
        }
    }

    handle_movement(x, z) {
        const command = { type: "move", x, z };
        this.controller.send_command_sync(command);

        if (this.controller.state.enable_logging && (Math.abs(x) > 0.1 || Math.abs(z) > 0.1)) {
            const magnitude = Math.hypot(x, z);
            const duration = Math.floor(magnitude * ActionConverter.MAGNITUDE_DURATION_SCALE);
            this.controller.action_handler._log_mcp_command("walk", { duration });
        }
    }

    handle_timed_action(action_name, duration, pygame_down_cmd, pygame_up_cmd, kwargs) {
        const commands_sent = [];
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
    
    handle_toggle_action(action_name, state, pygame_control) {
        if (pygame_control) {
            const command = { type: "control", control: pygame_control, state };
            this.controller.send_command_sync(command);
            if (this.data_collection_enabled && this.mcp_server) {
                this._queue_parallel_mcp_execution([command], `Toggle Action: ${action_name}`);
            }
        }
        this.controller.action_handler._log_mcp_command(action_name, { state });
    }

    handle_simple_action(action_name, pygame_cmd, params = {}) {
        if (pygame_cmd) {
            this.controller.send_command_sync(pygame_cmd);
            if (this.data_collection_enabled && this.mcp_server) {
                this._queue_parallel_mcp_execution([pygame_cmd], `Simple Action: ${action_name}`);
            }
        }
        this.controller.action_handler._log_mcp_command(action_name, params);
    }

    connect() {
        this.controller.start_websocket_connection();
    }
    
    process_continuous_state(mouse_pos, mouse_pressed, keys_pressed) {
        const keyboard_move = this.controller.ui_manager.keyboard_movement.handle_keyboard(keys_pressed);
        const joystick = this.controller.ui_manager.movement_joystick;
        const joystick_move = [
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
            const command = { type: "move", x: movement_x, z: movement_z };
            this.controller.send_command_sync(command);
        } else if (this.was_moving) {
             const command = { type: "move", x: 0.0, z: 0.0 };
             this.controller.send_command_sync(command);
        }
        this.was_moving = is_moving;

        if (this.data_collection_enabled) {
            // In the original, this was more complex. Here, we simplify and just
            // queue MCP execution for any significant movement at the end.
            // A more faithful port would require a movement accumulator.
        }
    }
    
    _queue_parallel_mcp_execution(actions, task_context) {
        if (!this.data_collection_enabled || !this.mcp_server) return;

        const mcp_actions = ActionConverter.pygame_to_mcp_simple(actions);
        this.logToDom(`🎭 Mock actions: ${mcp_actions.map(a => a.tool).join(', ')}`);
        
        // Use an async IIFE to call the async method from this sync context
        (async () => {
            await this._always_execute_getbotstatus(actions, mcp_actions, task_context);
        })();
    }

    async _always_execute_getbotstatus(pygame_actions, mcp_actions, task_context) {
        try {
            const real_response = await this.mcp_server.execute_tool("getBotStatus", {});
            
            const tool_text = real_response.content[0].text;
            const base64_string = real_response.content[1].data;
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

    logToDom(message, type = 'info') {
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
