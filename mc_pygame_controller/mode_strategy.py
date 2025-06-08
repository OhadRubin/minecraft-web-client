"""
Mode Strategy Pattern Implementation for MinecraftController

This module implements the Strategy Pattern to eliminate mode-specific if/else 
logic scattered throughout the controller by creating specialized mode handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import time


class ModeStrategy(ABC):
    """Abstract base class for controller mode strategies."""

    def __init__(self, controller):
        """Initialize with reference to the controller for accessing shared state and utilities."""
        self.controller = controller

    @abstractmethod
    def handle_movement(self, x: float, z: float):
        """Handle movement commands for this mode."""
        pass

    @abstractmethod
    def handle_timed_action(
        self, 
        action_name: str, 
        duration: str, 
        pygame_down_cmd: Dict[str, Any] = None,
        pygame_up_cmd: Dict[str, Any] = None,
        **kwargs
    ):
        """Handle timed actions (clicks, jump, etc.) for this mode."""
        pass

    @abstractmethod
    def handle_toggle_action(self, action_name: str, state: bool, pygame_control: str = None):
        """Handle toggle actions (sneak, sprint) for this mode."""
        pass

    @abstractmethod
    def handle_simple_action(self, action_name: str, pygame_cmd: Dict[str, Any] = None, **params):
        """Handle simple one-shot actions (drop, swap, inventory, etc.) for this mode."""
        pass

    @abstractmethod
    def connect(self):
        """Initialize connection/setup for this mode."""
        pass

    @abstractmethod
    def process_continuous_state(self, mouse_pos, mouse_pressed, keys_pressed):
        """Process continuous state updates for this mode (e.g., button holds)."""
        pass


class PygameModeStrategy(ModeStrategy):
    """Strategy for pygame mode - sends WebSocket commands to Minecraft client."""

    def __init__(self, controller):
        super().__init__(controller)
        # Track previous movement state for continuous streaming
        self.was_moving = False

    def handle_movement(self, x: float, z: float):
        """Send movement command via WebSocket and log for MCP compatibility."""
        command = {"type": "move", "x": x, "z": z}
        self.controller.send_command_sync(command)

        # Log movement in pygame mode if logging enabled
        if self.controller.enable_logging and (abs(x) > 0.1 or abs(z) > 0.1):
            # Calculate duration based on movement magnitude (same as MCP mode)
            magnitude = (x**2 + z**2) ** 0.5
            duration = int(magnitude * 2000)  # Scale to reasonable duration
            self.controller.action_handler._log_mcp_command("walk", {"duration": duration})

    def handle_timed_action(
        self, 
        action_name: str, 
        duration: str, 
        pygame_down_cmd: Dict[str, Any] = None,
        pygame_up_cmd: Dict[str, Any] = None,
        **kwargs
    ):
        """Send pygame down/up commands and log MCP equivalent."""
        if pygame_down_cmd:
            self.controller.send_command_sync(pygame_down_cmd)
        if pygame_up_cmd:
            self.controller.send_command_sync(pygame_up_cmd)

        # Log the action in pygame mode
        mcp_params = {"duration": duration, **kwargs}
        self.controller.action_handler._log_mcp_command(action_name, mcp_params)

    def handle_toggle_action(self, action_name: str, state: bool, pygame_control: str = None):
        """Send pygame control command and log MCP equivalent."""
        if pygame_control:
            command = {"type": "control", "control": pygame_control, "state": state}
            self.controller.send_command_sync(command)

        self.controller.action_handler._log_mcp_command(action_name, {"state": state})

    def handle_simple_action(self, action_name: str, pygame_cmd: Dict[str, Any] = None, **params):
        """Send pygame command and log MCP equivalent."""
        if pygame_cmd:
            self.controller.send_command_sync(pygame_cmd)

        self.controller.action_handler._log_mcp_command(action_name, params)

    def connect(self):
        """Start WebSocket connection for pygame mode."""
        self.controller.start_websocket_connection()

    def process_continuous_state(self, mouse_pos, mouse_pressed, keys_pressed):
        """Process continuous state for pygame mode - handles streaming behavior."""
        # Handle continuous movement streaming - CRITICAL FIX!
        # In pygame mode, we need to send movement commands every frame while keys are held
        # The ActionHandler only sends when movement values change, but we need continuous streaming
        keyboard_move_x, keyboard_move_y = (
            self.controller.ui_manager.keyboard_movement.handle_keyboard(keys_pressed)
        )

        # Get joystick values by calculating from knob position
        joystick = self.controller.ui_manager.movement_joystick
        joystick_move_x = (joystick.knob_x - joystick.center_x) / joystick.radius
        joystick_move_y = (joystick.knob_y - joystick.center_y) / joystick.radius

        # Determine active movement (same logic as UI manager)
        movement_x, movement_z = 0.0, 0.0
        if abs(joystick_move_x) < 0.1 and abs(joystick_move_y) < 0.1:
            if abs(keyboard_move_x) > 0.1 or abs(keyboard_move_y) > 0.1:
                movement_x, movement_z = keyboard_move_x, keyboard_move_y
        else:
            movement_x, movement_z = joystick_move_x, joystick_move_y

        # Check if currently moving
        is_moving = abs(movement_x) > 0.1 or abs(movement_z) > 0.1

        # Send movement commands or stop commands based on state changes
        if is_moving:
            # Send continuous movement while keys are held
            command = {"type": "move", "x": movement_x, "z": movement_z}
            self.controller.send_command_sync(command)
        elif self.was_moving and not is_moving:
            # Send stop command when transitioning from moving to not moving
            command = {"type": "move", "x": 0.0, "z": 0.0}
            self.controller.send_command_sync(command)

        # Update movement state for next frame
        self.was_moving = is_moving

        # Check for continuous button holds (mining/building)
        left_click_state = self.controller.state.action_states.get("left_click", {})
        if left_click_state.get("active", False):
            # Left click is being held - send continuous mining command
            command = {
                "type": "documentMouseEvent",
                "button": 0,
                "action": "down",
                "updateMouse": True,
            }
            self.controller.send_command_sync(command)

        right_click_state = self.controller.state.action_states.get("right_click", {})
        if right_click_state.get("active", False):
            # Right click is being held - send continuous right click command
            command = {"type": "rightDown"}
            self.controller.send_command_sync(command)


class MCPModeStrategy(ModeStrategy):
    """Strategy for MCP mode - converts actions to MCP tool calls."""

    def handle_movement(self, x: float, z: float):
        """Convert movement to walk command with timing control."""
        # Only send walk command if enough time has passed (avoid spamming)
        if time.time() - self.controller.last_moved_in_mcp_mode > 2:
            # Calculate duration based on movement magnitude
            magnitude = (x**2 + z**2) ** 0.5
            # Use a fixed duration for consistency (calculated_duration could be used for scaling)
            self.handle_simple_action("walk", duration=1000)
            self.controller.last_moved_in_mcp_mode = time.time()

    def handle_timed_action(
        self, 
        action_name: str, 
        duration: str, 
        pygame_down_cmd: Dict[str, Any] = None,
        pygame_up_cmd: Dict[str, Any] = None,
        **kwargs
    ):
        """Execute MCP timed action."""
        # pygame commands not used in MCP mode (parameters kept for interface compatibility)
        _ = pygame_down_cmd, pygame_up_cmd  # Suppress unused warnings
        params = {"duration": duration, **kwargs}
        self.controller.handle_other_commands(action_name, **params)

    def handle_toggle_action(self, action_name: str, state: bool, pygame_control: str = None):
        """Execute MCP toggle action."""
        # pygame_control not used in MCP mode (parameter kept for interface compatibility)
        _ = pygame_control  # Suppress unused warning
        self.controller.handle_other_commands(action_name, state=state)

    def handle_simple_action(self, action_name: str, pygame_cmd: Dict[str, Any] = None, **params):
        """Execute MCP simple action."""
        # pygame_cmd not used in MCP mode (parameter kept for interface compatibility)
        _ = pygame_cmd  # Suppress unused warning
        self.controller.handle_other_commands(action_name, **params)

    def connect(self):
        """MCP mode doesn't need WebSocket connection."""
        print("MCP mode ready. No WebSocket connection needed.")

    def process_continuous_state(self, mouse_pos, mouse_pressed, keys_pressed):
        """MCP mode does not handle continuous state streaming - uses discrete actions only."""
        pass
