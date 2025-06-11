/**
 * GamepadButton class for rendering and handling button interactions
 * in the gamepad controller interface
 */

import { IGamepadButton, GamepadCanvasContext } from './types.js';

export class GamepadButton implements IGamepadButton {
    public x: number;
    public y: number;
    public radius: number;
    public buttonId: number;
    public label: string;
    public pressed: boolean;
    public hover: boolean;

    private ctx: GamepadCanvasContext;

    constructor(
        x: number, 
        y: number, 
        radius: number, 
        buttonId: number, 
        label: string = "",
        ctx: GamepadCanvasContext
    ) {
        this.x = x;
        this.y = y;
        this.radius = radius;
        this.buttonId = buttonId;
        this.label = label || buttonId.toString();
        this.pressed = false;
        this.hover = false;
        this.ctx = ctx;
    }

    /**
     * Check if a point is within the button's bounds
     * @param x - X coordinate to check
     * @param y - Y coordinate to check
     * @returns True if the point is within the button
     */
    public containsPoint(x: number, y: number): boolean {
        const distance = Math.sqrt((x - this.x) ** 2 + (y - this.y) ** 2);
        return distance <= this.radius;
    }

    /**
     * Draw the button on the canvas
     */
    public draw(): void {
        // Button color based on state
        let color = '#808080';
        if (this.pressed) {
            color = '#ff6464';
        } else if (this.hover) {
            color = '#c8c8c8';
        }

        // Draw button circle
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        this.ctx.fill();

        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        // Draw label
        this.ctx.fillStyle = '#000';
        this.ctx.font = '20px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(this.label, this.x, this.y);
    }

    /**
     * Set the button's pressed state
     * @param pressed - Whether the button is pressed
     */
    public setPressed(pressed: boolean): void {
        this.pressed = pressed;
    }

    /**
     * Set the button's hover state
     * @param hover - Whether the button is being hovered
     */
    public setHover(hover: boolean): void {
        this.hover = hover;
    }

    /**
     * Get the button's current state
     * @returns Object containing the button's state information
     */
    public getState(): { pressed: boolean; hover: boolean; buttonId: number } {
        return {
            pressed: this.pressed,
            hover: this.hover,
            buttonId: this.buttonId
        };
    }
}