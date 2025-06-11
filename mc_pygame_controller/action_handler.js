import { Keys } from "./porting.js";
// === START_OF: action_handler.py
// =======================================================================

class ActionHandler {
    constructor(controller_state, mode_strategy, controller) {
        this.state = controller_state;
        this.strategy = mode_strategy;
        this.controller = controller;
        this._last_jump_state = false;

        this._action_handlers = {
            "movement": (v) => v && this.handle_movement(v[0], v[1]),
            "camera_look": (v) => v && this.handle_camera_look(v[0], v[1]),
            "camera_drag_state": (v) => this.controller._handle_camera_drag_state(v),
            "left_click": (v) => this.handle_left_click(v),
            "right_click": (v) => this.handle_right_click(v),
            "jump": (v) => this._handle_jump_action(v),
            "jump_keyboard": (v) => this._handle_jump_action(v),
            "sneak_toggled": (v) => this.handle_sneak(v),
            "sprint_toggled": (v) => this.handle_sprint(v),
            "inventory_pressed": (_) => this.handle_inventory(),
            "drop_item_pressed": (_) => this.handle_drop_item(),
            "swap_hands_pressed": (_) => this.handle_swap_hands(),
            "hotbar_slot_pressed": (v) => this.handle_hotbar_slot(v),
        };
    }

    _handle_jump_action(state) {
        if (state !== this._last_jump_state) {
            this.handle_jump(state);
            this._last_jump_state = state;
        }
    }

    _calculate_duration(start_time) {
        if (!start_time) return "medium";
        const duration_ms = Date.now() - start_time;
        if (duration_ms < 150) return "very_short";
        if (duration_ms < 750) return "short";
        if (duration_ms < 1500) return "medium";
        if (duration_ms < 3500) return "long";
        if (duration_ms < 7500) return "very_long";
        return "very_very_long";
    }

    _handle_timed_action(action_name, pressed, pygame_down_cmd, pygame_up_cmd, mcp_tool, mcp_params_func = null) {
        const state = this.state.action_states[action_name];
        if (pressed && !state.active) {
            if (this.state.enable_logging) console.log(`${action_name.toUpperCase()} DOWN`);
            state.start_time = Date.now();
            state.active = true;
        } else if (!pressed && state.active) {
            if (this.state.enable_logging) console.log(`${action_name.toUpperCase()} UP`);
            const duration = this._calculate_duration(state.start_time);
            state.start_time = null;

            const kwargs = mcp_params_func ? mcp_params_func(duration) : {};
            this.strategy.handle_timed_action(mcp_tool, duration, pygame_down_cmd, pygame_up_cmd, kwargs);
            state.active = false;
        }
    }

    _handle_toggle_action(action_name, toggled, pygame_control, mcp_tool) {
        const state = this.state.action_states[action_name];
        if (toggled !== state.active) {
            this.strategy.handle_toggle_action(mcp_tool, toggled, pygame_control);
            state.active = toggled;
        }
    }

    _detect_key_edge(key_name, current_state) {
        const last_state = this.state.last_key_states[key_name] || false;
        this.state.last_key_states[key_name] = current_state;
        const just_pressed = current_state && !last_state;
        const just_released = !current_state && last_state;
        return [just_pressed, just_released];
    }

    handle_movement(x, y) {
        const movement_x = x;
        const movement_z = y;
        if (Math.abs(movement_x - this.state.last_movement[0]) > 0.1 || Math.abs(movement_z - this.state.last_movement[1]) > 0.1) {
            this.strategy.handle_movement(movement_x, movement_z);
            this.state.last_movement = [movement_x, movement_z];
        }
    }

    handle_camera_look(delta_x, delta_y) {
        if (delta_x !== 0 || delta_y !== 0) {
            const scaled_x = delta_x * 2;
            const scaled_y = delta_y * 2;
            
            // In browser, look path tracker is handled by its own input handler
            // this.controller.look_path_tracker.add_movement(scaled_x, scaled_y);
            
            if (this.state.mode === "pygame") {
                const command = { type: "look", movementX: scaled_x, movementY: scaled_y };
                this.controller.send_command_sync(command);
            }
        }
    }

    handle_left_click(pressed) {
        this._handle_timed_action(
            "left_click",
            pressed,
            { type: "leftDown" },
            { type: "leftUp" },
            "leftClick"
        );
    }

    handle_right_click(pressed) {
        this._handle_timed_action(
            "right_click",
            pressed,
            { type: "rightDown" },
            { type: "rightUp" },
            "rightClick"
        );
    }

    handle_jump(pressed) {
        this._handle_timed_action(
            "jump",
            pressed,
            { type: "control", control: "jump", state: true },
            { type: "control", control: "jump", state: false },
            "jump"
        );
    }

    handle_sneak(toggled) {
        this._handle_toggle_action("sneak", toggled, "sneak", "sneak");
    }

    handle_sprint(toggled) {
        this._handle_toggle_action("sprint", toggled, "sprint", "sprint");
    }

    handle_inventory() {
        this.state.inventory_open = !this.state.inventory_open;
        if (this.state.enable_logging) {
            console.log(`INVENTORY ${this.state.inventory_open ? 'OPENED' : 'CLOSED'}`);
        }
        this.strategy.handle_simple_action("toggleInventory", { type: "inventory" });
    }

    handle_hotbar_slot(slot) {
        if (slot >= 0 && slot <= 8 && slot !== this.state.last_hotbar_slot) {
            if (this.state.enable_logging) console.log(`HOTBAR SLOT ${slot + 1}`);
            this.strategy.handle_simple_action(
                "setHotbarSlot",
                { type: "setHotbarSlot", slot: slot },
                { slot }
            );
            this.state.current_hotbar_slot = slot;
            this.state.last_hotbar_slot = slot;
        }
    }

    handle_drop_item() {
        if (this.state.enable_logging) console.log("DROP ITEM");
        this.strategy.handle_simple_action(
            "dropItem",
            { type: "dropItem", amount: 1 },
            { amount: 1 }
        );
    }

    handle_swap_hands() {
        if (this.state.enable_logging) console.log("SWAP HANDS");
        this.strategy.handle_simple_action(
            "swapHands",
            { type: "swapHands" }
        );
    }

    process_actions(actions) {
        for (const [action_name, value] of actions) {
            const handler = this._action_handlers[action_name];
            if (handler) {
                handler(value);
            } else if (action_name && this.state.enable_logging) {
                console.warn(`Warning: No handler for action '${action_name}'`);
            }
        }
    }

    process_edge_detections(keys_pressed) {
        // Hotbar slots 1-9
        for (let i = 0; i < 9; i++) {
            const key_name = `hotbar_${i}`;
            const key_code = Keys[`K_${i + 1}`];
            const [just_pressed] = this._detect_key_edge(key_name, keys_pressed[key_code]);
            if (just_pressed) this.handle_hotbar_slot(i);
        }

        // Other keys
        const key_map = {
            'drop_item': { key: Keys.K_q, handler: this.handle_drop_item },
            'swap_hands': { key: Keys.K_f, handler: this.handle_swap_hands },
            'inventory': { key: Keys.K_e, handler: this.handle_inventory },
        };
        for (const [name, { key, handler }] of Object.entries(key_map)) {
            const [just_pressed] = this._detect_key_edge(name, keys_pressed[key]);
            if (just_pressed) handler.call(this);
        }
    }

    _log_mcp_command(tool, parameters) {
        if (this.state.enable_logging) {
            const mcp_command = { tool, parameters };
            console.log(`LOGGED: ${JSON.stringify(mcp_command)}`);
        }
    }
}
// =======================================================================
export { ActionHandler };
// === END_OF: action_handler.py
