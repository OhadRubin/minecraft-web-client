/**
 * GamepadJoystick class for rendering and handling joystick interactions
 * in the gamepad controller interface
 */

import { IGamepadJoystick, GamepadCanvasContext } from './types.js';

export class GamepadJoystick implements IGamepadJoystick {
    public centerX: number;
    public centerY: number;
    public radius: number;
    public stickId: number;
    public label: string;
    public xPos: number; // Normalized position (-1 to 1)
    public yPos: number; // Normalized position (-1 to 1)
    public stickX: number; // Visual position
    public stickY: number; // Visual position
    public dragging: boolean;
    public maxDistance: number;

    private ctx: GamepadCanvasContext;

    constructor(
        x: number, 
        y: number, 
        radius: number, 
        stickId: number, 
        label: string = "",
        ctx: GamepadCanvasContext
    ) {
        this.centerX = x;
        this.centerY = y;
        this.radius = radius;
        this.stickId = stickId;
        this.label = label || `Stick ${stickId}`;
        this.ctx = ctx;

        // Current position (-1 to 1 range)
        this.xPos = 0.0;
        this.yPos = 0.0;

        // Visual stick position
        this.stickX = x;
        this.stickY = y;

        this.dragging = false;
        this.maxDistance = radius - 15;
    }

    /**
     * Check if a point is within the joystick's bounds
     * @param x - X coordinate to check
     * @param y - Y coordinate to check
     * @returns True if the point is within the joystick
     */
    public containsPoint(x: number, y: number): boolean {
        const distance = Math.sqrt((x - this.centerX) ** 2 + (y - this.centerY) ** 2);
        return distance <= this.radius;
    }

    /**
     * Update the joystick position based on mouse/touch coordinates
     * @param mouseX - Mouse X coordinate
     * @param mouseY - Mouse Y coordinate
     */
    public updatePosition(mouseX: number, mouseY: number): void {
        // Calculate offset from center
        let dx = mouseX - this.centerX;
        let dy = mouseY - this.centerY;

        // Limit to circle
        const distance = Math.sqrt(dx ** 2 + dy ** 2);
        if (distance > this.maxDistance) {
            dx = dx * this.maxDistance / distance;
            dy = dy * this.maxDistance / distance;
        }

        // Update visual position
        this.stickX = this.centerX + dx;
        this.stickY = this.centerY + dy;

        // Update normalized position (-1 to 1)
        this.xPos = dx / this.maxDistance;
        this.yPos = dy / this.maxDistance;
    }

    /**
     * Reset the joystick to center position
     */
    public resetPosition(): void {
        this.stickX = this.centerX;
        this.stickY = this.centerY;
        this.xPos = 0.0;
        this.yPos = 0.0;
    }

    /**
     * Draw the joystick on the canvas
     */
    public draw(): void {
        // Draw outer circle
        this.ctx.fillStyle = '#c8c8c8';
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, this.radius, 0, Math.PI * 2);
        this.ctx.fill();

        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 3;
        this.ctx.stroke();

        // Draw inner stick
        const stickRadius = 12;
        this.ctx.fillStyle = '#6496ff';
        this.ctx.beginPath();
        this.ctx.arc(Math.floor(this.stickX), Math.floor(this.stickY), stickRadius, 0, Math.PI * 2);
        this.ctx.fill();

        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        // Draw label
        this.ctx.fillStyle = '#000';
        this.ctx.font = '16px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(this.label, this.centerX, this.centerY + this.radius + 20);
    }

    /**
     * Set the joystick's dragging state
     * @param dragging - Whether the joystick is being dragged
     */
    public setDragging(dragging: boolean): void {
        this.dragging = dragging;
    }

    /**
     * Set the joystick position from normalized values
     * @param x - Normalized X position (-1 to 1)
     * @param y - Normalized Y position (-1 to 1)
     */
    public setNormalizedPosition(x: number, y: number): void {
        // Clamp values to [-1, 1] range
        this.xPos = Math.max(-1, Math.min(1, x));
        this.yPos = Math.max(-1, Math.min(1, y));

        // Update visual position
        this.stickX = this.centerX + (this.xPos * this.maxDistance);
        this.stickY = this.centerY + (this.yPos * this.maxDistance);
    }

    /**
     * Get the joystick's current state
     * @returns Object containing the joystick's state information
     */
    public getState(): { 
        xPos: number; 
        yPos: number; 
        dragging: boolean; 
        stickId: number;
        visualPosition: { x: number; y: number };
    } {
        return {
            xPos: this.xPos,
            yPos: this.yPos,
            dragging: this.dragging,
            stickId: this.stickId,
            visualPosition: { x: this.stickX, y: this.stickY }
        };
    }

    /**
     * Get rounded normalized position values (for sending to server)
     * @param precision - Number of decimal places (default: 3)
     * @returns Object with rounded x and y positions
     */
    public getRoundedPosition(precision: number = 3): { x: number; y: number } {
        const multiplier = Math.pow(10, precision);
        return {
            x: Math.round(this.xPos * multiplier) / multiplier,
            y: Math.round(this.yPos * multiplier) / multiplier
        };
    }
}