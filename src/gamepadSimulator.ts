// Minimal gamepad simulator - copied from gamepad-simulator and simplified
export const gamepadSimulator = {
  getGamepads: null as any,
  fakeController: {
    axes: [0, 0, 0, 0],
    buttons: Array.from({ length: 17 }, () => ({
      pressed: false,
      touched: false,
      value: 0,
    })),
    connected: false,
    id: "Standard gamepad by WebSocket Virtual",
    index: 0,
    mapping: "standard",
    timestamp: Math.floor(Date.now() / 1000),
  },

  create: function () {
    // Override navigator.getGamepads - NO VISUAL ELEMENTS
    if (!gamepadSimulator.getGamepads) {
      gamepadSimulator.getGamepads = navigator.getGamepads.bind(navigator);
      navigator.getGamepads = function () {
        const original = gamepadSimulator.getGamepads ? gamepadSimulator.getGamepads() : [];
        const result = Array.from(original);

        // Insert our virtual gamepad at index 0, shift others if needed
        if (gamepadSimulator.fakeController.connected) {
          result[0] = gamepadSimulator.fakeController;
        }

        return result as any;
      };
      console.log("[GamepadSimulator] Virtual gamepad API override installed (no visual)");
    }
  },

  connect: function () {
    const event = new Event("gamepadconnected") as any;
    gamepadSimulator.fakeController.connected = true;
    gamepadSimulator.fakeController.timestamp = Math.floor(Date.now() / 1000);
    event.gamepad = gamepadSimulator.fakeController;
    window.dispatchEvent(event);
    console.log("[GamepadSimulator] Virtual gamepad connected");
  },

  disconnect: function () {
    const event = new Event("gamepaddisconnected") as any;
    gamepadSimulator.fakeController.connected = false;
    gamepadSimulator.fakeController.timestamp = Math.floor(Date.now() / 1000);
    event.gamepad = gamepadSimulator.fakeController;
    window.dispatchEvent(event);
    console.log("[GamepadSimulator] Virtual gamepad disconnected");
  },

  destroy: function () {
    if (gamepadSimulator.fakeController.connected) {
      gamepadSimulator.disconnect();
    }
    if (gamepadSimulator.getGamepads) {
      navigator.getGamepads = gamepadSimulator.getGamepads;
      gamepadSimulator.getGamepads = null;
    }
    console.log("[GamepadSimulator] Virtual gamepad destroyed");
  },

  // Programmatic button press (for WebSocket commands)
  pressButton: function (buttonIndex: number, duration: number = 100) {
    if (buttonIndex < 0 || buttonIndex >= gamepadSimulator.fakeController.buttons.length) {
      console.warn(`[GamepadSimulator] Invalid button index: ${buttonIndex}`);
      return;
    }

    // Auto-setup: ensure gamepad is created and connected
    if (!gamepadSimulator.getGamepads) {
      gamepadSimulator.create();
    }
    if (!gamepadSimulator.fakeController.connected) {
      gamepadSimulator.connect();
    }

    // Set button pressed
    gamepadSimulator.fakeController.buttons[buttonIndex].pressed = true;
    gamepadSimulator.fakeController.buttons[buttonIndex].touched = true;
    gamepadSimulator.fakeController.buttons[buttonIndex].value = 1;
    gamepadSimulator.fakeController.timestamp = Math.floor(Date.now() / 1000);

    console.log(`[GamepadSimulator] Button ${buttonIndex} pressed for ${duration}ms`);

    // Auto-release after duration
    setTimeout(() => {
      gamepadSimulator.fakeController.buttons[buttonIndex].pressed = false;
      gamepadSimulator.fakeController.buttons[buttonIndex].touched = false;
      gamepadSimulator.fakeController.buttons[buttonIndex].value = 0;
      gamepadSimulator.fakeController.timestamp = Math.floor(Date.now() / 1000);
      console.log(`[GamepadSimulator] Button ${buttonIndex} released`);
    }, duration);
  },

  // Start button press (no auto-release)
  startButtonPress: function (buttonIndex: number) {
    if (buttonIndex < 0 || buttonIndex >= gamepadSimulator.fakeController.buttons.length) {
      console.warn(`[GamepadSimulator] Invalid button index: ${buttonIndex}`);
      return;
    }

    // Auto-setup: ensure gamepad is created and connected
    if (!gamepadSimulator.getGamepads) {
      gamepadSimulator.create();
    }
    if (!gamepadSimulator.fakeController.connected) {
      gamepadSimulator.connect();
    }

    // Set button pressed
    gamepadSimulator.fakeController.buttons[buttonIndex].pressed = true;
    gamepadSimulator.fakeController.buttons[buttonIndex].touched = true;
    gamepadSimulator.fakeController.buttons[buttonIndex].value = 1;
    gamepadSimulator.fakeController.timestamp = Math.floor(Date.now() / 1000);

    console.log(`[GamepadSimulator] Button ${buttonIndex} pressed (no auto-release)`);
  },

  // End button press
  endButtonPress: function (buttonIndex: number) {
    if (buttonIndex < 0 || buttonIndex >= gamepadSimulator.fakeController.buttons.length) {
      console.warn(`[GamepadSimulator] Invalid button index: ${buttonIndex}`);
      return;
    }

    // Release button
    gamepadSimulator.fakeController.buttons[buttonIndex].pressed = false;
    gamepadSimulator.fakeController.buttons[buttonIndex].touched = false;
    gamepadSimulator.fakeController.buttons[buttonIndex].value = 0;
    gamepadSimulator.fakeController.timestamp = Math.floor(Date.now() / 1000);

    console.log(`[GamepadSimulator] Button ${buttonIndex} released`);
  },

  // Set axis value
  setAxis: function (axisIndex: number, value: number) {
    if (axisIndex < 0 || axisIndex >= gamepadSimulator.fakeController.axes.length) {
      console.warn(`[GamepadSimulator] Invalid axis index: ${axisIndex}`);
      return;
    }
    gamepadSimulator.fakeController.axes[axisIndex] = Math.max(-1, Math.min(1, value));
    gamepadSimulator.fakeController.timestamp = Math.floor(Date.now() / 1000);
  },

  // Enhanced joystick features

  // Move a joystick to a specific position (x, y both from -1 to 1)
  moveJoystick: function (stickIndex: number, x: number, y: number) {
    if (stickIndex !== 0 && stickIndex !== 1) {
      console.warn(`[GamepadSimulator] Invalid stick index: ${stickIndex}. Use 0 for left stick, 1 for right stick`);
      return;
    }

    // Auto-setup: ensure gamepad is created and connected
    if (!gamepadSimulator.getGamepads) {
      gamepadSimulator.create();
    }
    if (!gamepadSimulator.fakeController.connected) {
      gamepadSimulator.connect();
    }

    const xAxisIndex = stickIndex * 2;     // Left stick: 0, Right stick: 2
    const yAxisIndex = stickIndex * 2 + 1; // Left stick: 1, Right stick: 3

    gamepadSimulator.setAxis(xAxisIndex, x);
    gamepadSimulator.setAxis(yAxisIndex, y);

    console.log(`[GamepadSimulator] ${stickIndex === 0 ? 'Left' : 'Right'} stick moved to (${x.toFixed(2)}, ${y.toFixed(2)})`);
  },

  // Move left joystick specifically
  moveLeftJoystick: function (x: number, y: number) {
    gamepadSimulator.moveJoystick(0, x, y);
  },

  // Move right joystick specifically  
  moveRightJoystick: function (x: number, y: number) {
    gamepadSimulator.moveJoystick(1, x, y);
  },

  // Reset joystick to center position
  centerJoystick: function (stickIndex: number) {
    gamepadSimulator.moveJoystick(stickIndex, 0, 0);
  },

  // Reset all joysticks to center
  centerAllJoysticks: function () {
    gamepadSimulator.centerJoystick(0); // Left stick
    gamepadSimulator.centerJoystick(1); // Right stick
  },

  // Animate joystick movement over time
  animateJoystick: function (stickIndex: number, fromX: number, fromY: number, toX: number, toY: number, duration: number = 1000) {
    if (stickIndex !== 0 && stickIndex !== 1) {
      console.warn(`[GamepadSimulator] Invalid stick index: ${stickIndex}. Use 0 for left stick, 1 for right stick`);
      return;
    }

    const startTime = Date.now();
    const deltaX = toX - fromX;
    const deltaY = toY - fromY;

    console.log(`[GamepadSimulator] Animating ${stickIndex === 0 ? 'left' : 'right'} stick from (${fromX.toFixed(2)}, ${fromY.toFixed(2)}) to (${toX.toFixed(2)}, ${toY.toFixed(2)}) over ${duration}ms`);

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Smooth easing function (ease-in-out)
      const eased = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2;

      const currentX = fromX + deltaX * eased;
      const currentY = fromY + deltaY * eased;

      gamepadSimulator.moveJoystick(stickIndex, currentX, currentY);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        console.log(`[GamepadSimulator] Animation complete for ${stickIndex === 0 ? 'left' : 'right'} stick`);
      }
    };

    requestAnimationFrame(animate);
  },

  // Simulate joystick input with auto-return to center
  pulseJoystick: function (stickIndex: number, x: number, y: number, duration: number = 500) {
    // Move to position
    gamepadSimulator.moveJoystick(stickIndex, x, y);

    // Return to center after duration
    setTimeout(() => {
      gamepadSimulator.centerJoystick(stickIndex);
    }, duration);

    console.log(`[GamepadSimulator] ${stickIndex === 0 ? 'Left' : 'Right'} stick pulsed to (${x.toFixed(2)}, ${y.toFixed(2)}) for ${duration}ms`);
  },

  // Circular movement for joystick (useful for testing)
  circularJoystickMovement: function (stickIndex: number, radius: number = 0.8, duration: number = 2000, clockwise: boolean = true) {
    const startTime = Date.now();
    const direction = clockwise ? 1 : -1;

    console.log(`[GamepadSimulator] Starting ${clockwise ? 'clockwise' : 'counter-clockwise'} circular movement for ${stickIndex === 0 ? 'left' : 'right'} stick`);

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = (elapsed / duration) % 1;
      const angle = progress * 2 * Math.PI * direction;

      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;

      gamepadSimulator.moveJoystick(stickIndex, x, y);

      if (elapsed < duration) {
        requestAnimationFrame(animate);
      } else {
        gamepadSimulator.centerJoystick(stickIndex);
        console.log(`[GamepadSimulator] Circular movement complete for ${stickIndex === 0 ? 'left' : 'right'} stick`);
      }
    };

    requestAnimationFrame(animate);
  },

  // Get current joystick position
  getJoystickPosition: function (stickIndex: number): { x: number, y: number } {
    if (stickIndex !== 0 && stickIndex !== 1) {
      console.warn(`[GamepadSimulator] Invalid stick index: ${stickIndex}. Use 0 for left stick, 1 for right stick`);
      return { x: 0, y: 0 };
    }

    const xAxisIndex = stickIndex * 2;     // Left stick: 0, Right stick: 2
    const yAxisIndex = stickIndex * 2 + 1; // Left stick: 1, Right stick: 3

    return {
      x: gamepadSimulator.fakeController.axes[xAxisIndex],
      y: gamepadSimulator.fakeController.axes[yAxisIndex]
    };
  },
};

// Make it available globally for debugging
(window as any).gamepadSimulator = gamepadSimulator;

export default gamepadSimulator;