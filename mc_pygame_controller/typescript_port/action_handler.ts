// Basic type definitions for Pygame and websockets
// These are simplified and may need to be expanded based on actual usage
type PygameKeyConstant = number; // Example: pygame.K_1
type PygameScancodeWrapper = Record<PygameKeyConstant, boolean>; // Mock for keys_pressed

interface WebSocketServerProtocol {
    send(data: string): Promise<void>;
    // Add other methods/properties if used by ActionHandler's dependencies
}

// Interface for ControllerState
interface ControllerState {
    running: boolean;
    connected: boolean;
    mode: string; // "pygame" or "mcp"
    sensitivity: number;
    enable_logging: boolean;
    data_collection_enabled: boolean;
    conversation_session_active: boolean;
    current_task_description: string;
    session_start_time: number;
    inventory_open: boolean;
    current_context: string; // "world" or "inventory"
    last_inventory_toggle_time: number;
    current_hotbar_slot: number;
    last_hotbar_slot: number;
    last_movement: [number, number];
    last_moved_in_mcp_mode: number;
    action_states: Record<string, { active: boolean; start_time?: number | null }>;
    key_states: Record<string, boolean>;
    last_key_states: Record<string, boolean>;
    camera_was_clicking: boolean;
    websocket?: WebSocketServerProtocol | null;
    connection_thread?: any; // Consider a more specific type if possible
    loop?: any; // Consider a more specific type if possible
    mcp_executor?: any; // Consider a more specific type if possible (e.g., MinecraftControllerInterface)
    event_loop?: any;
    event_queue?: any;
    command_queue?: any;
    result_queue?: any;
    chain?: any; // Consider a more specific type (e.g., PygameMCPAsyncMessageChain)
    servers: any[]; // Consider a more specific type for server objects
}

// Interface for ModeStrategy
interface ModeStrategy {
    handle_movement(x: number, z: number): void;
    handle_timed_action(
        action_name: string,
        duration: string,
        pygame_down_cmd?: Record<string, any>,
        pygame_up_cmd?: Record<string, any>,
        kwargs?: Record<string, any>
    ): void;
    handle_toggle_action(action_name: string, state: boolean, pygame_control?: string): void;
    handle_simple_action(action_name: string, pygame_cmd?: Record<string, any>, params?: Record<string, any>): void;
    connect(): void;
    process_continuous_state(mouse_pos: any, mouse_pressed: any, keys_pressed: any): void;
    // Add other methods if ActionHandler depends on them
}

// Interface for UIManager (based on its usage in ActionHandler and dependencies)
interface UiManager {
    left_click_btn?: { is_pressed: boolean };
    right_click_btn?: { is_pressed: boolean };
    // Add other properties/methods of UIManager if ActionHandler interacts with them
}

// Interface for LookPathTracker (based on its usage in ActionHandler's dependencies)
interface LookPathTracker {
    add_movement(delta_x: number, delta_y: number): void;
    clear_history(): void;
    // Add other properties/methods if ActionHandler interacts with them
}

// Interface for MinecraftController
// This will be a simplified version focusing on what ActionHandler interacts with
interface MinecraftController {
    state: ControllerState; // Added state property
    strategy: ModeStrategy; // Added strategy property
    ui_manager: UiManager; // Added ui_manager property
    look_path_tracker: LookPathTracker; // Added look_path_tracker property
    _handle_camera_drag_state(pressed: boolean): void;
    handle_test_status(): void;
    handle_save_demonstration(): void;
    send_command_sync(command: Record<string, any>): void;
    // Add other methods/properties if ActionHandler directly uses them
}

// Placeholder for Pygame key constants. These will need to be properly mapped.
const PygameK = {
    K_1: 49, K_2: 50, K_3: 51, K_4: 52, K_5: 53, K_6: 54, K_7: 55, K_8: 56, K_9: 57,
    K_q: 81, K_f: 70, K_e: 69, K_g: 71, // Common letter keys by ASCII, check if correct
};

export class ActionHandler {
    private state: ControllerState;
    private strategy: ModeStrategy;
    private controller: MinecraftController;
    private _last_jump_state: boolean = false;
    private _action_handlers: Record<string, (value: any) => void>;

    constructor(
        controller_state: ControllerState,
        mode_strategy: ModeStrategy,
        controller: MinecraftController
    ) {
        this.state = controller_state;
        this.strategy = mode_strategy;
        this.controller = controller;

        this._action_handlers = {
            movement: (v: [number, number] | undefined) => { if (v) this.handle_movement(v[0], v[1]); },
            camera_look: (v: [number, number] | undefined) => { if (v) this.handle_camera_look(v[0], v[1]); },
            camera_drag_state: (v: [boolean] | undefined) => { if (v) this.controller._handle_camera_drag_state(v[0]); },
            left_click: (v: boolean) => this.handle_left_click(v),
            right_click: (v: boolean) => this.handle_right_click(v),
            left_click_keyboard: (v: boolean) => this._handle_left_click_keyboard(v),
            right_click_keyboard: (v: boolean) => this._handle_right_click_keyboard(v),
            jump: (v: boolean) => this._handle_jump_action(v),
            jump_keyboard: (v: boolean) => this._handle_jump_action(v),
            sneak_toggled: (v: boolean) => this.handle_sneak(v),
            sprint_toggled: (v: boolean) => this.handle_sprint(v),
            inventory_pressed: (_: any) => this.handle_inventory(),
            drop_item_pressed: (_: any) => this.handle_drop_item(),
            swap_hands_pressed: (_: any) => this.handle_swap_hands(),
            clear_path_pressed: (_: any) => this.handle_clear_path(),
            test_status_pressed: (_: any) => this.controller.handle_test_status(),
            save_demo_pressed: (_: any) => this.controller.handle_save_demonstration(),
            hotbar_slot_pressed: (v: number) => this.handle_hotbar_slot(v),
        };
    }

    // --- Helper methods for action dispatch dictionary ---
    private _handle_jump_action(state: boolean): void {
        if (state !== this._last_jump_state) {
            this.handle_jump(state);
            this._last_jump_state = state;
        }
    }

    private _handle_left_click_keyboard(keyboard_state: boolean): void {
        const button_pressed = this.controller.ui_manager?.left_click_btn;
        const button_state = button_pressed ? button_pressed.is_pressed : false;
        const combined_state = keyboard_state || button_state;
        this.handle_left_click(combined_state);
    }

    private _handle_right_click_keyboard(keyboard_state: boolean): void {
        const button_pressed = this.controller.ui_manager?.right_click_btn;
        const button_state = button_pressed ? button_pressed.is_pressed : false;
        const combined_state = keyboard_state || button_state;
        this.handle_right_click(combined_state);
    }

    private _calculate_duration(start_time?: number | null): string {
        if (!start_time) {
            return "medium";
        }
        const duration_ms = Math.floor((Date.now() / 1000 - start_time) * 1000);

        if (duration_ms < 150) return "very_short"; // 100ms
        if (duration_ms < 750) return "short"; // 500ms
        if (duration_ms < 1500) return "medium"; // 1000ms
        if (duration_ms < 3500) return "long"; // 2000ms
        if (duration_ms < 7500) return "very_long"; // 5000ms
        return "very_very_long"; // 10000ms
    }

    private _handle_timed_action(
        action_name: string,
        pressed: boolean,
        pygame_down_cmd: Record<string, any>,
        pygame_up_cmd: Record<string, any>,
        mcp_tool: string,
        mcp_params_func?: (duration: string) => Record<string, any>
    ): void {
        const state = this.state.action_states[action_name];
        if (!state) {
            if (this.state.enable_logging) {
                console.warn(`Action state for '${action_name}' not found.`);
            }
            return;
        }

        if (pressed && !state.active) {
            if (this.state.enable_logging) {
                console.log(\`\${action_name.toUpperCase()} DOWN - sending command\`);
      }
      state.start_time = Date.now() / 1000;
      state.active = true;
    } else if (!pressed && state.active) {
      if (this.state.enable_logging) {
        console.log(\`\${action_name.toUpperCase()} UP - sending command\`);
      }
      const duration = this._calculate_duration(state.start_time);
      state.start_time = null;

      const kwargs = mcp_params_func ? mcp_params_func(duration) : {};
      this.strategy.handle_timed_action(
        mcp_tool,
        duration,
        pygame_down_cmd,
        pygame_up_cmd,
        kwargs
      );
      state.active = false;
    }
  }

  private _handle_toggle_action(
    action_name: string,
    toggled: boolean,
    pygame_control: string,
    mcp_tool: string
  ): void {
    const state = this.state.action_states[action_name];
    if (!state) {
        if (this.state.enable_logging) {
            console.warn(`Action state for '${action_name}' not found.`);
        }
        return;
    }

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

  // --- Action Handlers ---
  public handle_movement(x: number, y: number): void {
    const movement_x = x;
    const movement_z = y;

    if (
      Math.abs(movement_x - this.state.last_movement[0]) > 0.1 ||
      Math.abs(movement_z - this.state.last_movement[1]) > 0.1
    ) {
      this.strategy.handle_movement(movement_x, movement_z);
      this.state.last_movement = [movement_x, movement_z];
    }
  }

  public handle_camera_look(delta_x: number, delta_y: number): void {
    if (delta_x !== 0 || delta_y !== 0) {
      const scaled_x = delta_x * 2;
      const scaled_y = delta_y * 2;

      this.controller.look_path_tracker.add_movement(scaled_x, scaled_y);

      if (this.state.mode === "pygame") {
        const command = { type: "look", movementX: scaled_x, movementY: scaled_y };
        this.controller.send_command_sync(command);
      }
    }
  }

  public handle_left_click(pressed: boolean, inventory_mode: boolean = false): void {
    // inventory_mode is ignored as per Python code comments
    this._handle_timed_action(
      "left_click",
      pressed,
      { type: "leftDown" },
      { type: "leftUp" },
      "leftClick"
    );
  }

  public handle_right_click(pressed: boolean, inventory_mode: boolean = false): void {
    // inventory_mode is ignored
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
    this.state.last_inventory_toggle_time = Date.now() / 1000;

    if (this.state.enable_logging) {
      console.log(
        \`INVENTORY \${this.state.inventory_open ? "OPENED" : "CLOSED"} - context: \${this.state.current_context}\`
      );
    }

    this.strategy.handle_simple_action(
        "toggleInventory",
        { type: "inventory" }
    );
  }

  public handle_hotbar_slot(slot: number): void {
    if (slot >= 0 && slot <= 8 && slot !== this.state.last_hotbar_slot) {
      if (this.state.enable_logging) {
        console.log(\`HOTBAR SLOT \${slot + 1} - sending command\`);
      }
      this.strategy.handle_simple_action(
        "setHotbarSlot",
        { type: "setHotbarSlot", slot: slot },
        { slot: slot }
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
    this.strategy.handle_simple_action(
        "swapHands",
        { type: "swapHands" }
    );
  }

  public handle_clear_path(): void {
    this.controller.look_path_tracker.clear_history();
    if (this.state.enable_logging) {
      console.log("Look path cleared!");
    }
  }

  public process_actions(actions: Array<[string, any]>): void {
    for (const [action_name, value] of actions) {
      const handler = this._action_handlers[action_name];
      if (handler) {
        handler(value);
      } else {
        if (action_name && this.state.enable_logging) {
          console.warn(\`Warning: No handler for action '\${action_name}'\`);
        }
      }
    }
  }

  // Type for keys_pressed needs to be PygameScancodeWrapper or equivalent
  public process_edge_detections(keys_pressed: PygameScancodeWrapper): void {
    // Handle hotbar slot shortcuts (1-9 keys)
    [
      PygameK.K_1, PygameK.K_2, PygameK.K_3, PygameK.K_4, PygameK.K_5,
      PygameK.K_6, PygameK.K_7, PygameK.K_8, PygameK.K_9,
    ].forEach((key, i) => {
      const key_name = \`hotbar_\${i}\`;
      const [just_pressed, _] = this._detect_key_edge(key_name, keys_pressed[key]);
      if (just_pressed) {
        this.handle_hotbar_slot(i);
      }
    });

    // Handle drop item (Q key)
    let [just_pressed_q, _q] = this._detect_key_edge("drop_item", keys_pressed[PygameK.K_q]);
    if (just_pressed_q) {
      this.handle_drop_item();
    }

    // Handle swap hands (F key)
    let [just_pressed_f, _f] = this._detect_key_edge("swap_hands", keys_pressed[PygameK.K_f]);
    if (just_pressed_f) {
      this.handle_swap_hands();
    }

    // Handle inventory (E key)
    let [just_pressed_e, _e] = this._detect_key_edge("inventory", keys_pressed[PygameK.K_e]);
    if (just_pressed_e) {
      this.handle_inventory();
    }

    // Handle context debug (G key) - assuming this is just for logging or internal state
    this._detect_key_edge("context_debug", keys_pressed[PygameK.K_g]);
  }

  private _log_mcp_command(tool: string, parameters: Record<string, any>): void {
    if (this.state.enable_logging) {
      const mcp_command = { tool, parameters };
      console.log(\`LOGGED: \${JSON.stringify(mcp_command)}\`);
    }
  }
}
