/**
 * Controller State Management
 *
 * Centralized state management for the MinecraftController to improve organization
 * and make state sharing between components easier.
 */

// Placeholder for WebSocket type, replace with actual type from 'ws' or similar library later.
type WebSocketServerProtocol = any;
type AsyncLoop = any; // Placeholder for asyncio loop type
type EventQueue = any; // Placeholder for asyncio queue type
type CommandQueue = any; // Placeholder for asyncio queue type
type ResultQueue = any; // Placeholder for asyncio queue type
type McpExecutor = any; // Placeholder for MCP executor type
type Chain = any; // Placeholder for Chain type
type ConnectionThread = any; // Placeholder for ConnectionThread type

/**
 * Represents the state of a single action, including whether it's active
 * and when it started.
 */
interface ActionState {
    active: boolean;
    startTime?: number | null; // Optional start time, using number for timestamps
}

/**
 * Defines the structure for tracking multiple action states.
 * Keys are action names (e.g., "left_click", "jump").
 */
interface ActionStates {
    [key: string]: ActionState;
}

/**
 * Defines the structure for tracking keyboard key states.
 * Keys are key names (e.g., "ctrl", "space").
 */
interface KeyStates {
    [key: string]: boolean;
}

/**
 * Centralized state container for MinecraftController.
 */
export class ControllerState {
    /** Whether the controller is currently running. */
    running: boolean = true;
    /** Whether a WebSocket connection to the game is established. */
    connected: boolean = false;
    /** Current operating mode of the controller (e.g., "pygame", "mcp"). */
    mode: string = "pygame";
    /** Mouse sensitivity for camera movements. */
    sensitivity: number = 5.0;
    /** Whether detailed logging is enabled. */
    enable_logging: boolean = false;

    // Data collection state
    /** Whether data collection features are active. */
    data_collection_enabled: boolean = false;
    /** Whether a conversation session with an agent is active. */
    conversation_session_active: boolean = false;
    /** Description of the current task being performed. */
    current_task_description: string = "";
    /** Timestamp of when the current session started. */
    session_start_time: number = 0.0;

    // Context state for intelligent button handling
    /** Whether the player's inventory is currently open. */
    inventory_open: boolean = false;
    /** Current game context (e.g., "world", "inventory"). */
    current_context: string = "world";
    /** Timestamp of the last inventory toggle action. */
    last_inventory_toggle_time: number = 0.0;

    // Hotbar state
    /** Currently selected hotbar slot (0-8). */
    current_hotbar_slot: number = 0;
    /** Previously selected hotbar slot. */
    last_hotbar_slot: number = -1;

    // Movement state
    /** Last recorded mouse movement delta (dx, dy). */
    last_movement: [number, number] = [0.0, 0.0];
    /** Timestamp of the last movement input in MCP mode. */
    last_moved_in_mcp_mode: number = 0;

    // Action state tracking with timing
    /**
     * Tracks the state of various actions like clicking, jumping, etc.
     * Includes whether the action is active and its start time.
     */
    action_states: ActionStates = {
        "left_click": { active: false, startTime: null },
        "right_click": { active: false, startTime: null },
        "jump": { active: false, startTime: null },
        "sneak": { active: false },
        "sprint": { active: false },
    };

    // Keyboard shortcut states
    /** Tracks the pressed state of various keyboard keys for shortcuts. */
    key_states: KeyStates = {
        "ctrl": false,
        "tab": false,
        "z": false,
        "x": false,
        "space": false,
        "q": false,
        "f": false,
        "c": false,
    };

    // Key press tracking for edge detection
    /**
     * Tracks the previous state of keyboard keys to detect changes (press/release).
     */
    last_key_states: KeyStates = {};

    // Mouse tracking state for camera area
    /** Whether the camera area was being clicked in the previous frame. */
    camera_was_clicking: boolean = false;

    // WebSocket connection
    /** The WebSocket connection object. Type 'any' for now. */
    websocket: WebSocketServerProtocol | null = null;
    /** Thread handling the WebSocket connection. Type 'any' for now. */
    connection_thread: ConnectionThread | null = null;
    /** Asyncio event loop associated with the WebSocket. Type 'any' for now. */
    loop: AsyncLoop | null = null;

    // MCP execution state
    /** Executor for Minecraft Protocol (MCP) commands. Type 'any' for now. */
    mcp_executor: McpExecutor | null = null;

    // Asyncio integration
    /** Main asyncio event loop for the controller. Type 'any' for now. */
    event_loop: AsyncLoop | null = null;
    /** Queue for events. Type 'any' for now. */
    event_queue: EventQueue | null = null;
    /** Queue for commands to be sent to the game. Type 'any' for now. */
    command_queue: CommandQueue | null = null;
    /** Queue for results received from the game. Type 'any' for now. */
    result_queue: ResultQueue | null = null;

    // Additional state
    /** Placeholder for a 'Chain' object, possibly for command chaining. Type 'any' for now. */
    chain: Chain | null = null;
    /** List of available servers. */
    servers: any[] = []; // Python's 'list' translates to 'any[]' or a more specific type.

    constructor() {
        // Default factory for last_key_states is an empty dict,
        // so it's initialized directly as an empty object.
        this.last_key_states = {};
        // Default factory for servers is an empty list,
        // so it's initialized directly as an empty array.
        this.servers = [];
    }
}
