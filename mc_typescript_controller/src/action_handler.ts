/**
 * @file action_handler.ts
 * Handles the conversion of UI actions and raw inputs (like keyboard presses)
 * into game commands, utilizing a mode-specific strategy.
 */

import type { ControllerState } from './controller_state';
import type { ModeStrategy } from './mode_strategy';
// import type { MinecraftControllerBase } from './controller_base'; // Use this when controller_base.ts is defined
// import type { LookPathTracker } from './look_path'; // Use this when look_path.ts is defined

// Placeholder types until actual controller and tracker are fully defined
type MinecraftControllerBase = any;
type LookPathTracker = any;

/** Represents an action tuple: [actionName, actionValue] */
export type ActionTuple = [string, any];

/** Represents the state of keyboard keys, typically a record of key codes to boolean (pressed/not pressed) */
export type KeyStates = Record<string, boolean>;

/**
 * Processes user inputs and dispatches actions to the appropriate strategy.
 * It acts as a bridge between raw input/UI events and game-specific commands.
 */
export class ActionHandler {
    private state: ControllerState;
    private strategy: ModeStrategy;
    private controller: MinecraftControllerBase; // Should be MinecraftControllerBase
    private _last_jump_state: boolean = false;
    private _action_handlers: Record<string, (value: any) => void>;

    /**
     * Initializes the ActionHandler.
     * @param controller_state - The shared state of the controller.
     * @param mode_strategy - The current mode strategy for command execution.
     * @param controller - The main controller instance.
     */
    constructor(
        controller_state: ControllerState,
        mode_strategy: ModeStrategy,
        controller: MinecraftControllerBase // Should be MinecraftControllerBase
    ) {
        this.state = controller_state;
        this.strategy = mode_strategy;
        this.controller = controller;

        this._action_handlers = {
            "movement": (v) => v && this.handle_movement(v[0] as number, v[1] as number),
            "camera_look": (v) => v && this.handle_camera_look(v[0] as number, v[1] as number),
            "camera_drag_state": (v) => v && this.controller._handle_camera_drag_state(v[0]), // Assumes controller has this method
            "left_click": (v) => this.handle_left_click(v as boolean),
            "right_click": (v) => this.handle_right_click(v as boolean),
            "left_click_keyboard": (v) => this._handle_left_click_keyboard(v as boolean),
            "right_click_keyboard": (v) => this._handle_right_click_keyboard(v as boolean),
            "jump": (v) => this._handle_jump_action(v as boolean),
            "jump_keyboard": (v) => this._handle_jump_action(v as boolean), // Same helper
            "sneak_toggled": (v) => this.handle_sneak(v as boolean),
            "sprint_toggled": (v) => this.handle_sprint(v as boolean),
            "inventory_pressed": (_) => this.handle_inventory(),
            "drop_item_pressed": (_) => this.handle_drop_item(),
            "swap_hands_pressed": (_) => this.handle_swap_hands(),
            "clear_path_pressed": (_) => this.handle_clear_path(),
            "test_status_pressed": (_) => this.controller.handle_test_status(), // Assumes controller has this method
            "save_demo_pressed": (_) => this.controller.handle_save_demonstration(), // Assumes controller has this method
            "hotbar_slot_pressed": (v) => this.handle_hotbar_slot(v as number),
        };
    }

    private _handle_jump_action(state: boolean): void {
        if (state !== this._last_jump_state) {
            this.handle_jump(state);
            this._last_jump_state = state;
        }
    }

    private _handle_left_click_keyboard(keyboard_state: boolean): void {
        // Adaptation: Original Python code references self.controller.ui_manager.
        // This needs to be refactored for TypeScript. For now, assume button_state might be
        // sourced differently or this function's scope changes.
        // Defaulting button_state to false for now.
        const button_state = false; // TODO: Integrate with actual UI button state if necessary
        const combined_state = keyboard_state || button_state;
        this.handle_left_click(combined_state);
    }

    private _handle_right_click_keyboard(keyboard_state: boolean): void {
        // Adaptation: Similar to _handle_left_click_keyboard, UI manager dependency.
        const button_state = false; // TODO: Integrate with actual UI button state if necessary
        const combined_state = keyboard_state || button_state;
        this.handle_right_click(combined_state);
    }

    private _calculate_duration(start_time: number | null | undefined): string {
        if (!start_time) {
            return "medium";
        }
        const duration_ms = Math.round((Date.now() - start_time)); // start_time is already in ms from Date.now()

        if (duration_ms < 150) return "very_short";
        if (duration_ms < 750) return "short";
        if (duration_ms < 1500) return "medium";
        if (duration_ms < 3500) return "long";
        if (duration_ms < 7500) return "very_long";
        return "very_very_long";
    }

    private _handle_timed_action(
        action_name: keyof ControllerState['action_states'], // Ensure action_name is a valid key
        pressed: boolean,
        pygame_down_cmd: Record<string, any>,
        pygame_up_cmd: Record<string, any>,
        mcp_tool: string,
        mcp_params_func?: (duration: string) => Record<string, any>
    ): void {
        const actionState = this.state.action_states[action_name];
        if (!actionState) return; // Should not happen if action_name is a valid key

        if (pressed && !actionState.active) {
            if (this.state.enable_logging) {
                console.log(`${action_name.toUpperCase()} DOWN - sending command`);
            }
            actionState.startTime = Date.now(); // Use milliseconds
            actionState.active = true;
        } else if (!pressed && actionState.active) {
            if (this.state.enable_logging) {
                console.log(`${action_name.toUpperCase()} UP - sending command`);
            }
            const duration = this._calculate_duration(actionState.startTime);
            actionState.startTime = null;

            const kwargs = mcp_params_func ? mcp_params_func(duration) : {};
            this.strategy.handle_timed_action(
                mcp_tool,
                duration,
                pygame_down_cmd,
                pygame_up_cmd,
                kwargs
            );
            actionState.active = false;
        }
    }

    private _handle_toggle_action(
        action_name: keyof ControllerState['action_states'],
        toggled: boolean,
        pygame_control: string,
        mcp_tool: string
    ): void {
        const actionState = this.state.action_states[action_name];
        if (!actionState) return;

        if (toggled !== actionState.active) {
            this.strategy.handle_toggle_action(mcp_tool, toggled, pygame_control);
            actionState.active = toggled; // Ensure 'active' can be boolean
        }
    }

    private _detect_key_edge(key_name: string, current_state: boolean): [boolean, boolean] {
        const last_state = this.state.last_key_states[key_name] || false;
        this.state.last_key_states[key_name] = current_state;
        const just_pressed = current_state && !last_state;
        const just_released = !current_state && last_state;
        return [just_pressed, just_released];
    }

    public handle_movement(x: number, y: number): void {
        const movement_x = x;
        const movement_z = y; // Python version removed inversion, kept here.

        if (Math.abs(movement_x - this.state.last_movement[0]) > 0.1 ||
            Math.abs(movement_z - this.state.last_movement[1]) > 0.1) {
            this.strategy.handle_movement(movement_x, movement_z);
            this.state.last_movement = [movement_x, movement_z];
        }
    }

    public handle_camera_look(delta_x: number, delta_y: number): void {
        if (delta_x !== 0 || delta_y !== 0) {
            const scaled_x = delta_x * 2;
            const scaled_y = delta_y * 2;

            // Assuming this.controller.look_path_tracker is properly initialized LookPathTracker
            (this.controller.look_path_tracker as LookPathTracker).add_movement(scaled_x, scaled_y);

            if (this.state.mode === "pygame") {
                const command = { type: "look", movementX: scaled_x, movementY: scaled_y };
                this.controller.send_command_sync(command); // Assumes controller has send_command_sync
            }
        }
    }

    public handle_left_click(pressed: boolean): void {
        this._handle_timed_action(
            "left_click",
            pressed,
            { type: "leftDown" },
            { type: "leftUp" },
            "leftClick"
        );
    }

    public handle_right_click(pressed: boolean): void {
        this._handle_timed_action(
            "right_click",
            pressed,
            { type: "rightDown" },
            { type: "rightUp" },
            "rightClick"
        );
    }

    public handle_jump(pressed: boolean): void {
        this._handle_timed_action(
            "jump",
            pressed,
            { type: "control", control: "jump", state: true },
            { type: "control", control: "jump", state: false },
            "jump"
        );
    }

    public handle_sneak(toggled: boolean): void {
        this._handle_toggle_action("sneak", toggled, "sneak", "sneak");
    }

    public handle_sprint(toggled: boolean): void {
        this._handle_toggle_action("sprint", toggled, "sprint", "sprint");
    }

    public handle_inventory(): void {
        this.state.inventory_open = !this.state.inventory_open;
        this.state.current_context = this.state.inventory_open ? "inventory" : "world";
        this.state.last_inventory_toggle_time = Date.now() / 1000; // Seconds

        if (this.state.enable_logging) {
            console.log(`INVENTORY ${this.state.inventory_open ? 'OPENED' : 'CLOSED'} - context: ${this.state.current_context}`);
        }
        this.strategy.handle_simple_action("toggleInventory", { type: "inventory" });
    }

    public handle_hotbar_slot(slot: number): void {
        if (slot >= 0 && slot <= 8 && slot !== this.state.last_hotbar_slot) {
            if (this.state.enable_logging) {
                console.log(`HOTBAR SLOT ${slot + 1} - sending command`);
            }
            this.strategy.handle_simple_action(
                "setHotbarSlot",
                { type: "setHotbarSlot", slot },
                { slot }
            );
            this.state.current_hotbar_slot = slot;
            this.state.last_hotbar_slot = slot;
        }
    }

    public handle_drop_item(): void {
        if (this.state.enable_logging) {
            console.log("DROP ITEM - sending command");
        }
        this.strategy.handle_simple_action(
            "dropItem",
            { type: "dropItem", amount: 1 },
            { amount: 1 }
        );
    }

    public handle_swap_hands(): void {
        if (this.state.enable_logging) {
            console.log("SWAP HANDS - sending command");
        }
        this.strategy.handle_simple_action("swapHands", { type: "swapHands" });
    }

    public handle_clear_path(): void {
        (this.controller.look_path_tracker as LookPathTracker).clear_history();
        if (this.state.enable_logging) {
            console.log("Look path cleared!");
        }
    }

    public process_actions(actions: ActionTuple[]): void {
        for (const [action_name, value] of actions) {
            const handler = this._action_handlers[action_name];
            if (handler) {
                handler(value);
            } else {
                if (action_name && this.state.enable_logging) {
                    console.warn(`Warning: No handler for action '${action_name}'`);
                }
            }
        }
    }

    /**
     * Handles keyboard shortcuts that require edge detection (press/release).
     * @param keys_pressed - A record of currently pressed keys (e.g., `{'KeyQ': true, 'Digit1': false}`).
     *                       Uses JavaScript KeyboardEvent.code values.
     */
    public process_edge_detections(keys_pressed: KeyStates): void {
        // Hotbar slots (1-9 keys)
        for (let i = 0; i < 9; i++) {
            const key_code = `Digit${i + 1}`; // e.g., 'Digit1', 'Digit2'
            const key_name = `hotbar_${i}`;
            const [just_pressed] = this._detect_key_edge(key_name, keys_pressed[key_code] || false);
            if (just_pressed) {
                this.handle_hotbar_slot(i);
            }
        }

        // Drop item (Q key)
        const [drop_just_pressed] = this._detect_key_edge("drop_item", keys_pressed['KeyQ'] || false);
        if (drop_just_pressed) {
            this.handle_drop_item();
        }

        // Swap hands (F key)
        const [swap_just_pressed] = this._detect_key_edge("swap_hands", keys_pressed['KeyF'] || false);
        if (swap_just_pressed) {
            this.handle_swap_hands();
        }

        // Inventory (E key)
        const [inventory_just_pressed] = this._detect_key_edge("inventory", keys_pressed['KeyE'] || false);
        if (inventory_just_pressed) {
            this.handle_inventory();
        }

        // Context debug (G key) - Assuming no direct action, just logging or internal state change
        const [debug_just_pressed] = this._detect_key_edge("context_debug", keys_pressed['KeyG'] || false);
        if (debug_just_pressed && this.state.enable_logging) {
            console.log("Context debug key (G) pressed.");
            // Add any specific debug logic here if needed
        }
    }

    /**
     * Logs an MCP-formatted command if logging is enabled in the controller state.
     * @param tool - The name of the MCP tool.
     * @param parameters - The parameters for the MCP tool.
     */
    public _log_mcp_command(tool: string, parameters: Record<string, any>): void {
        if (this.state.enable_logging) {
            const mcp_command = { tool, parameters };
            console.log(`LOGGED: ${JSON.stringify(mcp_command)}`);
        }
    }
}
