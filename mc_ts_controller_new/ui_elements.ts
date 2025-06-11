import { COLORS, Keys } from "./porting.js";

// Type definitions
interface Rect {
    x: number;
    y: number;
    w: number;
    h: number;
}

interface Position {
    x: number;
    y: number;
}

type MousePosition = [number, number];
type JoystickDelta = [number, number];
type CameraDelta = [number, number] | null;
type ButtonState = 'down' | 'up' | 'toggled' | null;

interface Surface {
    draw: {
        rect: (surface: Surface, color: number[] | string, rect: number[], width?: number) => void;
        circle: (surface: Surface, color: number[] | string, center: number[], radius: number) => void;
    };
}

interface Font {
    render: (text: string, position: number[], color: number[] | string) => void;
}

interface LookPathTracker {
    add_movement: (dx: number, dy: number) => void;
}

interface KeysState {
    [key: string]: boolean;
}

// === START_OF: ui_elements.py (Inferred Implementation)
// =======================================================================
abstract class UIElement {
    protected rect: Rect;

    constructor(x: number, y: number, w: number, h: number) {
        this.rect = { x, y, w, h };
    }

    is_hovered(mousePos: MousePosition): boolean {
        const [mx, my] = mousePos;
        return mx >= this.rect.x && mx <= this.rect.x + this.rect.w &&
               my >= this.rect.y && my <= this.rect.y + this.rect.h;
    }

    abstract draw(surface: Surface, font: Font): void;
    
    handle_event(event: any, mousePos: MousePosition): any {
        return null;
    }
}

class Button extends UIElement {
    protected text: string;
    protected font: Font;
    protected is_pressed: boolean;
    protected hovered: boolean;

    constructor(x: number, y: number, w: number, h: number, text: string, font: Font) {
        super(x, y, w, h);
        this.text = text;
        this.font = font;
        this.is_pressed = false;
        this.hovered = false;
    }

    draw(surface: Surface, font: Font): void {
        const color = this.is_pressed ? COLORS.BUTTON_PRESSED : (this.hovered ? COLORS.BUTTON_HOVER : COLORS.BUTTON_IDLE);
        surface.draw.rect(surface, color, [this.rect.x, this.rect.y, this.rect.w, this.rect.h]);
        font.render(this.text, [this.rect.x + 10, this.rect.y + 10], COLORS.TEXT_COLOR);
    }
    
    handle_input(mousePos: MousePosition, mousePressed: boolean): ButtonState {
        this.hovered = this.is_hovered(mousePos);
        const was_pressed = this.is_pressed;
        this.is_pressed = this.hovered && mousePressed;
        if (this.is_pressed && !was_pressed) return 'down';
        if (!this.is_pressed && was_pressed) return 'up';
        return null;
    }
}

class ToggleButton extends Button {
    public toggled: boolean;

    constructor(x: number, y: number, w: number, h: number, text: string, font: Font) {
        super(x, y, w, h, text, font);
        this.toggled = false;
    }

    draw(surface: Surface, font: Font): void {
        let color = this.toggled ? COLORS.TOGGLE_ON : COLORS.TOGGLE_OFF;
        if (this.hovered) {
            color = (color as number[]).map(c => Math.min(255, c + 30));
        }
        surface.draw.rect(surface, color, [this.rect.x, this.rect.y, this.rect.w, this.rect.h]);
        font.render(`${this.text}: ${this.toggled ? 'ON' : 'OFF'}`, [this.rect.x + 10, this.rect.y + 10], COLORS.TEXT_COLOR);
    }
    
    handle_input(mousePos: MousePosition, mousePressed: boolean): ButtonState {
        this.hovered = this.is_hovered(mousePos);
        if (this.hovered && mousePressed && !this.is_pressed) {
            this.is_pressed = true;
            this.toggled = !this.toggled;
            return 'toggled';
        }
        if (!mousePressed) {
            this.is_pressed = false;
        }
        return null;
    }
}

class VirtualJoystick extends UIElement {
    center_x: number;
    center_y: number;
    radius: number;
    knob_x: number;
    knob_y: number;
    private is_dragging: boolean;

    constructor(x: number, y: number, radius: number) {
        super(x - radius, y - radius, radius * 2, radius * 2);
        this.center_x = x;
        this.center_y = y;
        this.radius = radius;
        this.knob_x = x;
        this.knob_y = y;
        this.is_dragging = false;
    }

    draw(surface: Surface, font: Font): void {
        surface.draw.circle(surface, COLORS.JOYSTICK_BASE, [this.center_x, this.center_y], this.radius);
        surface.draw.circle(surface, COLORS.JOYSTICK_KNOB, [this.knob_x, this.knob_y], this.radius / 2);
    }
    
    handle_input(mousePos: MousePosition, mousePressed: boolean): JoystickDelta {
        const [mx, my] = mousePos;
        const dist_from_center = Math.hypot(mx - this.center_x, my - this.center_y);

        if (mousePressed && !this.is_dragging && dist_from_center < this.radius) {
            this.is_dragging = true;
        }

        if (this.is_dragging) {
            if (mousePressed) {
                const angle = Math.atan2(my - this.center_y, mx - this.center_x);
                const clamped_dist = Math.min(dist_from_center, this.radius);
                this.knob_x = this.center_x + Math.cos(angle) * clamped_dist;
                this.knob_y = this.center_y + Math.sin(angle) * clamped_dist;
            } else {
                this.is_dragging = false;
                this.knob_x = this.center_x;
                this.knob_y = this.center_y;
            }
        }
        
        const dx = (this.knob_x - this.center_x) / this.radius;
        const dz = (this.knob_y - this.center_y) / this.radius; // In canvas, Y is down, so this works for forward
        return [dx, dz];
    }
}

class TouchArea extends UIElement {
    is_touching: boolean;
    private last_pos: Position | null;

    constructor(x: number, y: number, w: number, h: number) {
        super(x, y, w, h);
        this.is_touching = false;
        this.last_pos = null;
    }
    
    draw(surface: Surface, font: Font): void {
        surface.draw.rect(surface, COLORS.CAMERA_AREA, [this.rect.x, this.rect.y, this.rect.w, this.rect.h], 2);
        font.render("Look Area", [this.rect.x + 10, this.rect.y + 10], COLORS.TEXT_COLOR);
    }
    
    handle_input(mousePos: MousePosition, mousePressed: boolean, lookPathTracker: LookPathTracker): CameraDelta {
        const [mx, my] = mousePos;
        this.is_touching = this.is_hovered(mousePos);
        
        if (this.is_touching && mousePressed) {
            if (this.last_pos) {
                const dx = mx - this.last_pos.x;
                const dy = my - this.last_pos.y;
                if (dx !== 0 || dy !== 0) {
                    lookPathTracker.add_movement(dx, dy);
                    return [dx, dy]; // Return delta
                }
            }
            this.last_pos = { x: mx, y: my };
        } else {
            this.last_pos = null;
        }
        return null; // No delta
    }
}

class KeyboardMovement {
    handle_keyboard(keys: KeysState): JoystickDelta {
        let x = 0;
        let y = 0;
        if (keys[Keys.K_w]) y -= 1;
        if (keys[Keys.K_s]) y += 1;
        if (keys[Keys.K_a]) x -= 1;
        if (keys[Keys.K_d]) x += 1;
        
        // Normalize
        const len = Math.hypot(x, y);
        if (len > 0) {
            x /= len;
            y /= len;
        }

        return [x, y];
    }
}

// =======================================================================
export { UIElement, Button, ToggleButton, VirtualJoystick, TouchArea, KeyboardMovement };
export type { Rect, Position, MousePosition, JoystickDelta, CameraDelta, ButtonState, Surface, Font, LookPathTracker, KeysState };
// === END_OF: ui_elements.py