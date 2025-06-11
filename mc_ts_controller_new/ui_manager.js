import { toCssColor, COLORS, WINDOW_WIDTH, WINDOW_HEIGHT } from "./porting.js";
import { VirtualJoystick, KeyboardMovement, TouchArea, Button, ToggleButton } from "./ui_elements.js";
// === START_OF: ui_manager.py (Inferred Implementation)
// =======================================================================
class UIManager {
    constructor(surface, state, lookPathTracker) {
        this.surface = surface;
        this.state = state;
        this.lookPathTracker = lookPathTracker;
        this.font = {
            render: (text, [x, y], color) => {
                this.surface.ctx.fillStyle = toCssColor(color);
                this.surface.ctx.font = '16px sans-serif';
                this.surface.ctx.fillText(text, x, y);
            }
        };
        this.elements = {};
        this._setup_ui();
    }

    _setup_ui() {
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
    
    process_events(events) {
        // In the browser, most events are handled by global listeners.
        // This can be used for things that require event objects, like key presses.
        const actions = [];
        for (const event of events) {
            if (event.type === 'keydown') {
                if (event.key === Keys.K_F5) actions.push(['save_demo_pressed', true]); // F5 to start
            }
        }
        return actions;
    }

    process_inputs(mousePos, mousePressed, keysPressed) {
        const actions = [];

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

        let final_move = [0, 0];
        if (Math.abs(joy_move[0]) > 0.1 || Math.abs(joy_move[1]) > 0.1) {
            final_move = joy_move;
        } else if (Math.abs(key_move[0]) > 0.1 || Math.abs(key_move[1]) > 0.1) {
            final_move = key_move;
        }
        actions.push(['movement', final_move]);

        // Camera
        const camera_delta = this.camera_area.handle_input(mousePos, mousePressed, this.lookPathTracker);
        if (camera_delta) {
            actions.push(['camera_look', camera_delta]);
        }
        actions.push(['camera_drag_state', mousePressed]);
        
        return actions;
    }

    process_keyboard_shortcuts(keys) {
        const actions = [];
        if (keys[Keys.K_SPACE]) actions.push(['jump_keyboard', true]);
        else actions.push(['jump_keyboard', false]);
        
        // These are handled by edge detection in ActionHandler now
        // if (keys[Keys.K_e]) actions.push(['inventory_pressed', true]); 
        // if (keys[Keys.K_q]) actions.push(['drop_item_pressed', true]);
        // etc...
        return actions;
    }

    update() {
        // For animations or time-based updates
    }
    
    draw() {
        // Clear screen
        this.surface.ctx.fillStyle = toCssColor(COLORS.DARK_GRAY);
        this.surface.ctx.fillRect(0, 0, this.surface.width, this.surface.height);
        
        // Draw all elements
        for (const el of Object.values(this.elements)) {
            el.draw(this.surface, this.font);
        }
        
        // Draw Status
        document.getElementById('connection-status').textContent = this.state.connected ? 'Connected' : 'Disconnected';
        document.getElementById('connection-status').style.color = toCssColor(this.state.connected ? COLORS.CONNECTION_STATUS_OK : COLORS.CONNECTION_STATUS_FAIL);
        document.getElementById('mode-status').textContent = this.state.mode.toUpperCase();
    }
}
// =======================================================================
export { UIManager };
// === END_OF: ui_manager.py
