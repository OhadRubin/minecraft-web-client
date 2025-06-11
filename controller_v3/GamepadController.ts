import { 
  GamepadControllerState,
  MousePosition,
  ButtonMapping,
  IGamepadButton,
  IGamepadJoystick,
  GamepadCanvasElement,
  GamepadCanvasContext,
  StatusElement,
  TriggerControlElement
} from './types.js';
import { WebSocketManager } from './WebSocketManager.js';

/**
 * GamepadButton class for UI button representation
 */
class GamepadButton implements IGamepadButton {
  public x: number;
  public y: number;
  public radius: number;
  public buttonId: number;
  public label: string;
  public pressed: boolean = false;
  public hover: boolean = false;

  constructor(x: number, y: number, radius: number, buttonId: number, label: string = "") {
    this.x = x;
    this.y = y;
    this.radius = radius;
    this.buttonId = buttonId;
    this.label = label || buttonId.toString();
  }

  public containsPoint(x: number, y: number): boolean {
    const distance = Math.sqrt((x - this.x) ** 2 + (y - this.y) ** 2);
    return distance <= this.radius;
  }

  public draw(ctx: GamepadCanvasContext): void {
    // Button color based on state
    let color = '#808080';
    if (this.pressed) {
      color = '#ff6464';
    } else if (this.hover) {
      color = '#c8c8c8';
    }

    // Draw button circle
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw label
    ctx.fillStyle = '#000';
    ctx.font = '20px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(this.label, this.x, this.y);
  }
}

/**
 * GamepadJoystick class for UI joystick representation
 */
class GamepadJoystick implements IGamepadJoystick {
  public centerX: number;
  public centerY: number;
  public radius: number;
  public stickId: number;
  public label: string;
  public xPos: number = 0.0; // Normalized position (-1 to 1)
  public yPos: number = 0.0; // Normalized position (-1 to 1)
  public stickX: number; // Visual position
  public stickY: number; // Visual position
  public dragging: boolean = false;
  public maxDistance: number;

  constructor(centerX: number, centerY: number, radius: number, stickId: number, label: string = "") {
    this.centerX = centerX;
    this.centerY = centerY;
    this.radius = radius;
    this.stickId = stickId;
    this.label = label || `Stick ${stickId}`;
    this.stickX = centerX;
    this.stickY = centerY;
    this.maxDistance = radius - 15;
  }

  public containsPoint(x: number, y: number): boolean {
    const distance = Math.sqrt((x - this.centerX) ** 2 + (y - this.centerY) ** 2);
    return distance <= this.radius;
  }

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

  public resetPosition(): void {
    this.stickX = this.centerX;
    this.stickY = this.centerY;
    this.xPos = 0.0;
    this.yPos = 0.0;
  }

  public draw(ctx: GamepadCanvasContext): void {
    // Draw outer circle
    ctx.fillStyle = '#c8c8c8';
    ctx.beginPath();
    ctx.arc(this.centerX, this.centerY, this.radius, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#000';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw inner stick
    const stickRadius = 12;
    ctx.fillStyle = '#6496ff';
    ctx.beginPath();
    ctx.arc(Math.floor(this.stickX), Math.floor(this.stickY), stickRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw label
    ctx.fillStyle = '#000';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(this.label, this.centerX, this.centerY + this.radius + 20);
  }
}

/**
 * Main GamepadController class that coordinates all functionality
 */
export class GamepadController {
  private canvas: GamepadCanvasElement;
  private ctx: GamepadCanvasContext;
  private wsManager: WebSocketManager;
  private state: GamepadControllerState;
  
  // Track buttons currently pressed via visual interface (to prevent gamepad override)
  private visuallyPressedButtons: Set<number> = new Set();
  
  // Track button press start times for duration calculation
  private buttonPressStartTimes: Map<number, number> = new Map();
  
  // Button mapping (Xbox controller standard)
  private readonly buttonMapping: ButtonMapping = {
    0: 0, // A button
    1: 1, // B button
    2: 2, // X button
    3: 3, // Y button
    4: 4, // Left shoulder (L1)
    5: 5, // Right shoulder (R1)
    6: 6, // Left trigger (L2)
    7: 7, // Right trigger (R2)
    8: 8, // Back/Select
    9: 9, // Start
    10: 10, // Left stick click
    11: 11, // Right stick click
    12: 15, // D-pad up
    13: 13, // D-pad down
    14: 14, // D-pad left
    15: 12 // D-pad right
  };

  private animationFrameId: number | null = null;

  constructor(canvasId: string = 'canvas', websocketUrl: string = "ws://localhost:8081") {
    // Initialize canvas
    const canvasElement = document.getElementById(canvasId) as GamepadCanvasElement;
    if (!canvasElement) {
      throw new Error(`Canvas element with id '${canvasId}' not found`);
    }
    this.canvas = canvasElement;
    
    const context = this.canvas.getContext('2d') as GamepadCanvasContext;
    if (!context) {
      throw new Error('Failed to get 2D context from canvas');
    }
    this.ctx = context;

    // Initialize WebSocket manager
    this.wsManager = new WebSocketManager({
      url: websocketUrl,
      onStatusChange: (status) => {
        this.state.connected = status.connected;
        this.updateStatus();
      }
    });
    
    // Initialize state
    this.state = {
      websocket: null,
      connected: false,
      physicalGamepads: [],
      buttons: [],
      joysticks: [],
      draggingJoystick: null,
      buttonIntervals: new Map<number, boolean>(),
      settings: {
        deadzone: 0.15,
        triggerDuration: 50,
        triggerInterval: 16
      }
    };

    this.initialize();
  }

  /**
   * Initialize the controller
   */
  private async initialize(): Promise<void> {
    this.setupGamepadLayout();
    this.setupEventHandlers();
    this.setupTriggerControls();
    
    // Connect to WebSocket
    await this.wsManager.connect();
    
    // Start animation loop
    this.startAnimationLoop();
  }


  /**
   * Setup gamepad button and joystick layout
   */
  private setupGamepadLayout(): void {
    // Face buttons (right side) - A, B, X, Y
    const faceCenterX = 650, faceCenterY = 250;
    const faceSpacing = 35;

    this.state.buttons.push(new GamepadButton(faceCenterX, faceCenterY + faceSpacing, 20, 0, "A"));
    this.state.buttons.push(new GamepadButton(faceCenterX + faceSpacing, faceCenterY, 20, 1, "B"));
    this.state.buttons.push(new GamepadButton(faceCenterX - faceSpacing, faceCenterY, 20, 2, "X"));
    this.state.buttons.push(new GamepadButton(faceCenterX, faceCenterY - faceSpacing, 20, 3, "Y"));

    // D-Pad (left side)
    const dpadCenterX = 150, dpadCenterY = 250;
    const dpadSpacing = 30;

    this.state.buttons.push(new GamepadButton(dpadCenterX - dpadSpacing, dpadCenterY, 15, 14, "←"));
    this.state.buttons.push(new GamepadButton(dpadCenterX + dpadSpacing, dpadCenterY, 15, 12, "→"));
    this.state.buttons.push(new GamepadButton(dpadCenterX, dpadCenterY - dpadSpacing, 15, 15, "↑"));
    this.state.buttons.push(new GamepadButton(dpadCenterX, dpadCenterY + dpadSpacing, 15, 13, "↓"));

    // Shoulder buttons (top)
    this.state.buttons.push(new GamepadButton(200, 80, 25, 4, "L1"));
    this.state.buttons.push(new GamepadButton(280, 60, 20, 6, "L2"));
    this.state.buttons.push(new GamepadButton(600, 80, 25, 5, "R1"));
    this.state.buttons.push(new GamepadButton(520, 60, 20, 7, "R2"));

    // Center buttons
    this.state.buttons.push(new GamepadButton(350, 200, 18, 8, "SELECT"));
    this.state.buttons.push(new GamepadButton(450, 200, 18, 9, "START"));
    this.state.buttons.push(new GamepadButton(400, 150, 15, 16, "HOME"));

    // Joysticks
    this.state.joysticks.push(new GamepadJoystick(250, 400, 45, 0, "Left"));
    this.state.joysticks.push(new GamepadJoystick(550, 400, 45, 1, "Right"));
  }

  /**
   * Setup mouse and touch event handlers
   */
  private setupEventHandlers(): void {
    // Mouse events
    this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
    this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
    this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));

    // Gamepad events
    window.addEventListener('gamepadconnected', this.handleGamepadConnected.bind(this));
    window.addEventListener('gamepaddisconnected', this.handleGamepadDisconnected.bind(this));

    // Cleanup on page unload
    window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
  }

  /**
   * Setup trigger control input listeners
   */
  private setupTriggerControls(): void {
    const durationInput = document.getElementById('trigger-duration') as HTMLInputElement | null;
    const intervalInput = document.getElementById('trigger-interval') as HTMLInputElement | null;

    if (durationInput) {
      durationInput.addEventListener('input', (e) => {
        const target = e.target as TriggerControlElement;
        const value = parseInt(target.value);
        if (value >= 1 && value <= 1000) {
          this.state.settings.triggerDuration = value;
          console.log(`🎯 Trigger duration updated to: ${value}ms`);
        }
      });
    }

    if (intervalInput) {
      intervalInput.addEventListener('input', (e) => {
        const target = e.target as TriggerControlElement;
        const value = parseInt(target.value);
        if (value >= 1 && value <= 1000) {
          this.state.settings.triggerInterval = value;
          console.log(`⏱️ Trigger interval updated to: ${value}ms`);
        }
      });
    }
  }

  /**
   * Get mouse position relative to canvas
   */
  private getMousePos(e: MouseEvent): MousePosition {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) * (this.canvas.width / rect.width),
      y: (e.clientY - rect.top) * (this.canvas.height / rect.height)
    };
  }

  /**
   * Handle mouse down events
   */
  private async handleMouseDown(e: MouseEvent): Promise<void> {
    const pos = this.getMousePos(e);

    // Check button clicks
    for (const button of this.state.buttons) {
      if (button.containsPoint(pos.x, pos.y)) {
        button.pressed = true;
        this.visuallyPressedButtons.add(button.buttonId);

        // Record press start time
        this.buttonPressStartTimes.set(button.buttonId, Date.now());

        // Start continuous pressing for triggers (buttons 6 and 7)
        if (button.buttonId === 6 || button.buttonId === 7) {
          this.startButtonPress(button.buttonId);
        } else {
          // Single press for other buttons
          await this.wsManager.sendCommand({
            type: "gamepadButtonPressDown",
            buttonIndex: button.buttonId
          });

          // Auto-release after short duration
          setTimeout(async () => {
            await this.wsManager.sendCommand({
              type: "gamepadButtonPressUp",
              buttonIndex: button.buttonId
            });
            button.pressed = false;
            this.visuallyPressedButtons.delete(button.buttonId);
            this.logButtonDuration(button.buttonId);
          }, 100);
        }
      }
    }

    // Check joystick clicks
    for (const joystick of this.state.joysticks) {
      if (joystick.containsPoint(pos.x, pos.y)) {
        joystick.dragging = true;
        this.state.draggingJoystick = joystick;
        joystick.updatePosition(pos.x, pos.y);
        await this.wsManager.sendCommand({
          type: "gamepadJoystickMove",
          stickIndex: joystick.stickId,
          x: Math.round(joystick.xPos * 1000) / 1000,
          y: Math.round(joystick.yPos * 1000) / 1000
        });
      }
    }
  }

  /**
   * Handle mouse move events
   */
  private async handleMouseMove(e: MouseEvent): Promise<void> {
    const pos = this.getMousePos(e);

    // Update button hover states
    for (const button of this.state.buttons) {
      button.hover = button.containsPoint(pos.x, pos.y);
    }

    // Handle joystick dragging
    if (this.state.draggingJoystick && this.state.draggingJoystick.dragging) {
      this.state.draggingJoystick.updatePosition(pos.x, pos.y);
      await this.wsManager.sendCommand({
        type: "gamepadJoystickMove",
        stickIndex: this.state.draggingJoystick.stickId,
        x: Math.round(this.state.draggingJoystick.xPos * 1000) / 1000,
        y: Math.round(this.state.draggingJoystick.yPos * 1000) / 1000
      });
    }
  }

  /**
   * Handle mouse up events
   */
  private async handleMouseUp(): Promise<void> {
    // Release all buttons and stop continuous pressing
    for (const button of this.state.buttons) {
      if (this.visuallyPressedButtons.has(button.buttonId)) {
        button.pressed = false;
        this.visuallyPressedButtons.delete(button.buttonId);

        // Stop continuous pressing for triggers
        if (button.buttonId === 6 || button.buttonId === 7) {
          this.stopButtonPress(button.buttonId);
        }
        
        // Log button duration
        this.logButtonDuration(button.buttonId);
      }
    }

    // Stop dragging joysticks and center them
    if (this.state.draggingJoystick) {
      this.state.draggingJoystick.dragging = false;
      this.state.draggingJoystick.resetPosition();
      
      await this.wsManager.sendCommand({
        type: "gamepadJoystickMove",
        stickIndex: this.state.draggingJoystick.stickId,
        x: 0,
        y: 0
      });
      
      await this.wsManager.sendCommand({
        type: "gamepadJoystickCenter",
        stickIndex: this.state.draggingJoystick.stickId
      });
      
      this.state.draggingJoystick = null;
    }
  }

  /**
   * Start continuous button pressing
   */
  private async startButtonPress(buttonId: number): Promise<void> {
    if (this.state.buttonIntervals.has(buttonId)) {
      return; // Already pressing
    }

    // Send single press down - the backend will handle continuous behavior
    await this.wsManager.sendCommand({
      type: "gamepadButtonPressDown",
      buttonIndex: buttonId
    });

    // Mark as active
    this.state.buttonIntervals.set(buttonId, true);
    console.log(`🔥 Started continuous press for button ${buttonId}`);
  }

  /**
   * Stop continuous button pressing
   */
  private async stopButtonPress(buttonId: number): Promise<void> {
    if (this.state.buttonIntervals.has(buttonId)) {
      this.state.buttonIntervals.delete(buttonId);
      
      // Send button up to stop the continuous press
      await this.wsManager.sendCommand({
        type: "gamepadButtonPressUp",
        buttonIndex: buttonId
      });
      
      console.log(`⏹️ Stopped continuous press for button ${buttonId}`);
    }
  }

  /**
   * Log button press duration to terminal
   */
  private logButtonDuration(buttonId: number): void {
    const startTime = this.buttonPressStartTimes.get(buttonId);
    if (startTime) {
      const duration = Date.now() - startTime;
      const buttonName = this.getButtonName(buttonId);
      const timestamp = new Date().toLocaleTimeString();
      
      // Log to terminal
      const terminal = (window as any).gamepadTerminal;
      if (terminal) {
        terminal.writeln(`[${timestamp}] 🎮 Button ${buttonName} pressed for ${duration}ms`);
      }
      
      // Clean up
      this.buttonPressStartTimes.delete(buttonId);
    }
  }

  /**
   * Get button name from button ID
   */
  private getButtonName(buttonId: number): string {
    const buttonNames: { [key: number]: string } = {
      0: "A", 1: "B", 2: "X", 3: "Y",
      4: "L1", 5: "R1", 6: "L2", 7: "R2",
      8: "SELECT", 9: "START", 10: "L3", 11: "R3",
      12: "D-RIGHT", 13: "D-DOWN", 14: "D-LEFT", 15: "D-UP",
      16: "HOME"
    };
    return buttonNames[buttonId] || `${buttonId}`;
  }

  /**
   * Handle gamepad connected events
   */
  private handleGamepadConnected(e: GamepadEvent): void {
    console.log(`🎮 Gamepad connected: ${e.gamepad.id}`);
    this.pollGamepads();
  }

  /**
   * Handle gamepad disconnected events
   */
  private handleGamepadDisconnected(e: GamepadEvent): void {
    console.log(`🎮 Gamepad disconnected: ${e.gamepad.id}`);
    this.pollGamepads();
  }

  /**
   * Poll for connected gamepads
   */
  private pollGamepads(): void {
    const gamepads = navigator.getGamepads();
    this.state.physicalGamepads = [];

    for (let i = 0; i < gamepads.length; i++) {
      const gamepad = gamepads[i];
      if (gamepad !== null) {
        this.state.physicalGamepads.push(gamepad);
      }
    }

    this.updateStatus();
  }

  /**
   * Apply deadzone to analog values
   */
  private applyDeadzone(value: number): number {
    return Math.abs(value) < this.state.settings.deadzone ? 0.0 : value;
  }

  /**
   * Update physical gamepad input
   */
  private async updatePhysicalGamepads(): Promise<void> {
    const gamepads = navigator.getGamepads();

    for (let i = 0; i < gamepads.length; i++) {
      const gamepad = gamepads[i];
      if (!gamepad) continue;

      // Check buttons
      for (let j = 0; j < gamepad.buttons.length; j++) {
        const buttonId = this.buttonMapping[j];
        if (buttonId !== undefined) {

          const button = this.state.buttons.find(b => b.buttonId === buttonId);
          if (button) {
            const wasPressed = button.pressed;
            
            // Only update from physical gamepad if not visually pressed
            if (!this.visuallyPressedButtons.has(buttonId)) {
              button.pressed = gamepad.buttons[j].pressed;
            }

            // Send command on button state change (only for physical gamepad state)
            const physicalPressed = gamepad.buttons[j].pressed;
            if (!wasPressed && physicalPressed && !this.visuallyPressedButtons.has(buttonId)) {
              // Button pressed down (physical only, not visual override)
              this.buttonPressStartTimes.set(buttonId, Date.now());
              await this.wsManager.sendCommand({
                type: "gamepadButtonPressDown",
                buttonIndex: buttonId
              });
            } else if (wasPressed && !physicalPressed && !this.visuallyPressedButtons.has(buttonId)) {
              // Button released (physical only, not visual override)
              await this.wsManager.sendCommand({
                type: "gamepadButtonPressUp",
                buttonIndex: buttonId
              });
              this.logButtonDuration(buttonId);
            }
          }
        }
      }

      // Check analog sticks
      if (gamepad.axes.length >= 4) {
        // Left stick (axes 0, 1)
        const leftX = this.applyDeadzone(gamepad.axes[0]);
        const leftY = this.applyDeadzone(gamepad.axes[1]);

        if (this.state.joysticks[0]) {
          const joystick = this.state.joysticks[0];
          const prevX = joystick.xPos;
          const prevY = joystick.yPos;

          joystick.xPos = leftX;
          joystick.yPos = leftY;
          joystick.stickX = joystick.centerX + (leftX * joystick.maxDistance);
          joystick.stickY = joystick.centerY + (leftY * joystick.maxDistance);

          if (Math.abs(prevX - leftX) > 0.01 || Math.abs(prevY - leftY) > 0.01) {
            await this.wsManager.sendCommand({
              type: "gamepadJoystickMove",
              stickIndex: 0,
              x: Math.round(leftX * 1000) / 1000,
              y: Math.round(leftY * 1000) / 1000
            });
          }
        }

        // Right stick (axes 2, 3)
        const rightX = this.applyDeadzone(gamepad.axes[2]);
        const rightY = this.applyDeadzone(gamepad.axes[3]);

        if (this.state.joysticks[1]) {
          const joystick = this.state.joysticks[1];
          const prevX = joystick.xPos;
          const prevY = joystick.yPos;

          joystick.xPos = rightX;
          joystick.yPos = rightY;
          joystick.stickX = joystick.centerX + (rightX * joystick.maxDistance);
          joystick.stickY = joystick.centerY + (rightY * joystick.maxDistance);

          if (Math.abs(prevX - rightX) > 0.01 || Math.abs(prevY - rightY) > 0.01) {
            await this.wsManager.sendCommand({
              type: "gamepadJoystickMove",
              stickIndex: 1,
              x: Math.round(rightX * 1000) / 1000,
              y: Math.round(rightY * 1000) / 1000
            });
          }
        }
      }
    }
  }

  /**
   * Update status display
   */
  private updateStatus(): void {
    const wsStatus = document.getElementById('websocket-status') as StatusElement;
    const gamepadStatus = document.getElementById('gamepad-status') as StatusElement;

    if (wsStatus) {
      if (this.state.connected) {
        wsStatus.textContent = 'WebSocket: Connected';
        wsStatus.className = 'connected';
      } else {
        wsStatus.textContent = 'WebSocket: Disconnected';
        wsStatus.className = 'disconnected';
      }
    }

    if (gamepadStatus) {
      gamepadStatus.textContent = `Physical Gamepads: ${this.state.physicalGamepads.length}`;
      if (this.state.physicalGamepads.length > 0) {
        gamepadStatus.className = 'gamepad-detected';
      } else {
        gamepadStatus.className = '';
      }
    }
  }

  /**
   * Draw the gamepad interface
   */
  private draw(): void {
    // Clear canvas
    this.ctx.fillStyle = '#ffffff';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Draw title
    this.ctx.fillStyle = '#000';
    this.ctx.font = 'bold 28px Arial';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText('Gamepad Controller', 400, 30);

    // Draw gamepad body outline
    this.ctx.fillStyle = '#c8c8c8';
    this.ctx.beginPath();
    this.ctx.roundRect(120, 120, 560, 400, 30);
    this.ctx.fill();

    this.ctx.strokeStyle = '#000';
    this.ctx.lineWidth = 3;
    this.ctx.stroke();

    // Draw all buttons
    for (const button of this.state.buttons) {
      button.draw(this.ctx);
    }

    // Draw all joysticks
    for (const joystick of this.state.joysticks) {
      joystick.draw(this.ctx);
    }

    // Draw instructions
    this.ctx.fillStyle = '#404040';
    this.ctx.font = '16px Arial';
    this.ctx.textAlign = 'left';
    this.ctx.fillText('Click buttons or use physical gamepad', 10, 550);
    this.ctx.fillText('Drag joysticks or use analog sticks', 10, 570);
    this.ctx.fillText('Connect a gamepad and press any button to use it', 10, 590);
  }

  /**
   * Animation loop
   */
  private async animate(): Promise<void> {
    this.pollGamepads();
    await this.updatePhysicalGamepads();
    this.draw();
    
    this.animationFrameId = requestAnimationFrame(() => this.animate());
  }

  /**
   * Start the animation loop
   */
  private startAnimationLoop(): void {
    this.animate();
  }

  /**
   * Stop the animation loop
   */
  private stopAnimationLoop(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  /**
   * Handle page unload cleanup
   */
  private async handleBeforeUnload(): Promise<void> {
    // Clear all button intervals
    this.state.buttonIntervals.clear();
    
    // Clear visual button state
    this.visuallyPressedButtons.clear();
    
    // Clear button press timers
    this.buttonPressStartTimes.clear();
    
    // Disconnect WebSocket
    this.wsManager.disconnect();
  }

  /**
   * Destroy the controller and cleanup resources
   */
  public async destroy(): Promise<void> {
    this.stopAnimationLoop();
    this.wsManager.disconnect();
    this.wsManager.destroy();
    
    // Clear visual button state
    this.visuallyPressedButtons.clear();
    
    // Clear button press timers
    this.buttonPressStartTimes.clear();
    
    // Remove event listeners
    this.canvas.removeEventListener('mousedown', this.handleMouseDown.bind(this));
    this.canvas.removeEventListener('mousemove', this.handleMouseMove.bind(this));
    this.canvas.removeEventListener('mouseup', this.handleMouseUp.bind(this));
    window.removeEventListener('gamepadconnected', this.handleGamepadConnected.bind(this));
    window.removeEventListener('gamepaddisconnected', this.handleGamepadDisconnected.bind(this));
    window.removeEventListener('beforeunload', this.handleBeforeUnload.bind(this));
  }
}