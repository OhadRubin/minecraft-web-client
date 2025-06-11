// === START_OF: controller_state.py
// =======================================================================

interface ActionState {
    active: boolean;
    start_time: number | null;
}

interface ActionStates {
    left_click: ActionState;
    right_click: ActionState;
    jump: ActionState;
    sneak: { active: boolean };
    sprint: { active: boolean };
}

interface ControllerStateOptions {
    mode?: string;
    sensitivity?: number;
    enable_logging?: boolean;
    data_collection_enabled?: boolean;
}

interface KeyStates {
    [key: string]: boolean;
}

type ControllerMode = "pygame" | "mcp";
type ContextType = "world" | "inventory";

class ControllerState {
    running: boolean = true;
    connected: boolean = false;
    mode: ControllerMode = "pygame";
    sensitivity: number = 5.0;
    enable_logging: boolean = false;
    data_collection_enabled: boolean = false;
    conversation_session_active: boolean = false;
    current_task_description: string = "";
    session_start_time: number = 0;
    inventory_open: boolean = false;
    current_context: ContextType = "world";
    last_inventory_toggle_time: number = 0;
    current_hotbar_slot: number = 0;
    last_hotbar_slot: number = -1;
    last_movement: [number, number] = [0.0, 0.0];
    last_moved_in_mcp_mode: number = 0;
    action_states: ActionStates = {
        left_click: { active: false, start_time: null },
        right_click: { active: false, start_time: null },
        jump: { active: false, start_time: null },
        sneak: { active: false },
        sprint: { active: false },
    };
    last_key_states: KeyStates = {};
    camera_was_clicking: boolean = false;
    websocket: WebSocket | null = null;
    mcp_server: any = null; // Ported from Python - using 'any' as the specific type is not defined

    constructor(options: ControllerStateOptions = {}) {
        this.mode = "pygame";
        this.sensitivity = options.sensitivity ?? 5.0;
        this.enable_logging = options.enable_logging ?? false;
        this.data_collection_enabled = options.data_collection_enabled ?? false;
    }
}

// =======================================================================
export { ControllerState };
export type { ControllerStateOptions, ActionState, ActionStates, KeyStates, ControllerMode, ContextType };
// === END_OF: controller_state.py