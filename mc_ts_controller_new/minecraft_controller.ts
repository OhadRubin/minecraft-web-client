import { WINDOW_WIDTH, WINDOW_HEIGHT, InputManager, PygameDraw, BrowserFileHandler } from "./porting.js";
import { ControllerState } from "./controller_state.js";
import { LookPathTracker } from "./look_path.js";
import { UIManager } from "./ui_manager.js";
import { ActionHandler } from "./action_handler.js";
import { MCPModeStrategy, PygameModeStrategy } from "./mode_strategy.js";

// === START_OF: main controller
// =======================================================================

// Type definitions
interface ControllerOptions {
    mode?: 'pygame' | 'mcp';
    data_collection_enabled?: boolean;
    sensitivity?: number;
    enable_logging?: boolean;
    [key: string]: any;
}

interface Surface {
    ctx: CanvasRenderingContext2D;
    width: number;
    height: number;
    draw: PygameDraw;
}

interface MCPCommand {
    tool: string;
    parameters: Record<string, any>;
}

interface MCPResponse {
    content: Array<{
        type: 'text' | 'image';
        text?: string;
        data?: string;
    }>;
}

interface MockMCPServer {
    execute_tool: (toolName: string, params: Record<string, any>) => Promise<MCPResponse>;
}

interface WebSocketCommand {
    init?: string;
    [key: string]: any;
}

interface MousePosition {
    x: number;
    y: number;
}

interface UIAction {
    type: string;
    [key: string]: any;
}

type ModeStrategy = MCPModeStrategy | PygameModeStrategy;

class MinecraftController {
    private state: ControllerState;
    private surface: Surface;
    private input: InputManager;
    private look_path_tracker: LookPathTracker;
    private strategy: ModeStrategy;
    private ui_manager: UIManager;
    private action_handler: ActionHandler;

    constructor(options: ControllerOptions = {}) {
        this.state = new ControllerState(options);

        const canvas = document.getElementById('main-canvas') as HTMLCanvasElement;
        if (!canvas) {
            throw new Error('Canvas element with id "main-canvas" not found');
        }
        
        canvas.width = WINDOW_WIDTH;
        canvas.height = WINDOW_HEIGHT;
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            throw new Error('Could not get 2D rendering context from canvas');
        }
        
        this.surface = { 
            ctx,
            width: WINDOW_WIDTH,
            height: WINDOW_HEIGHT,
            draw: new PygameDraw(ctx)
        };
        
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
        this.look_path_tracker.set_execution_callback((mcp_command: MCPCommand) => {
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
            const downloadBtn = document.getElementById('download-log-btn') as HTMLButtonElement;
            if (downloadBtn) {
                downloadBtn.onclick = () => {
                    BrowserFileHandler.downloadLog(this.strategy.traceLog.join('\n'), 'trace.txt');
                };
            }
        }
    }

    private _create_mcp_server_for_data_collection(): MockMCPServer {
        console.log("🔧 Creating MOCK MCP server for data collection in browser.");
        return {
            execute_tool: async (toolName: string, params: Record<string, any>): Promise<MCPResponse> => {
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

    private _handle_camera_drag_state(mouse_pressed: boolean): void {
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
    
    start_websocket_connection(): void {
        if (this.state.websocket) {
            this.state.websocket.close();
        }
        const uri = "ws://localhost:8081";
        console.log(`Connecting to ${uri}...`);
        
        this.state.websocket = new WebSocket(uri);

        this.state.websocket.onopen = (event: Event) => {
            console.log("Connected to Minecraft Web Client!");
            this.state.connected = true;
            const init_message: WebSocketCommand = { init: this.state.mode };
            this.state.websocket!.send(JSON.stringify(init_message));
        };
        
        this.state.websocket.onclose = (event: CloseEvent) => {
            console.log("Disconnected from Minecraft Web Client.");
            this.state.connected = false;
        };

        this.state.websocket.onerror = (event: Event) => {
            console.error("WebSocket error:", event);
            this.state.connected = false;
        };
    }

    send_command_sync(command: WebSocketCommand): void {
        if (this.state.websocket && this.state.connected) {
            try {
                this.state.websocket.send(JSON.stringify(command));
            } catch (e) {
                console.error("Error sending command:", e);
                this.state.connected = false;
            }
        }
    }
    
    execute_mcp_action(mcp_command: MCPCommand): void {
        console.log(`🎮 Executing: ${mcp_command.tool}(${JSON.stringify(mcp_command.parameters)})`);
        // In a real MCP setup, this would send to a server. Here we just log it.
    }
    
    private _execute_pygame_mcp_action(mcp_command: MCPCommand): void {
        if (!this.strategy._queue_parallel_mcp_execution) return;
        const action: UIAction = { type: mcp_command.tool, ...mcp_command.parameters };
        this.strategy._queue_parallel_mcp_execution(
            [action], `Camera drag: ${mcp_command.tool}`
        );
    }
    
    private _process_frame(timestamp: number): void {
        const events: Event[] = []; // Can be populated if specific event objects are needed
        
        const mouse_pos: MousePosition = this.input.getMousePos();
        const mouse_pressed: boolean = this.input.getMousePressed()[0];
        const keys_pressed: Record<string, boolean> = this.input.getPressed();

        const event_actions: UIAction[] = this.ui_manager.process_events(events);
        const ui_actions: UIAction[] = this.ui_manager.process_inputs(mouse_pos, mouse_pressed, keys_pressed);
        const keyboard_actions: UIAction[] = this.ui_manager.process_keyboard_shortcuts(keys_pressed);
        
        this.action_handler.process_actions(
            [...event_actions, ...ui_actions, ...keyboard_actions]
        );
        
        this.strategy.process_continuous_state(mouse_pos, mouse_pressed, keys_pressed);
        
        this.action_handler.process_edge_detections(keys_pressed);
        
        this.ui_manager.update();
        this.ui_manager.draw();

        if (this.state.running) {
            requestAnimationFrame((t: number) => this._process_frame(t));
        }
    }

    run(): void {
        console.log(`Starting Minecraft Controller in ${this.state.mode.toUpperCase()} mode...`);
        this.strategy.connect();
        this.state.running = true;
        requestAnimationFrame((t: number) => this._process_frame(t));
    }
}

// =======================================================================
export { MinecraftController };
export type { ControllerOptions, MCPCommand, MCPResponse, MockMCPServer, WebSocketCommand, MousePosition, UIAction };
// === END_OF: main controller