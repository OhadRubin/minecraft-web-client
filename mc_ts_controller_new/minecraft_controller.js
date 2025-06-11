import { WINDOW_WIDTH, WINDOW_HEIGHT, InputManager, PygameDraw, BrowserFileHandler } from "./porting.js";
import { ControllerState } from "./controller_state.js";
import { LookPathTracker } from "./look_path.js";
import { UIManager } from "./ui_manager.js";
import { ActionHandler } from "./action_handler.js";
import { MCPModeStrategy, PygameModeStrategy } from "./mode_strategy.js";
// === START_OF: main controller
// =======================================================================

class MinecraftController {
    constructor(options = {}) {
        this.state = new ControllerState(options);

        const canvas = document.getElementById('main-canvas');
        canvas.width = WINDOW_WIDTH;
        canvas.height = WINDOW_HEIGHT;
        this.surface = { 
            ctx: canvas.getContext('2d'),
            width: WINDOW_WIDTH,
            height: WINDOW_HEIGHT,
        };
        this.surface.draw = new PygameDraw(this.surface.ctx);
        this.input = new InputManager(canvas);

        this.look_path_tracker = new LookPathTracker(
            this.state.sensitivity,
            this.state.enable_logging,
            this.state.mode,
        );

        if (this.state.mode === "pygame" && this.state.data_collection_enabled) {
            this.state.mcp_server = this._create_mcp_server_for_data_collection();
        }
        
        // The original used a callback for MCP mode. We'll simplify this.
        this.look_path_tracker.set_execution_callback((mcp_command) => {
            if (this.state.mode === 'mcp') {
                this.execute_mcp_action(mcp_command);
            } else if (this.state.mode === 'pygame' && this.state.data_collection_enabled) {
                this._execute_pygame_mcp_action(mcp_command);
            }
        });

        if (this.state.mode === "pygame") {
            this.strategy = new PygameModeStrategy(
                this, this.state.mcp_server, this.state.data_collection_enabled
            );
        } else if (this.state.mode === "mcp") {
            this.strategy = new MCPModeStrategy(this);
        } else {
            throw new Error(`Unknown mode: ${this.state.mode}`);
        }

        this.ui_manager = new UIManager(this.surface, this.state, this.look_path_tracker);
        this.action_handler = new ActionHandler(this.state, this.strategy, this);
        
        if (this.state.data_collection_enabled) {
            console.log("🎬 Data collection enabled! Hotkeys: F5=Start session (mock)");
            const downloadBtn = document.getElementById('download-log-btn');
            downloadBtn.onclick = () => {
                BrowserFileHandler.downloadLog(this.strategy.traceLog.join('\n'), 'trace.txt');
            };
        }
    }

    _create_mcp_server_for_data_collection() {
        console.log("🔧 Creating MOCK MCP server for data collection in browser.");
        return {
            execute_tool: async (toolName, params) => {
                console.log(`MOCK MCP SERVER: execute_tool(${toolName}) called`);
                if (toolName === "getBotStatus") {
                    await new Promise(resolve => setTimeout(resolve, 200)); // Simulate network latency
                    // Return a mock response
                    return {
                        content: [
                            { type: "text", text: "Mock observation: You are standing in a plains biome. It is daytime. Your health is 20/20." },
                            { type: "image", data: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" } // 1x1 black pixel PNG
                        ]
                    };
                }
                return { content: [{ type: "text", text: "Mock response for " + toolName }] };
            }
        };
    }

    _handle_camera_drag_state(mouse_pressed) {
        const camera_is_clicking = this.ui_manager.camera_area.is_touching && mouse_pressed;
        const prev_clicking = this.state.camera_was_clicking;

        if (camera_is_clicking && !prev_clicking) {
            if (this.state.enable_logging) console.log("🖱️ Mouse pressed in camera area - starting drag tracking");
            this.look_path_tracker.start_mouse_tracking();
            this.state.camera_was_clicking = true;
        } else if (!mouse_pressed && prev_clicking) {
            if (this.state.enable_logging) console.log("🖱️ Mouse released - ending drag tracking");
            this.look_path_tracker.stop_mouse_tracking();
            this.state.camera_was_clicking = false;
        }
    }
    
    start_websocket_connection() {
        if (this.state.websocket) {
            this.state.websocket.close();
        }
        const uri = "ws://localhost:8081";
        console.log(`Connecting to ${uri}...`);
        
        this.state.websocket = new WebSocket(uri);

        this.state.websocket.onopen = (event) => {
            console.log("Connected to Minecraft Web Client!");
            this.state.connected = true;
            const init_message = { init: this.state.mode };
            this.state.websocket.send(JSON.stringify(init_message));
        };
        
        this.state.websocket.onclose = (event) => {
            console.log("Disconnected from Minecraft Web Client.");
            this.state.connected = false;
        };

        this.state.websocket.onerror = (event) => {
            console.error("WebSocket error:", event);
            this.state.connected = false;
        };
    }

    send_command_sync(command) {
        if (this.state.websocket && this.state.connected) {
            try {
                this.state.websocket.send(JSON.stringify(command));
            } catch (e) {
                console.error("Error sending command:", e);
                this.state.connected = false;
            }
        }
    }
    
    execute_mcp_action(mcp_command) {
        console.log(`🎮 Executing: ${mcp_command.tool}(${JSON.stringify(mcp_command.parameters)})`);
        // In a real MCP setup, this would send to a server. Here we just log it.
    }
    
     _execute_pygame_mcp_action(mcp_command) {
        if (!this.strategy._queue_parallel_mcp_execution) return;
        const action = { type: mcp_command.tool, ...mcp_command.parameters };
        this.strategy._queue_parallel_mcp_execution(
            [action], `Camera drag: ${mcp_command.tool}`
        );
    }
    
    _process_frame(timestamp) {
        const events = []; // Can be populated if specific event objects are needed
        
        const mouse_pos = this.input.getMousePos();
        const mouse_pressed = this.input.getMousePressed()[0];
        const keys_pressed = this.input.getPressed();

        const event_actions = this.ui_manager.process_events(events);
        const ui_actions = this.ui_manager.process_inputs(mouse_pos, mouse_pressed, keys_pressed);
        const keyboard_actions = this.ui_manager.process_keyboard_shortcuts(keys_pressed);
        
        this.action_handler.process_actions(
            [...event_actions, ...ui_actions, ...keyboard_actions]
        );
        
        this.strategy.process_continuous_state(mouse_pos, mouse_pressed, keys_pressed);
        
        this.action_handler.process_edge_detections(keys_pressed);
        
        this.ui_manager.update();
        this.ui_manager.draw();

        if (this.state.running) {
            requestAnimationFrame((t) => this._process_frame(t));
        }
    }

    run() {
        console.log(`Starting Minecraft Controller in ${this.state.mode.toUpperCase()} mode...`);
        this.strategy.connect();
        this.state.running = true;
        requestAnimationFrame((t) => this._process_frame(t));
    }
}

// =======================================================================
export { MinecraftController };
// === END_OF: main controller
