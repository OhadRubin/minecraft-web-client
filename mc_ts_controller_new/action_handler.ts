import { Keys } from "./porting.js";

// === START_OF: action_handler.py
// =======================================================================

// Type definitions
interface ActionState {
    active: boolean;
    start_time: number | null;
}

interface ActionStates {
    [key: string]: ActionState;
}

interface ControllerState {
    action_states: ActionStates;
    enable_logging: boolean;
    last_key_states: { [key: string]: boolean };
    last_movement: [number, number];
    mode: string;
    inventory_open: boolean;
    last_hotbar_slot: number;
    current_hotbar_slot: number;
}

interface ModeStrategy {
    handle_timed_action(
        mcp_tool: string,
        duration: DurationString,
        pygame_down_cmd: PygameCommand,
        pygame_up_cmd: PygameCommand,
        kwargs?: Record<string, any>
    ): void;
    handle_toggle_action(mcp_tool: string, toggled: boolean, pygame_control: string): void;
    handle_movement(movement_x: number, movement_z: number): void;
    handle_simple_action(
        mcp_tool: string,
        pygame_cmd: PygameCommand,
        mcp_params?: Record<string, any>
    ): void;
}

interface Controller {
    _handle_camera_drag_state(value: any): void;
    send_command_sync(command: PygameCommand): void;
}

type DurationString = 
    | "very_short" 
    | "short" 
    | "medium" 
    | "long" 
    | "very_long" 
    | "very_very_long";

interface PygameCommand {
    type: string;
    [key: string]: any;
}

type ActionHandlerFunction = (value: any) => void;
type ActionHandlers = { [key: string]: ActionHandlerFunction };

type ActionEntry = [string, any];
type Actions = ActionEntry[];

interface KeyMap {
    [key: string]: {
        key: number;
        handler: () => void;
    };
}

type MCPParamsFunction = (duration: DurationString) => Record<string, any>;

export class ActionHandler {
    private state: ControllerState;
    private strategy: ModeStrategy;
    private controller: Controller;
    private _last_jump_state: boolean;
    private _action_handlers: ActionHandlers;

    constructor(controller_state: ControllerState, mode_strategy: ModeStrategy, controller: Controller) {
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

    private _handle_jump_action(state: boolean): void {
        if (state !== this._last_jump_state) {
            this.handle_jump(state);
            this._last_jump_state = state;
        }
    }

    private _calculate_duration(start_time: number | null): DurationString {
        if (!start_time) return "medium";
        const duration_ms = Date.now() - start_time;
        if (duration_ms < 150) return "very_short";
        if (duration_ms < 750) return "short";
        if (duration_ms < 1500) return "medium";
        if (duration_ms < 3500) return "long";
        if (duration_ms < 7500) return "very_long";
        return "very_very_long";
    }

    private _handle_timed_action(
        action_name: string,
        pressed: boolean,
        pygame_down_cmd: PygameCommand,
        pygame_up_cmd: PygameCommand,
        mcp_tool: string,
        mcp_params_func: MCPParamsFunction | null = null
    ): void {
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

    private _handle_toggle_action(action_name: string, toggled: boolean, pygame_control: string, mcp_tool: string): void {
        const state = this.state.action_states[action_name];
        if (toggled !== state.active) {
            this.strategy.handle_toggle_action(mcp_tool, toggled, pygame_control);
            state.active = toggled;
        }
    }

    private _detect_key_edge(key_name: string, current_state: boolean): [boolean, boolean] {
        const last_state = this.state.last_key_states[key_name] || false;
        this.state.last_key_states[key_name] = current_state;
        const just_pressed = current_state && !last_state;
        const just_released = !current_state && last_state;
        return [just_pressed, just_released];
    }

    handle_movement(x: number, y: number): void {
        const movement_x = x;
        const movement_z = y;
        if (Math.abs(movement_x - this.state.last_movement[0]) > 0.1 || Math.abs(movement_z - this.state.last_movement[1]) > 0.1) {
            this.strategy.handle_movement(movement_x, movement_z);
            this.state.last_movement = [movement_x, movement_z];
        }
    }

    handle_camera_look(delta_x: number, delta_y: number): void {
        if (delta_x !== 0 || delta_y !== 0) {
            const scaled_x = delta_x * 2;
            const scaled_y = delta_y * 2;
            
            // In browser, look path tracker is handled by its own input handler
            // this.controller.look_path_tracker.add_movement(scaled_x, scaled_y);
            
            if (this.state.mode === "pygame") {
                const command: PygameCommand = { type: "look", movementX: scaled_x, movementY: scaled_y };
                this.controller.send_command_sync(command);
            }
        }
    }

    handle_left_click(pressed: boolean): void {
        this._handle_timed_action(
            "left_click",
            pressed,
            { type: "leftDown" },
            { type: "leftUp" },
            "leftClick"
        );
    }

    handle_right_click(pressed: boolean): void {
        this._handle_timed_action(
            "right_click",
            pressed,
            { type: "rightDown" },
            { type: "rightUp" },
            "rightClick"
        );
    }

    handle_jump(pressed: boolean): void {
        this._handle_timed_action(
            "jump",
            pressed,
            { type: "control", control: "jump", state: true },
            { type: "control", control: "jump", state: false },
            "jump"
        );
    }

    handle_sneak(toggled: boolean): void {
        this._handle_toggle_action("sneak", toggled, "sneak", "sneak");
    }

    handle_sprint(toggled: boolean): void {
        this._handle_toggle_action("sprint", toggled, "sprint", "sprint");
    }

    handle_inventory(): void {
        this.state.inventory_open = !this.state.inventory_open;
        if (this.state.enable_logging) {
            console.log(`INVENTORY ${this.state.inventory_open ? 'OPENED' : 'CLOSED'}`);
        }
        this.strategy.handle_simple_action("toggleInventory", { type: "inventory" });
    }

    handle_hotbar_slot(slot: number): void {
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

    handle_drop_item(): void {
        if (this.state.enable_logging) console.log("DROP ITEM");
        this.strategy.handle_simple_action(
            "dropItem",
            { type: "dropItem", amount: 1 },
            { amount: 1 }
        );
    }

    handle_swap_hands(): void {
        if (this.state.enable_logging) console.log("SWAP HANDS");
        this.strategy.handle_simple_action(
            "swapHands",
            { type: "swapHands" }
        );
    }

    process_actions(actions: Actions): void {
        for (const [action_name, value] of actions) {
            const handler = this._action_handlers[action_name];
            if (handler) {
                handler(value);
            } else if (action_name && this.state.enable_logging) {
                console.warn(`Warning: No handler for action '${action_name}'`);
            }
        }
    }

    process_edge_detections(keys_pressed: { [key: number]: boolean }): void {
        // Hotbar slots 1-9
        for (let i = 0; i < 9; i++) {
            const key_name = `hotbar_${i}`;
            const key_code = Keys[`K_${i + 1}` as keyof typeof Keys] as number;
            const [just_pressed] = this._detect_key_edge(key_name, keys_pressed[key_code]);
            if (just_pressed) this.handle_hotbar_slot(i);
        }

        // Other keys
        const key_map: KeyMap = {
            'drop_item': { key: Keys.K_q as number, handler: this.handle_drop_item },
            'swap_hands': { key: Keys.K_f as number, handler: this.handle_swap_hands },
            'inventory': { key: Keys.K_e as number, handler: this.handle_inventory },
        };
        for (const [name, { key, handler }] of Object.entries(key_map)) {
            const [just_pressed] = this._detect_key_edge(name, keys_pressed[key]);
            if (just_pressed) handler.call(this);
        }
    }

    private _log_mcp_command(tool: string, parameters: Record<string, any>): void {
        if (this.state.enable_logging) {
            const mcp_command = { tool, parameters };
            console.log(`LOGGED: ${JSON.stringify(mcp_command)}`);
        }
    }
}
// =======================================================================
export type { 
    ActionState, 
    ActionStates, 
    ControllerState, 
    ModeStrategy, 
    Controller, 
    DurationString, 
    PygameCommand,
    Actions
};
// === END_OF: action_handler.py