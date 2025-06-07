// src/ui.ts

import { Rect, Point, Color, WHITE, GRAY, LIGHT_GRAY, DARK_GRAY, BLUE, GREEN, YELLOW, PURPLE } from "./constants";
import { LookPathTracker } from './look-path-tracker';

function isPointInRect(point: Point, rect: Rect): boolean {
  return point.x >= rect.x && point.x <= rect.x + rect.width &&
         point.y >= rect.y && point.y <= rect.y + rect.height;
}

export class Button {
  rect: Rect;
  text: string;
  color: Color;
  textColor: Color;
  isPressed: boolean = false;
  font: string = "20px sans-serif";
  onClick: (() => void) | null = null;
  
  constructor(rect: Rect, text: string, color: Color = GRAY, textColor: Color = WHITE, onClick: (() => void) | null = null) {
    this.rect = rect;
    this.text = text;
    this.color = color;
    this.textColor = textColor;
    this.onClick = onClick;
  }

  handleEvent(type: 'mousedown' | 'mouseup' | 'mousemove', pos: Point): boolean {
    const wasPressed = this.isPressed;
    
    if (type === 'mousedown' && isPointInRect(pos, this.rect)) {
      this.isPressed = true;
    } else if (type === 'mouseup') {
      if (this.isPressed && isPointInRect(pos, this.rect)) {
        if(this.onClick) this.onClick();
      }
      this.isPressed = false;
    }
    
    // Return true if the button was just clicked
    const justClicked = this.isPressed && !wasPressed;
    if (justClicked && this.onClick) {
        // For buttons that trigger on press-down, not release
        // This behavior is specific to how the original python code was structured
    }
    return justClicked;
  }

  draw(ctx: CanvasRenderingContext2D) {
    const color = this.isPressed ? LIGHT_GRAY : this.color;
    ctx.fillStyle = color;
    ctx.fillRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    ctx.strokeStyle = WHITE;
    ctx.lineWidth = 2;
    ctx.strokeRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);

    ctx.fillStyle = this.textColor;
    ctx.font = this.font;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(this.text, this.rect.x + this.rect.width / 2, this.rect.y + this.rect.height / 2);
  }
}

export class ToggleButton extends Button {
  isToggled: boolean = false;

  constructor(rect: Rect, text: string, color: Color = GRAY, textColor: Color = WHITE, onToggle: ((toggled: boolean) => void) | null = null) {
    super(rect, text, color, textColor);
    this.onClick = () => {
        this.isToggled = !this.isToggled;
        if(onToggle) onToggle(this.isToggled);
    }
  }

  draw(ctx: CanvasRenderingContext2D) {
    const color = this.isToggled ? GREEN : (this.isPressed ? LIGHT_GRAY : this.color);
    ctx.fillStyle = color;
    ctx.fillRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    ctx.strokeStyle = WHITE;
    ctx.lineWidth = 2;
    ctx.strokeRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);

    ctx.fillStyle = this.textColor;
    ctx.font = this.font;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(this.text, this.rect.x + this.rect.width / 2, this.rect.y + this.rect.height / 2);
  }
}

export class VirtualJoystick {
    center: Point;
    radius: number;
    knobPos: Point;
    knobRadius: number;
    isPressed: boolean = false;

    constructor(center: Point, radius: number) {
        this.center = center;
        this.radius = radius;
        this.knobPos = { ...center };
        this.knobRadius = radius / 3;
    }

    handleEvent(type: 'mousedown' | 'mouseup' | 'mousemove', pos: Point): Point {
        const distance = Math.hypot(pos.x - this.center.x, pos.y - this.center.y);

        if (type === 'mousedown' && distance <= this.radius) {
            this.isPressed = true;
        }

        if (type === 'mouseup') {
            this.isPressed = false;
        }

        if (!this.isPressed) {
            this.knobPos = { ...this.center };
            return { x: 0, y: 0 };
        }

        if (distance <= this.radius) {
            this.knobPos = { ...pos };
        } else {
            const angle = Math.atan2(pos.y - this.center.y, pos.x - this.center.x);
            this.knobPos.x = this.center.x + Math.cos(angle) * this.radius;
            this.knobPos.y = this.center.y + Math.sin(angle) * this.radius;
        }

        const normX = (this.knobPos.x - this.center.x) / this.radius;
        const normY = (this.knobPos.y - this.center.y) / this.radius;
        return { x: normX, y: normY };
    }

    draw(ctx: CanvasRenderingContext2D) {
        // Draw outer circle
        ctx.strokeStyle = this.isPressed ? BLUE : GRAY;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(this.center.x, this.center.y, this.radius, 0, 2 * Math.PI);
        ctx.stroke();

        // Draw knob
        ctx.fillStyle = this.isPressed ? YELLOW : LIGHT_GRAY;
        ctx.beginPath();
        ctx.arc(this.knobPos.x, this.knobPos.y, this.knobRadius, 0, 2 * Math.PI);
        ctx.fill();
    }
}

export class KeyboardMovement {
    private keys: { [key: string]: boolean } = {
        'w': false, 'a': false, 's': false, 'd': false
    };

    constructor() {
        window.addEventListener('keydown', (e) => this.handleKey(e.key, true));
        window.addEventListener('keyup', (e) => this.handleKey(e.key, false));
    }

    private handleKey(key: string, isPressed: boolean) {
        const lowerKey = key.toLowerCase();
        if (lowerKey in this.keys) {
            this.keys[lowerKey] = isPressed;
        }
    }
    
    isAnyKeyPressed(): boolean {
        return this.keys['w'] || this.keys['a'] || this.keys['s'] || this.keys['d'];
    }

    getMovement(): Point {
        let normX = 0;
        let normY = 0;

        if (this.keys['a']) normX -= 1;
        if (this.keys['d']) normX += 1;
        if (this.keys['w']) normY -= 1; // W = forward = negative Y
        if (this.keys['s']) normY += 1; // S = backward = positive Y

        const length = Math.hypot(normX, normY);
        if (length > 1) {
            normX /= length;
            normY /= length;
        }

        return { x: normX, y: normY };
    }
}

export class TouchArea {
  rect: Rect;
  private lastMousePos: Point | null = null;
  isTouching: boolean = false;

  constructor(rect: Rect) {
    this.rect = rect;
  }

  handleEvent(type: 'mousedown' | 'mouseup' | 'mousemove', pos: Point): Point {
    const touching = isPointInRect(pos, this.rect);
    
    if (type === 'mousedown' && touching) {
        this.isTouching = true;
        this.lastMousePos = { ...pos };
        return { x: 0, y: 0 };
    }

    if (type === 'mouseup') {
        this.isTouching = false;
        this.lastMousePos = null;
    }
    
    if (this.isTouching && type === 'mousemove') {
        if(this.lastMousePos) {
            const deltaX = pos.x - this.lastMousePos.x;
            const deltaY = pos.y - this.lastMousePos.y;
            this.lastMousePos = { ...pos };
            return { x: deltaX, y: deltaY };
        }
    }
    
    return { x: 0, y: 0 };
  }
  
  draw(ctx: CanvasRenderingContext2D) {
    const color = this.isTouching ? GREEN : DARK_GRAY;
    
    ctx.fillStyle = this.isTouching ? 'rgba(0, 64, 0, 0.5)' : 'rgba(32, 32, 32, 0.5)';
    ctx.fillRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);

    ctx.fillStyle = WHITE;
    ctx.font = "28px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("Camera Look Area - Drag to Look Around", this.rect.x + this.rect.width / 2, this.rect.y + this.rect.height / 2);
  }
}

export class LookPathVisualizationArea {
    rect: Rect;
    private origin: Point;
    private scale = 0.5;
    private gridSize = 20;
    private font = "16px sans-serif";

    constructor(rect: Rect) {
        this.rect = rect;
        this.origin = {
            x: rect.x + rect.width / 2,
            y: rect.y + rect.height / 2
        };
    }

    draw(ctx: CanvasRenderingContext2D, pathTracker: LookPathTracker) {
        ctx.save();
        
        // Background
        ctx.fillStyle = 'rgba(20, 20, 20, 0.8)';
        ctx.fillRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
        ctx.strokeStyle = WHITE;
        ctx.lineWidth = 2;
        ctx.strokeRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);

        this.drawGrid(ctx);
        this.drawAxes(ctx);
        this.drawOrigin(ctx);

        if (pathTracker.positions.length > 0) {
            this.drawPath(ctx, pathTracker.positions);
        }

        this.drawInfo(ctx, pathTracker);

        ctx.restore();
    }
    
    private drawGrid(ctx: CanvasRenderingContext2D) {
        ctx.strokeStyle = 'rgba(40, 40, 40, 0.8)';
        ctx.lineWidth = 1;
        for (let x = this.rect.x; x < this.rect.x + this.rect.width; x += this.gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, this.rect.y);
            ctx.lineTo(x, this.rect.y + this.rect.height);
            ctx.stroke();
        }
        for (let y = this.rect.y; y < this.rect.y + this.rect.height; y += this.gridSize) {
            ctx.beginPath();
            ctx.moveTo(this.rect.x, y);
            ctx.lineTo(this.rect.x + this.rect.width, y);
            ctx.stroke();
        }
    }
    
    private drawAxes(ctx: CanvasRenderingContext2D) {
        ctx.strokeStyle = GRAY;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(this.rect.x, this.origin.y);
        ctx.lineTo(this.rect.x + this.rect.width, this.origin.y);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(this.origin.x, this.rect.y);
        ctx.lineTo(this.origin.x, this.rect.y + this.rect.height);
        ctx.stroke();
    }
    
    private drawOrigin(ctx: CanvasRenderingContext2D) {
        ctx.fillStyle = RED;
        ctx.beginPath();
        ctx.arc(this.origin.x, this.origin.y, 6, 0, 2 * Math.PI);
        ctx.fill();
        ctx.strokeStyle = WHITE;
        ctx.lineWidth = 2;
        ctx.stroke();
    }
    
    private drawPath(ctx: CanvasRenderingContext2D, positions: any[]) {
        if (positions.length < 2) return;
        
        ctx.strokeStyle = CYAN;
        ctx.lineWidth = 2;
        ctx.beginPath();
        const startX = this.origin.x + positions[0].x * this.scale;
        const startY = this.origin.y + positions[0].y * this.scale;
        ctx.moveTo(startX, startY);

        for (const pos of positions) {
             const x = this.origin.x + pos.x * this.scale;
             const y = this.origin.y + pos.y * this.scale;
             ctx.lineTo(x, y);
        }
        ctx.stroke();
        
        // Draw current position marker
        const lastPos = positions[positions.length - 1];
        const lastX = this.origin.x + lastPos.x * this.scale;
        const lastY = this.origin.y + lastPos.y * this.scale;
        ctx.fillStyle = PURPLE;
        ctx.beginPath();
        ctx.arc(lastX, lastY, 5, 0, 2 * Math.PI);
        ctx.fill();
    }

    private drawInfo(ctx: CanvasRenderingContext2D, pathTracker: LookPathTracker) {
        const stats = pathTracker.get_current_stats();
        const infoRect = { x: this.rect.x + 5, y: this.rect.y + 5, width: 200, height: 180 };
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(infoRect.x, infoRect.y, infoRect.width, infoRect.height);
        
        ctx.fillStyle = WHITE;
        ctx.font = this.font;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';

        let yOffset = infoRect.y + 8;
        const write = (text: string) => {
            ctx.fillText(text, infoRect.x + 5, yOffset);
            yOffset += 18;
        };

        if (!stats) {
            write("No movements recorded");
            return;
        }

        write(`Movements: ${stats.num_movements}`);
        const [totalX, totalY] = stats.total_displacement;
        write(`Position: (${totalX.toFixed(0)}, ${totalY.toFixed(0)})`);
        write(`Overall: ${stats.overall_angle_deg.toFixed(1)}° (${stats.compass_direction})`);
        write(`Efficiency: ${(stats.path_efficiency * 100).toFixed(1)}%`);
    }
}
