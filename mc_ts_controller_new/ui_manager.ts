import { toCssColor, COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, Keys } from "./porting.js";
import { VirtualJoystick, KeyboardMovement, TouchArea, Button, ToggleButton } from "./ui_elements.js";
import { LookPathTracker } from "./look_path.js";

// Type definitions for UI Manager
interface Surface {
    ctx: CanvasRenderingContext2D;
    width: number;
    height: number;
}

interface Font {
    render: (text: string, position: [number, number], color: number[]) => void;
}

interface State {
    connected: boolean;
    mode: string;
}

interface Event {
    type: string;
    key?: string;
}

type ActionType = 
    | ['save_demo_pressed', boolean]
    | ['left_click', boolean]
    | ['right_click', boolean]
    | ['jump', boolean]
    | ['sneak_toggled', boolean]
    | ['sprint_toggled', boolean]
    | ['movement', [number, number]]
    | ['camera_look', [number, number]]
    | ['camera_drag_state', boolean]
    | ['jump_keyboard', boolean];

interface UIElements {
    movement_joystick: VirtualJoystick;
    camera_area: TouchArea;
    left_click_btn: Button;
    right_click_btn: Button;
    jump_btn: Button;
    sneak_toggle: ToggleButton;
    sprint_toggle: ToggleButton;
}

interface KeysPressed {
    [key: string]: boolean;
}

// === START_OF: ui_manager.py (Inferred Implementation)
// =======================================================================
class UIManager {
    private surface: Surface;
    private state: State;
    private lookPathTracker: LookPathTracker;
    private font: Font;
    private elements: UIElements;
    movement_joystick: VirtualJoystick;
    keyboard_movement: KeyboardMovement;
    camera_area: TouchArea;
    private left_click_btn: Button;
    private right_click_btn: Button;
    private jump_btn: Button;
    private sneak_toggle: ToggleButton;
    private sprint_toggle: ToggleButton;

    constructor(surface: Surface, state: State, lookPathTracker: LookPathTracker) {
        this.surface = surface;
        this.state = state;
        this.lookPathTracker = lookPathTracker;
        this.font = {
            render: (text: string, [x, y]: [number, number], color: number[]): void => {
                this.surface.ctx.fillStyle = toCssColor(color);
                this.surface.ctx.font = '16px sans-serif';
                this.surface.ctx.fillText(text, x, y);
            }
        };
        this._setup_ui();
    }

    private _setup_ui(): void {
        this.movement_joystick = new VirtualJoystick(150, WINDOW_HEIGHT - 150, 70);
        this.keyboard_movement = new KeyboardMovement();
        
        this.camera_area = new TouchArea(300, 100, WINDOW_WIDTH - 350, WINDOW_HEIGHT - 200);

        this.left_click_btn = new Button(50, 100, 100, 50, "Left Click", this.font);
        this.right_click_btn = new Button(50, 160, 100, 50, "Right Click", this.font);
        this.jump_btn = new Button(50, 220, 100, 50, "Jump", this.font);
        this.sneak_toggle = new ToggleButton(50, 280, 100, 50, "Sneak", this.font);
        this.sprint_toggle = new ToggleButton(50, 340, 100, 50, "Sprint", this.font);

        this.elements = {
            movement_joystick: this.movement_joystick,
            camera_area: this.camera_area,
            left_click_btn: this.left_click_btn,
            right_click_btn: this.right_click_btn,
            jump_btn: this.jump_btn,
            sneak_toggle: this.sneak_toggle,
            sprint_toggle: this.sprint_toggle,
        };
    }
    
    process_events(events: Event[]): ActionType[] {
        // In the browser, most events are handled by global listeners.
        // This can be used for things that require event objects, like key presses.
        const actions: ActionType[] = [];
        for (const event of events) {
            if (event.type === 'keydown') {
                if (event.key === Keys.K_F5) actions.push(['save_demo_pressed', true]); // F5 to start
            }
        }
        return actions;
    }

    process_inputs(mousePos: [number, number], mousePressed: boolean, keysPressed: KeysPressed): ActionType[] {
        const actions: ActionType[] = [];

        // UI Buttons
        const leftClickState = this.left_click_btn.handle_input(mousePos, mousePressed);
        if (leftClickState) actions.push(['left_click', leftClickState === 'down']);
        
        const rightClickState = this.right_click_btn.handle_input(mousePos, mousePressed);
        if (rightClickState) actions.push(['right_click', rightClickState === 'down']);
        
        const jumpState = this.jump_btn.handle_input(mousePos, mousePressed);
        if (jumpState) actions.push(['jump', jumpState === 'down']);
        
        if (this.sneak_toggle.handle_input(mousePos, mousePressed) === 'toggled') {
            actions.push(['sneak_toggled', this.sneak_toggle.toggled]);
        }
        if (this.sprint_toggle.handle_input(mousePos, mousePressed) === 'toggled') {
            actions.push(['sprint_toggled', this.sprint_toggle.toggled]);
        }

        // Joystick and Keyboard Movement
        const joy_move = this.movement_joystick.handle_input(mousePos, mousePressed);
        const key_move = this.keyboard_movement.handle_keyboard(keysPressed);

        let final_move: [number, number] = [0, 0];
        if (Math.abs(joy_move[0]) > 0.1 || Math.abs(joy_move[1]) > 0.1) {
            final_move = joy_move;
        } else if (Math.abs(key_move[0]) > 0.1 || Math.abs(key_move[1]) > 0.1) {
            final_move = key_move;
        }
        actions.push(['movement', final_move]);

        // Camera
        const camera_delta = this.camera_area.handle_input(mousePos, mousePressed, this.lookPathTracker);
        if (camera_delta) {
            actions.push(['camera_look', camera_delta as [number, number]]);
        }
        actions.push(['camera_drag_state', mousePressed]);
        
        return actions;
    }

    process_keyboard_shortcuts(keys: KeysPressed): ActionType[] {
        const actions: ActionType[] = [];
        if (keys[Keys.K_SPACE]) actions.push(['jump_keyboard', true]);
        else actions.push(['jump_keyboard', false]);
        
        // These are handled by edge detection in ActionHandler now
        // if (keys[Keys.K_e]) actions.push(['inventory_pressed', true]); 
        // if (keys[Keys.K_q]) actions.push(['drop_item_pressed', true]);
        // etc...
        return actions;
    }

    update(): void {
        // For animations or time-based updates
    }
    
    draw(): void {
        // Clear screen
        this.surface.ctx.fillStyle = toCssColor(COLORS.DARK_GRAY);
        this.surface.ctx.fillRect(0, 0, this.surface.width, this.surface.height);
        
        // Draw all elements
        for (const el of Object.values(this.elements)) {
            el.draw(this.surface, this.font);
        }
        
        // Draw Status
        const connectionStatusElement = document.getElementById('connection-status');
        const modeStatusElement = document.getElementById('mode-status');
        
        if (connectionStatusElement) {
            connectionStatusElement.textContent = this.state.connected ? 'Connected' : 'Disconnected';
            connectionStatusElement.style.color = toCssColor(this.state.connected ? COLORS.CONNECTION_STATUS_OK : COLORS.CONNECTION_STATUS_FAIL);
        }
        
        if (modeStatusElement) {
            modeStatusElement.textContent = this.state.mode.toUpperCase();
        }
    }
}
// =======================================================================
export { UIManager };
export type { Surface, Font, State, Event, ActionType, UIElements, KeysPressed };
// === END_OF: ui_manager.py