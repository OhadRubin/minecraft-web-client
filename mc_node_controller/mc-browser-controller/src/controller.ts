// src/controller.ts

import { WINDOW_WIDTH, WINDOW_HEIGHT, BLACK, WHITE, RED, BLUE, GREEN, ORANGE, PURPLE, GRAY, YELLOW, DARK_GRAY, BROWN, TEAL } from './constants';
import { Button, ToggleButton, VirtualJoystick, KeyboardMovement, TouchArea, LookPathVisualizationArea } from './ui';
import { LookPathTracker } from './look-path-tracker';
import { MinecraftControllerInterface } from './interface';
import { Point } from './types';

/**
 * Port of mc_pygame_controller/controller_base.py
 * The main controller class that manages the UI, state, and main loop.
 */
export class MinecraftController {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private running = true;
    private mode: 'mcp' = 'mcp'; // Only MCP mode is ported for the browser
    private sensitivity: number;
    
    // UI Elements
    private movementJoystick: VirtualJoystick;
    private keyboardMovement: KeyboardMovement;
    private cameraArea: TouchArea;
    private lookPathTracker: LookPathTracker;
    private lookVisualization: LookPathVisualizationArea;
    private buttons: (Button | ToggleButton)[] = [];
    private hotbarButtons: Button[] = [];
    
    // State
    private lastMovement: Point = { x: 0, y: 0 };
    private currentHotbarSlot = 0;
    private lastHotbarSlot = -1;

    // MCP Integration
    private mcpExecutor: MinecraftControllerInterface | null = null;

    constructor(canvas: HTMLCanvasElement, sensitivity: number = 5.0) {
        this.canvas = canvas;
        this.canvas.width = WINDOW_WIDTH;
        this.canvas.height = WINDOW_HEIGHT;
        this.ctx = canvas.getContext('2d')!;
        this.sensitivity = sensitivity;

        // Init UI
        this.lookPathTracker = new LookPathTracker(2000, this.sensitivity);
        this.lookVisualization = new LookPathVisualizationArea({x: 1230, y: 50, width: 350, height: 300});
        
        this.movementJoystick = new VirtualJoystick({ x: 150, y: WINDOW_HEIGHT - 200 }, 100);
        this.keyboardMovement = new KeyboardMovement();
        this.cameraArea = new TouchArea({ x: 400, y: 50, width: 800, height: 500 });
        
        this.setupButtons();
        this.setupHotbar();
        
        this.attachEventListeners();
    }
    
    public setMcpExecutor(executor: MinecraftControllerInterface) {
        this.mcpExecutor = executor;
        this.lookPathTracker.set_execution_callback((cmd) => this.mcpExecutor?.captureCommand(cmd));
    }

    private setupButtons() {
        const btnW = 100, btnH = 40, startX = 1300, startY = 600, spacing = 50;
        
        const createAndAdd = (rect: any, text: string, color: any, isToggle: boolean, onAction: any) => {
            const btn = isToggle
                ? new ToggleButton(rect, text, color, WHITE, onAction)
                : new Button(rect, text, color, WHITE, onAction);
            this.buttons.push(btn);
            return btn;
        };

        createAndAdd({x: startX, y: startY, width: btnW, height: btnH}, "Left Click", RED, false, () => this.handleAction('leftClick'));
        createAndAdd({x: startX + 110, y: startY, width: btnW, height: btnH}, "Right Click", BLUE, false, () => this.handleAction('rightClick'));
        createAndAdd({x: startX, y: startY + spacing, width: btnW, height: btnH}, "Jump", GREEN, false, () => this.handleAction('jump'));
        createAndAdd({x: startX, y: startY + spacing * 2, width: btnW, height: btnH}, "Inventory", GRAY, false, () => this.handleAction('openInventory'));
        createAndAdd({x: startX + 110, y: startY + spacing, width: btnW, height: btnH}, "Sneak", ORANGE, true, (state) => this.handleAction('sneak', { state }));
        createAndAdd({x: startX + 110, y: startY + spacing * 2, width: btnW, height: btnH}, "Sprint", PURPLE, true, (state) => this.handleAction('sprint', { state }));
        createAndAdd({x: startX, y: startY + spacing * 3, width: btnW, height: btnH}, "Drop Item", YELLOW, false, () => this.handleAction('dropItem'));
        createAndAdd({x: startX + 110, y: startY + spacing * 3, width: btnW, height: btnH}, "Swap Hands", PINK, false, () => this.handleAction('swapHands'));
        createAndAdd({x: startX, y: startY + spacing * 4, width: btnW * 2 + 10, height: btnH}, "Clear Look Path", BROWN, false, () => this.lookPathTracker.clear_history());
        createAndAdd({x: startX, y: startY + spacing * 5, width: btnW * 2 + 10, height: btnH}, "Save Demo Step", TEAL, false, () => this.mcpExecutor?.saveDemonstrationStep("User clicked save step"));
    }
    
    private setupHotbar() {
        const btnW = 50, btnH = 40, startX = 50, hotbarY = WINDOW_HEIGHT - 60, spacing = 55;
        for (let i = 0; i < 9; i++) {
            const slot = i;
            const btn = new Button(
                { x: startX + i * spacing, y: hotbarY, width: btnW, height: btnH },
                String(i + 1), DARK_GRAY, WHITE,
                () => this.handleHotbar(slot)
            );
            this.hotbarButtons.push(btn);
        }
    }

    private handleHotbar(slot: number) {
        if (slot !== this.lastHotbarSlot) {
            this.handleAction('setHotbarSlot', { slot });
            this.currentHotbarSlot = slot;
            this.lastHotbarSlot = slot;
        }
    }

    private handleAction(tool: string, parameters: any = {}) {
        const command = { tool, parameters };
        
        // Clicks need special handling if we want hold support, but for demo capture, single actions are fine.
        if (tool === 'leftClick' || tool === 'rightClick' || tool === 'jump') {
            command.parameters.duration = 'short';
        }
        
        this.mcpExecutor?.captureCommand(command);
    }

    private attachEventListeners() {
        const getPos = (e: MouseEvent | TouchEvent): Point => {
            const rect = this.canvas.getBoundingClientRect();
            if (e instanceof MouseEvent) {
                return { x: e.clientX - rect.left, y: e.clientY - rect.top };
            }
            const touch = e.touches[0] || e.changedTouches[0];
            return { x: touch.clientX - rect.left, y: touch.clientY - rect.top };
        };

        const onDown = (e: MouseEvent | TouchEvent) => {
            e.preventDefault();
            const pos = getPos(e);
            const type = 'mousedown';
            this.movementJoystick.handleEvent(type, pos);
            this.cameraArea.handleEvent(type, pos);
            if (this.cameraArea.isTouching) { this.lookPathTracker.start_mouse_tracking(); }
            this.buttons.forEach(b => b.handleEvent(type, pos));
            this.hotbarButtons.forEach(b => b.handleEvent(type, pos));
        };

        const onUp = (e: MouseEvent | TouchEvent) => {
            e.preventDefault();
            const pos = getPos(e);
            const type = 'mouseup';
            this.movementJoystick.handleEvent(type, pos);
            if (this.cameraArea.isTouching) { this.lookPathTracker.stop_mouse_tracking(); }
            this.cameraArea.handleEvent(type, pos);
            this.buttons.forEach(b => b.handleEvent(type, pos));
            this.hotbarButtons.forEach(b => b.handleEvent(type, pos));
        };

        const onMove = (e: MouseEvent | TouchEvent) => {
            e.preventDefault();
            const pos = getPos(e);
            const type = 'mousemove';
            this.movementJoystick.handleEvent(type, pos);
            const lookDelta = this.cameraArea.handleEvent(type, pos);
            this.lookPathTracker.add_movement(lookDelta.x, lookDelta.y);
        };

        this.canvas.addEventListener('mousedown', onDown);
        this.canvas.addEventListener('mouseup', onUp);
        this.canvas.addEventListener('mousemove', onMove);
        this.canvas.addEventListener('touchstart', onDown);
        this.canvas.addEventListener('touchend', onUp);
        this.canvas.addEventListener('touchmove', onMove);
        
        // Keyboard hotkeys
        window.addEventListener('keydown', (e) => {
            if (e.key >= '1' && e.key <= '9') {
                this.handleHotbar(parseInt(e.key) - 1);
            }
            if (e.key.toLowerCase() === 'q') this.handleAction('dropItem');
            if (e.key.toLowerCase() === 'f') this.handleAction('swapHands');
            if (e.key.toLowerCase() === 'e') this.handleAction('openInventory');
            if (e.key === ' ') this.handleAction('jump');
        });
    }
    
    private handleMovement() {
        const joyMove = this.movementJoystick.handleEvent('mousemove', this.movementJoystick.knobPos);
        const keyMove = this.keyboardMovement.getMovement();
        
        let move = {x: 0, y: 0};
        if (Math.hypot(joyMove.x, joyMove.y) > 0.1) {
            move = joyMove;
        } else if (Math.hypot(keyMove.x, keyMove.y) > 0.1) {
            move = keyMove;
        }

        if (Math.hypot(move.x, move.y) > 0.1) {
            if (JSON.stringify(move) !== JSON.stringify(this.lastMovement)) {
                 // For human demos, we convert continuous movement into discrete 'walk' commands.
                 // This is a simplification. A better system might have a start/stopWalk action.
                 // Here, we'll just send a short walk command.
                 this.handleAction('walk', { duration: 100, direction: { x: move.x, z: move.y }});
                 this.lastMovement = move;
            }
        } else {
            this.lastMovement = {x: 0, y: 0};
        }
    }

    private draw() {
        this.ctx.fillStyle = BLACK;
        this.ctx.fillRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT);
        
        // Draw all UI elements
        this.movementJoystick.draw(this.ctx);
        this.cameraArea.draw(this.ctx);
        this.lookVisualization.draw(this.ctx, this.lookPathTracker);
        this.buttons.forEach(b => b.draw(this.ctx));
        this.hotbarButtons.forEach((b, i) => {
            b.draw(this.ctx);
            if (i === this.currentHotbarSlot) {
                this.ctx.strokeStyle = YELLOW;
                this.ctx.lineWidth = 3;
                this.ctx.strokeRect(b.rect.x-2, b.rect.y-2, b.rect.width+4, b.rect.height+4);
            }
        });
        
        // Draw labels and status
        this.ctx.fillStyle = WHITE;
        this.ctx.font = '24px sans-serif';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`Mode: ${this.mode.toUpperCase()}`, 10, 30);
    }
    
    public start() {
        console.log(`Starting Minecraft Controller in ${this.mode.toUpperCase()} mode...`);
        this.animationLoop();
    }
    
    private animationLoop = () => {
        if (!this.running) return;

        this.handleMovement();
        this.draw();
        
        requestAnimationFrame(this.animationLoop);
    }

    public cleanup() {
        this.running = false;
        // Remove event listeners if necessary
    }
}
