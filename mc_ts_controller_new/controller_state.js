// === START_OF: controller_state.py
// =======================================================================

class ControllerState {
    running = true;
    connected = false;
    mode = "pygame";
    sensitivity = 5.0;
    enable_logging = false;
    data_collection_enabled = false;
    conversation_session_active = false;
    current_task_description = "";
    session_start_time = 0;
    inventory_open = false;
    current_context = "world";
    last_inventory_toggle_time = 0;
    current_hotbar_slot = 0;
    last_hotbar_slot = -1;
    last_movement = [0.0, 0.0];
    last_moved_in_mcp_mode = 0;
    action_states = {
        left_click: { active: false, start_time: null },
        right_click: { active: false, start_time: null },
        jump: { active: false, start_time: null },
        sneak: { active: false },
        sprint: { active: false },
    };
    last_key_states = {};
    camera_was_clicking = false;
    websocket = null;
    mcp_server = null; // Ported from Python

    constructor(options = {}) {
        this.mode = options.mode ?? "pygame";
        this.sensitivity = options.sensitivity ?? 5.0;
        this.enable_logging = options.enable_logging ?? false;
        this.data_collection_enabled = options.data_collection_enabled ?? false;
    }
}

// =======================================================================
export { ControllerState };
// === END_OF: controller_state.py
