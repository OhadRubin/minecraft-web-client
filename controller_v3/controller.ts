import { GamepadButton } from './GamepadButton.js';
import { GamepadJoystick } from './GamepadJoystick.js';
import { 
    GamepadCanvasContext, 
    GamepadCanvasElement, 
    IGamepadButton, 
    IGamepadJoystick,
    WebSocketCommand,
    WebSocketInitMessage
} from './types';

// Canvas setup - Using non-null assertion after check for legacy code
const canvasElement = document.getElementById('canvas') as GamepadCanvasElement | null;
const ctxElement = canvasElement?.getContext('2d') as GamepadCanvasContext | null;

// Exit early if canvas is not available
if (!canvasElement || !ctxElement) {
    console.error('Canvas element not found');
    throw new Error('Canvas element not found');
}

// After validation, we can safely assert these are non-null
const canvas = canvasElement!;
const ctx = ctxElement!;

// WebSocket connection
let websocket: WebSocket | null = null;
let connected = false;

// Physical gamepad state
let physicalGamepads: Gamepad[] = [];
let gamepadDeadzone = 0.15;

// UI elements
const buttons: IGamepadButton[] = [];
const joysticks: IGamepadJoystick[] = [];
let draggingJoystick: IGamepadJoystick | null = null;

// Track button press intervals for continuous pressing
const buttonIntervals = new Map<number, boolean>();

// Configurable trigger settings
let triggerDuration = 50; // Default duration in ms
let triggerInterval = 16; // Default interval in ms (60fps)

// Button mapping (Xbox controller standard)
const buttonMapping: { [key: number]: number } = {
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



// Setup gamepad layout
function setupGamepadLayout() {
    // Face buttons (right side) - A, B, X, Y
    const faceCenterX = 650,
        faceCenterY = 250;
    const faceSpacing = 35;

    buttons.push(new GamepadButton(faceCenterX, faceCenterY + faceSpacing, 20, 0, "A", ctx));
    buttons.push(new GamepadButton(faceCenterX + faceSpacing, faceCenterY, 20, 1, "B", ctx));
    buttons.push(new GamepadButton(faceCenterX - faceSpacing, faceCenterY, 20, 2, "X", ctx));
    buttons.push(new GamepadButton(faceCenterX, faceCenterY - faceSpacing, 20, 3, "Y", ctx));

    // D-Pad (left side)
    const dpadCenterX = 150,
        dpadCenterY = 250;
    const dpadSpacing = 30;

    buttons.push(new GamepadButton(dpadCenterX - dpadSpacing, dpadCenterY, 15, 14, "←", ctx));
    buttons.push(new GamepadButton(dpadCenterX + dpadSpacing, dpadCenterY, 15, 12, "→", ctx));
    buttons.push(new GamepadButton(dpadCenterX, dpadCenterY - dpadSpacing, 15, 15, "↑", ctx));
    buttons.push(new GamepadButton(dpadCenterX, dpadCenterY + dpadSpacing, 15, 13, "↓", ctx));

    // Shoulder buttons (top)
    buttons.push(new GamepadButton(200, 80, 25, 4, "L1", ctx));
    buttons.push(new GamepadButton(280, 60, 20, 6, "L2", ctx));
    buttons.push(new GamepadButton(600, 80, 25, 5, "R1", ctx));
    buttons.push(new GamepadButton(520, 60, 20, 7, "R2", ctx));

    // Center buttons
    buttons.push(new GamepadButton(350, 200, 18, 8, "SELECT", ctx));
    buttons.push(new GamepadButton(450, 200, 18, 9, "START", ctx));
    buttons.push(new GamepadButton(400, 150, 15, 16, "HOME", ctx));

    // Joysticks
    joysticks.push(new GamepadJoystick(250, 400, 45, 0, "Left", ctx));
    joysticks.push(new GamepadJoystick(550, 400, 45, 1, "Right", ctx));
}

// WebSocket connection
async function connectWebSocket() {
    try {
        console.log("🔌 Connecting to WebSocket...");
        websocket = new WebSocket("ws://localhost:8081");

        websocket.onopen = async() => {
            // Register as MCP client
            const initMsg: WebSocketInitMessage = {
                init: "pygame"
            };
            websocket!.send(JSON.stringify(initMsg));
            console.log("✅ Connected to WebSocket server");

            // Connect the gamepad
            await sendCommand({
                type: "gamepadConnect"
            });

            connected = true;
            updateStatus();
        };

        websocket.onclose = () => {
            console.log("❌ WebSocket disconnected");
            connected = false;
            updateStatus();
        };

        websocket.onerror = (error) => {
            console.error("❌ WebSocket error:", error);
            connected = false;
            updateStatus();
        };

    } catch (error) {
        console.error("❌ Failed to connect:", error);
        connected = false;
        updateStatus();
    }
}

async function sendCommand(command: WebSocketCommand): Promise<void> {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        return;
    }

    try {
        websocket.send(JSON.stringify(command));
        console.log("📤 Sent:", command);
    } catch (error) {
        console.error("❌ Error sending command:", error);
    }
}

// Start continuous button pressing
function startButtonPress(buttonId: number): void {
    if (buttonIntervals.has(buttonId)) {
        return; // Already pressing
    }

    // Send single press down - the backend will handle continuous behavior
    sendCommand({
        type: "gamepadButtonPressDown",
        buttonIndex: buttonId
    });

    // Mark as active (no interval needed, just tracking)
    buttonIntervals.set(buttonId, true);
    console.log(`🔥 Started continuous press for button ${buttonId}`);
}

// Stop continuous button pressing
function stopButtonPress(buttonId: number): void {
    if (buttonIntervals.has(buttonId)) {
        buttonIntervals.delete(buttonId);
        
        // Send button up to stop the continuous press
        sendCommand({
            type: "gamepadButtonPressUp",
            buttonIndex: buttonId
        });
        
        console.log(`⏹️ Stopped continuous press for button ${buttonId}`);
    }
}

// Update status display
function updateStatus(): void {
    const wsStatus = document.getElementById('websocket-status');
    const gamepadStatus = document.getElementById('gamepad-status');

    if (wsStatus) {
        if (connected) {
            wsStatus.textContent = 'WebSocket: Connected';
            wsStatus.className = 'connected';
        } else {
            wsStatus.textContent = 'WebSocket: Disconnected';
            wsStatus.className = 'disconnected';
        }
    }

    if (gamepadStatus) {
        gamepadStatus.textContent = `Physical Gamepads: ${physicalGamepads.length}`;
        if (physicalGamepads.length > 0) {
            gamepadStatus.className = 'gamepad-detected';
        } else {
            gamepadStatus.className = '';
        }
    }
}

// Apply deadzone to analog values
function applyDeadzone(value: number): number {
    return Math.abs(value) < gamepadDeadzone ? 0.0 : value;
}

// Mouse/touch event handlers
function getMousePos(e: MouseEvent): { x: number; y: number } {
    const rect = canvas.getBoundingClientRect();
    return {
        x: (e.clientX - rect.left) * (canvas.width / rect.width),
        y: (e.clientY - rect.top) * (canvas.height / rect.height)
    };
}

canvas.addEventListener('mousedown', async(e) => {
    const pos = getMousePos(e);

    // Check button clicks
    for (const button of buttons) {
        if (button.containsPoint(pos.x, pos.y)) {
            button.pressed = true;

            // Start continuous pressing for triggers (buttons 6 and 7)
            if (button.buttonId === 6 || button.buttonId === 7) {
                startButtonPress(button.buttonId);
            } else {
                // Single press for other buttons - send down then up
                await sendCommand({
                    type: "gamepadButtonPressDown",
                    buttonIndex: button.buttonId
                });

                // Auto-release after short duration
                setTimeout(async () => {
                    await sendCommand({
                        type: "gamepadButtonPressUp",
                        buttonIndex: button.buttonId
                    });
                    button.pressed = false;
                }, 100);
            }
        }
    }

    // Check joystick clicks
    for (const joystick of joysticks) {
        if (joystick.containsPoint(pos.x, pos.y)) {
            joystick.dragging = true;
            draggingJoystick = joystick;
            joystick.updatePosition(pos.x, pos.y);
            await sendCommand({
                type: "gamepadJoystickMove",
                stickIndex: joystick.stickId,
                x: Math.round(joystick.xPos * 1000) / 1000,
                y: Math.round(joystick.yPos * 1000) / 1000
            });
        }
    }
});

canvas.addEventListener('mousemove', async(e) => {
    const pos = getMousePos(e);

    // Update button hover states
    for (const button of buttons) {
        button.hover = button.containsPoint(pos.x, pos.y);
    }

    // Handle joystick dragging
    if (draggingJoystick && draggingJoystick.dragging) {
        draggingJoystick.updatePosition(pos.x, pos.y);
        await sendCommand({
            type: "gamepadJoystickMove",
            stickIndex: draggingJoystick.stickId,
            x: Math.round(draggingJoystick.xPos * 1000) / 1000,
            y: Math.round(draggingJoystick.yPos * 1000) / 1000
        });
    }
});

canvas.addEventListener('mouseup', async() => {
    // Release all buttons and stop continuous pressing
    for (const button of buttons) {
        button.pressed = false;

        // Stop continuous pressing for triggers
        if (button.buttonId === 6 || button.buttonId === 7) {
            stopButtonPress(button.buttonId);
        }
    }

    // Stop dragging joysticks and center them
    if (draggingJoystick) {
        draggingJoystick.dragging = false;
        draggingJoystick.resetPosition();
        await sendCommand({
            type: "gamepadJoystickMove",
            stickIndex: draggingJoystick.stickId,
            x: 0,
            y: 0
        });
        await sendCommand({
            type: "gamepadJoystickCenter",
            stickIndex: draggingJoystick.stickId
        });
        draggingJoystick = null;
    }
});

// Physical gamepad polling
function pollGamepads(): void {
    const gamepads = navigator.getGamepads();
    physicalGamepads = [];

    for (let i = 0; i < gamepads.length; i++) {
        const gamepad = gamepads[i];
        if (gamepad) {
            physicalGamepads.push(gamepad);
        }
    }

    updateStatus();
}

// Handle physical gamepad input
async function updatePhysicalGamepads() {
    const gamepads = navigator.getGamepads();

    for (let i = 0; i < gamepads.length; i++) {
        const gamepad = gamepads[i];
        if (!gamepad) continue;

        // Check buttons
        for (let j = 0; j < gamepad.buttons.length; j++) {
            const buttonId = buttonMapping[j];
            if (buttonId !== undefined) {

                const button = buttons.find(b => b.buttonId === buttonId);
                if (button) {
                    const wasPressed = button.pressed;
                    button.pressed = gamepad.buttons[j].pressed;

                    // Send command on button state change
                    if (!wasPressed && button.pressed) {
                        // Button pressed down
                        await sendCommand({
                            type: "gamepadButtonPressDown",
                            buttonIndex: buttonId
                        });
                    } else if (wasPressed && !button.pressed) {
                        // Button released
                        await sendCommand({
                            type: "gamepadButtonPressUp",
                            buttonIndex: buttonId
                        });
                    }
                }
            }
        }

        // Check analog sticks
        if (gamepad.axes.length >= 4) {
            // Left stick (axes 0, 1)
            const leftX = applyDeadzone(gamepad.axes[0]);
            const leftY = applyDeadzone(gamepad.axes[1]);

            if (joysticks[0]) {
                const prevX = joysticks[0].xPos;
                const prevY = joysticks[0].yPos;

                joysticks[0].xPos = leftX;
                joysticks[0].yPos = leftY;
                joysticks[0].stickX = joysticks[0].centerX + (leftX * joysticks[0].maxDistance);
                joysticks[0].stickY = joysticks[0].centerY + (leftY * joysticks[0].maxDistance);

                if (Math.abs(prevX - leftX) > 0.01 || Math.abs(prevY - leftY) > 0.01) {
                    await sendCommand({
                        type: "gamepadJoystickMove",
                        stickIndex: 0,
                        x: Math.round(leftX * 1000) / 1000,
                        y: Math.round(leftY * 1000) / 1000
                    });
                }
            }

            // Right stick (axes 2, 3)
            const rightX = applyDeadzone(gamepad.axes[2]);
            const rightY = applyDeadzone(gamepad.axes[3]);

            if (joysticks[1]) {
                const prevX = joysticks[1].xPos;
                const prevY = joysticks[1].yPos;

                joysticks[1].xPos = rightX;
                joysticks[1].yPos = rightY;
                joysticks[1].stickX = joysticks[1].centerX + (rightX * joysticks[1].maxDistance);
                joysticks[1].stickY = joysticks[1].centerY + (rightY * joysticks[1].maxDistance);

                if (Math.abs(prevX - rightX) > 0.01 || Math.abs(prevY - rightY) > 0.01) {
                    await sendCommand({
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

// Drawing function
function draw() {
    // Clear canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw title
    ctx.fillStyle = '#000';
    ctx.font = 'bold 28px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Gamepad Controller', 400, 30);

    // Draw gamepad body outline
    ctx.fillStyle = '#c8c8c8';
    ctx.beginPath();
    ctx.roundRect(120, 120, 560, 400, 30);
    ctx.fill();

    ctx.strokeStyle = '#000';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw all buttons
    for (const button of buttons) {
        button.draw(ctx);
    }

    // Draw all joysticks
    for (const joystick of joysticks) {
        joystick.draw(ctx);
    }

    // Draw instructions
    ctx.fillStyle = '#404040';
    ctx.font = '16px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('Click buttons or use physical gamepad', 10, 550);
    ctx.fillText('Drag joysticks or use analog sticks', 10, 570);
    ctx.fillText('Connect a gamepad and press any button to use it', 10, 590);
}

// Animation loop
async function animate() {
    pollGamepads();
    await updatePhysicalGamepads();
    draw();
    requestAnimationFrame(animate);
}

// Listen for gamepad connections
window.addEventListener('gamepadconnected', (e) => {
    console.log(`🎮 Gamepad connected: ${e.gamepad.id}`);
    pollGamepads();
});

window.addEventListener('gamepaddisconnected', (e) => {
    console.log(`🎮 Gamepad disconnected: ${e.gamepad.id}`);
    pollGamepads();
});

// Initialize
setupGamepadLayout();

// Setup trigger control input listeners
function setupTriggerControls() {
    const durationInput = document.getElementById('trigger-duration');
    const intervalInput = document.getElementById('trigger-interval');

    if (durationInput) {
        durationInput.addEventListener('input', (e) => {
            const target = e.target as HTMLInputElement;
            const value = parseInt(target.value);
            if (value >= 1 && value <= 1000) {
                triggerDuration = value;
                console.log(`🎯 Trigger duration updated to: ${triggerDuration}ms`);
            }
        });
    }

    if (intervalInput) {
        intervalInput.addEventListener('input', (e) => {
            const target = e.target as HTMLInputElement;
            const value = parseInt(target.value);
            if (value >= 1 && value <= 1000) {
                triggerInterval = value;
                console.log(`⏱️ Trigger interval updated to: ${triggerInterval}ms`);
            }
        });
    }
}

setupTriggerControls();
connectWebSocket();
animate();

// Cleanup on page unload
window.addEventListener('beforeunload', async() => {
    // Clear all button intervals - just clear the map since we're only tracking state
    buttonIntervals.clear();

    if (websocket && websocket.readyState === WebSocket.OPEN) {
        await sendCommand({
            type: "gamepadDestroy"
        });
        websocket.close();
    }
});