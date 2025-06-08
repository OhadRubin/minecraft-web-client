import asyncio
import json
import websockets
import threading
import sys
import argparse
from typing import Optional, Dict, Any, Callable, List, Tuple
import time

import pygame

from .constants import *
from .look_path import LookPathTracker, LookPathVisualizationArea
from .ui_elements import (
    Button,
    ToggleButton,
    VirtualJoystick,
    KeyboardMovement,
    TouchArea,
)
from .mode_strategy import ModeStrategy, PygameModeStrategy, MCPModeStrategy
from .ui_manager import UIManager
from .controller_state import ControllerState
from mc_pygame_controller.camera_drag_handler import CameraDragHandler
import argparse


class MinecraftController:

    def __init__(
        self, mode="pygame", chain_args=None, sensitivity=5.0, enable_logging=False
    ):
        # Initialize centralized state
        self.state = ControllerState(
            mode=mode,
            sensitivity=sensitivity,
            enable_logging=enable_logging
        )

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Minecraft Web Client Controller")
        self.clock = pygame.time.Clock()

        # Look path tracking
        self.look_path_tracker = LookPathTracker(
            sensitivity=self.state.sensitivity, enable_logging=self.state.enable_logging, mode=self.state.mode
        )
        self.look_visualization = LookPathVisualizationArea(
            1230, 50, 350, 300
        )  # Right side visualization

        if chain_args is not None:
            self.state.chain = chain_args[1]
            self.state.servers = chain_args[0]
        else:
            self.state.servers = []
            self.state.chain = None

        # Connect LookPathTracker for MCP mode
        if self.state.mode == "mcp":
            self.look_path_tracker.set_execution_callback(self.execute_mcp_action)

        # Initialize mode strategy
        if self.state.mode == "pygame":
            self.strategy = PygameModeStrategy(self)
        elif self.state.mode == "mcp":
            self.strategy = MCPModeStrategy(self)
        else:
            raise ValueError(f"Unknown mode: {self.state.mode}")

        # Initialize UI Manager
        self.ui_manager = UIManager(self.screen, self.state, self.look_path_tracker, self.look_visualization)

        # Instantiate CameraDragHandler
        self.camera_drag_handler = CameraDragHandler(self.look_path_tracker)

        # Initialize action dispatch dictionary for cleaner action handling
        self._action_handlers = {
            "movement": lambda v: self.handle_movement(v[0], v[1]) if v else None,
            "camera_look": lambda v: self.handle_camera_look(v[0], v[1]) if v else None,
            "left_click": self.handle_left_click,
            "right_click": self.handle_right_click,
            "left_click_keyboard": self._handle_left_click_keyboard,
            "right_click_keyboard": self._handle_right_click_keyboard,
            "jump": self._handle_jump_action,
            "jump_keyboard": self._handle_jump_action,
            "sneak_toggled": self.handle_sneak,
            "sprint_toggled": self.handle_sprint,
            "inventory_pressed": lambda _: self.handle_inventory(),
            "drop_item_pressed": lambda _: self.handle_drop_item(),
            "swap_hands_pressed": lambda _: self.handle_swap_hands(),
            "clear_path_pressed": lambda _: self.handle_clear_path(),
            "test_status_pressed": lambda _: self.handle_test_status(),
            "save_demo_pressed": lambda _: self.handle_save_demonstration(),
            "hotbar_slot_pressed": self.handle_hotbar_slot,
        }

    # Property decorators for backward compatibility
    @property
    def mode(self):
        """Access mode through state for backward compatibility."""
        return self.state.mode

    @property
    def sensitivity(self):
        """Access sensitivity through state for backward compatibility."""
        return self.state.sensitivity

    @property
    def enable_logging(self):
        """Access enable_logging through state for backward compatibility."""
        return self.state.enable_logging

    @property
    def running(self):
        """Access running through state for backward compatibility."""
        return self.state.running

    @running.setter
    def running(self, value):
        """Set running through state for backward compatibility."""
        self.state.running = value

    @property
    def connected(self):
        """Access connected through state for backward compatibility."""
        return self.state.connected

    @connected.setter
    def connected(self, value):
        """Set connected through state for backward compatibility."""
        self.state.connected = value

    @property
    def current_hotbar_slot(self):
        """Access current_hotbar_slot through state for backward compatibility."""
        return self.state.current_hotbar_slot

    @current_hotbar_slot.setter
    def current_hotbar_slot(self, value):
        """Set current_hotbar_slot through state for backward compatibility."""
        self.state.current_hotbar_slot = value

    @property
    def last_hotbar_slot(self):
        """Access last_hotbar_slot through state for backward compatibility."""
        return self.state.last_hotbar_slot

    @last_hotbar_slot.setter
    def last_hotbar_slot(self, value):
        """Set last_hotbar_slot through state for backward compatibility."""
        self.state.last_hotbar_slot = value

    @property
    def last_movement(self):
        """Access last_movement through state for backward compatibility."""
        return self.state.last_movement

    @last_movement.setter
    def last_movement(self, value):
        """Set last_movement through state for backward compatibility."""
        self.state.last_movement = value

    @property
    def last_moved_in_mcp_mode(self):
        """Access last_moved_in_mcp_mode through state for backward compatibility."""
        return self.state.last_moved_in_mcp_mode

    @last_moved_in_mcp_mode.setter
    def last_moved_in_mcp_mode(self, value):
        """Set last_moved_in_mcp_mode through state for backward compatibility."""
        self.state.last_moved_in_mcp_mode = value

    @property
    def websocket(self):
        """Access websocket through state for backward compatibility."""
        return self.state.websocket

    @websocket.setter
    def websocket(self, value):
        """Set websocket through state for backward compatibility."""
        self.state.websocket = value

    @property
    def connection_thread(self):
        """Access connection_thread through state for backward compatibility."""
        return self.state.connection_thread

    @connection_thread.setter
    def connection_thread(self, value):
        """Set connection_thread through state for backward compatibility."""
        self.state.connection_thread = value

    @property
    def loop(self):
        """Access loop through state for backward compatibility."""
        return self.state.loop

    @loop.setter
    def loop(self, value):
        """Set loop through state for backward compatibility."""
        self.state.loop = value

    @property
    def mcp_executor(self):
        """Access mcp_executor through state for backward compatibility."""
        return self.state.mcp_executor

    @mcp_executor.setter
    def mcp_executor(self, value):
        """Set mcp_executor through state for backward compatibility."""
        self.state.mcp_executor = value

    @property
    def chain(self):
        """Access chain through state for backward compatibility."""
        return self.state.chain

    @property
    def servers(self):
        """Access servers through state for backward compatibility."""
        return self.state.servers

    # Helper methods for action dispatch dictionary

    def _handle_jump_action(self, state: bool):
        """Handle jump action, managing combined state from button and keyboard."""
        if not hasattr(self, '_last_jump_state'):
            self._last_jump_state = False

        if state != self._last_jump_state:
            self.handle_jump(state)
            self._last_jump_state = state

    def _handle_left_click_keyboard(self, keyboard_state: bool):
        """Handle left click keyboard input, combining with button state."""
        # Get button state from UI manager
        button_pressed = getattr(self.ui_manager, "left_click_btn", None)
        button_state = button_pressed.is_pressed if button_pressed else False

        # Combine keyboard and button states (OR logic)
        combined_state = keyboard_state or button_state
        self.handle_left_click(combined_state)

    def _handle_right_click_keyboard(self, keyboard_state: bool):
        """Handle right click keyboard input, combining with button state."""
        # Get button state from UI manager
        button_pressed = getattr(self.ui_manager, "right_click_btn", None)
        button_state = button_pressed.is_pressed if button_pressed else False

        # Combine keyboard and button states (OR logic)
        combined_state = keyboard_state or button_state
        self.handle_right_click(combined_state)

    def _calculate_duration(self, start_time: Optional[float]) -> str:
        """Calculate duration string from start time - updated with more options"""
        if not start_time:
            return "medium"

        duration_ms = int((time.time() - start_time) * 1000)

        # Updated duration mapping to match MCP server capabilities
        if duration_ms < 150:
            return "very_short"  # 100ms
        elif duration_ms < 750:
            return "short"  # 500ms
        elif duration_ms < 1500:
            return "medium"  # 1000ms
        elif duration_ms < 3500:
            return "long"  # 2000ms
        elif duration_ms < 7500:
            return "very_long"  # 5000ms
        else:
            return "very_very_long"  # 10000ms

    def _log_mcp_command(self, tool: str, parameters: Dict[str, Any]):
        """Log MCP command if logging is enabled"""
        if self.enable_logging:
            mcp_command = {"tool": tool, "parameters": parameters}
            print(f"LOGGED: {mcp_command}")

    def _handle_timed_action(
        self,
        action_name: str,
        pressed: bool,
        pygame_down_cmd: Dict[str, Any],
        pygame_up_cmd: Dict[str, Any],
        mcp_tool: str,
        mcp_params_func: Callable[[str], Dict[str, Any]] = None,
    ):
        """Generic handler for timed actions (clicks, jump, etc.)"""
        state = self.state.action_states[action_name]

        if pressed and not state["active"]:
            print(f"{action_name.upper()} DOWN - sending command")
            state["start_time"] = time.time()
            state["active"] = True

        elif not pressed and state["active"]:
            print(f"{action_name.upper()} UP - sending command")

            duration = self._calculate_duration(state["start_time"])
            state["start_time"] = None

            # Use strategy to handle the action
            kwargs = mcp_params_func(duration) if mcp_params_func else {}
            self.strategy.handle_timed_action(
                mcp_tool, 
                duration, 
                pygame_down_cmd=pygame_down_cmd,
                pygame_up_cmd=pygame_up_cmd,
                **kwargs
            )

            state["active"] = False

    def _handle_toggle_action(
        self, action_name: str, toggled: bool, pygame_control: str, mcp_tool: str
    ):
        """Generic handler for toggle actions (sneak, sprint)"""
        state = self.state.action_states[action_name]

        if toggled != state["active"]:
            self.strategy.handle_toggle_action(mcp_tool, toggled, pygame_control)
            state["active"] = toggled

    def _detect_key_edge(self, key_name: str, current_state: bool) -> tuple[bool, bool]:
        """Detect key press/release edges. Returns (just_pressed, just_released)"""
        last_state = self.state.last_key_states.get(key_name, False)
        self.state.last_key_states[key_name] = current_state

        just_pressed = current_state and not last_state
        just_released = not current_state and last_state

        return just_pressed, just_released

    async def connect_websocket(self):
        try:
            uri = "ws://localhost:8081"
            print(f"Connecting to {uri}...")
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print("Connected to Minecraft Web Client!")

            # Register client based on mode
            init_message = {"init": self.mode}
            await self.websocket.send(json.dumps(init_message))
            print(f"Registered as {self.mode} client")

            # Keep connection alive
            while self.connected and self.running:
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connected = False

    def start_websocket_connection(self):
        """Start WebSocket connection in a separate thread"""

        def run_async():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.connect_websocket())

        self.connection_thread = threading.Thread(target=run_async, daemon=True)
        self.connection_thread.start()

    async def send_command_async(self, command: dict):
        """Async method to send command"""
        if self.websocket and self.connected:
            try:
                await self.websocket.send(json.dumps(command))
                print(f"Sent command: {command}")
            except Exception as e:
                print(f"Error sending command: {e}")
                self.connected = False

    def send_command_sync(self, command: dict):
        """Send command instantly from main thread"""
        if self.connected and self.loop and not self.loop.is_closed():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.send_command_async(command), self.loop
                )
                # Don't wait for the result to keep it instant
            except Exception as e:
                print(f"Error sending command: {e}")
                self.connected = False

    def handle_movement(self, x: float, y: float):
        # Convert joystick coordinates to movement commands
        # y maps directly to z: joystick up (negative y) = forward (negative z)
        movement_x = x
        movement_z = y  # Remove the inversion - up should be forward (negative z)

        # Only send if movement changed significantly
        if (
            abs(movement_x - self.last_movement[0]) > 0.1
            or abs(movement_z - self.last_movement[1]) > 0.1
        ):
            self.strategy.handle_movement(movement_x, movement_z)
            self.last_movement = (movement_x, movement_z)

    def handle_camera_look(self, delta_x: int, delta_y: int):
        if delta_x != 0 or delta_y != 0:
            # Scale the movement for better sensitivity
            scaled_x = delta_x * 2
            scaled_y = delta_y * 2

            # Add to path tracker
            self.look_path_tracker.add_movement(scaled_x, scaled_y)

            # Only send WebSocket command in pygame mode
            # In MCP mode, LookPathTracker will handle conversion via callback
            if self.mode == "pygame":
                command = {"type": "look", "movementX": scaled_x, "movementY": scaled_y}
                self.send_command_sync(command)

    def handle_left_click(self, pressed: bool):
        """Handle left click using the generic timed action handler"""
        self._handle_timed_action(
            "left_click",
            pressed,
            {
                "type": "documentMouseEvent",
                "button": 0,
                "action": "down",
                "updateMouse": True,
            },
            {
                "type": "documentMouseEvent",
                "button": 0,
                "action": "up",
                "updateMouse": False,
            },
            "leftClick",
        )

    def handle_right_click(self, pressed: bool):
        """Handle right click using the generic timed action handler"""
        self._handle_timed_action(
            "right_click",
            pressed,
            {"type": "rightDown"},
            {"type": "rightUp"},
            "right_click",
        )

    def handle_jump(self, pressed: bool):
        """Handle jump using the generic timed action handler"""
        self._handle_timed_action(
            "jump",
            pressed,
            {"type": "control", "control": "jump", "state": True},
            {"type": "control", "control": "jump", "state": False},
            "jump",
        )

    def handle_sneak(self, toggled: bool):
        """Handle sneak using the generic toggle handler"""
        self._handle_toggle_action("sneak", toggled, "sneak", "sneak")

    def handle_sprint(self, toggled: bool):
        """Handle sprint using the generic toggle handler"""
        self._handle_toggle_action("sprint", toggled, "sprint", "sprint")

    def handle_control_button(self, control: str, state: bool):
        command = {"type": "control", "control": control, "state": state}
        self.send_command_sync(command)

    def handle_inventory(self):
        # Send inventory command (toggle)
        self.strategy.handle_simple_action(
            "toggleInventory", 
            pygame_cmd={"type": "inventory"}
        )

    def handle_hotbar_slot(self, slot: int):
        """Handle hotbar slot selection (slot should be 0-8)"""
        if 0 <= slot <= 8 and slot != self.state.last_hotbar_slot:
            print(f"HOTBAR SLOT {slot + 1} - sending command")
            self.strategy.handle_simple_action(
                "setHotbarSlot",
                pygame_cmd={"type": "setHotbarSlot", "slot": slot},
                slot=slot
            )
            self.state.current_hotbar_slot = slot
            self.state.last_hotbar_slot = slot
            # Update backward compatibility properties
            self.current_hotbar_slot = slot
            self.last_hotbar_slot = slot

    def handle_drop_item(self):
        """Handle dropping 1 item from current hotbar slot"""
        print("DROP ITEM - sending command")
        self.strategy.handle_simple_action(
            "dropItem",
            pygame_cmd={"type": "dropItem", "amount": 1},
            amount=1
        )

    def handle_swap_hands(self):
        """Handle swapping main hand and off-hand items"""
        print("SWAP HANDS - sending command")
        self.strategy.handle_simple_action(
            "swapHands",
            pygame_cmd={"type": "swapHands"}
        )

    def handle_clear_path(self):
        """Handle clearing the look path"""
        self.look_path_tracker.clear_history()
        print("Look path cleared!")

    def execute_mcp_action(self, mcp_command):
        """Execute MCP-formatted action directly"""
        if self.mcp_executor:
            print(f"🎮 Executing: {mcp_command['tool']}({mcp_command['parameters']})")
            # Call the sync version that just captures the action
            self.mcp_executor.capture_command(mcp_command)
        else:
            print(
                f"🎮 MCP Command (no executor): {mcp_command['tool']}({mcp_command['parameters']})"
            )

    def set_mcp_executor(self, executor):
        """Set the MCP command executor"""
        self.mcp_executor = executor

    def convert_to_mcp_format(self, command_type, params):
        """Convert pygame commands to MCP format"""
        # Simple mapping for clicks, movement, etc.
        if command_type == "left_click" or command_type == "leftClick":
            return {
                "tool": "leftClick",
                "parameters": {"duration": params.get("duration", "medium")},
            }
        elif command_type == "right_click" or command_type == "rightClick":
            return {
                "tool": "rightClick",
                "parameters": {"duration": params.get("duration", "medium")},
            }
        elif command_type == "walk":
            return {
                "tool": "walk",
                "parameters": {"duration": params.get("duration", 1000)},
            }
        elif command_type == "setHotbarSlot":
            return {
                "tool": "setHotbarSlot",
                "parameters": {"slot": params.get("slot", 0)},
            }
        elif command_type == "jump":
            return {
                "tool": "jump",
                "parameters": {"duration": params.get("duration", "short")},
            }
        elif command_type == "sneak":
            return {
                "tool": "sneak",
                "parameters": {"state": params.get("state", True)},
            }
        elif command_type == "sprint":
            return {
                "tool": "sprint",
                "parameters": {"state": params.get("state", True)},
            }
        elif command_type == "toggleInventory":
            return {
                "tool": "toggleInventory",
                "parameters": {},
            }
        elif command_type == "dropItem":
            return {
                "tool": "dropItem",
                "parameters": {"amount": params.get("amount", 1)},
            }
        elif command_type == "swapHands":
            return {
                "tool": "swapHands",
                "parameters": {},
            }
        # Add more mappings as needed
        return None

    def handle_other_commands(self, command_type, **params):
        """Execute non-look MCP commands directly"""
        if self.mode == "mcp" and self.mcp_executor:
            # Simple mapping for clicks, movement, etc.
            mcp_command = self.convert_to_mcp_format(command_type, params)
            if mcp_command:
                self.execute_mcp_action(mcp_command)

    def _process_frame(self):
        """Process a single frame of input and rendering. Common logic for both game loops."""
        # Handle pygame events that need to be caught early
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state.running = False
                return False  # Signal to exit loop
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state.running = False
                    return False  # Signal to exit loop
                elif event.key == pygame.K_r and self.state.mode == "pygame":
                    # Reconnect - only in pygame mode
                    self.state.connected = False
                    self.start_websocket_connection()

        # Get current input state
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed_buttons = pygame.mouse.get_pressed()
        mouse_pressed = mouse_pressed_buttons[0]  # Left click for UIManager and other existing logic
        keys_pressed = pygame.key.get_pressed()

        # New camera drag handling
        scaled_mouse_pos = self.ui_manager.get_scaled_mouse_pos(mouse_pos)
        is_in_cam_area = self.ui_manager.camera_area.is_touching(scaled_mouse_pos)
        # mouse_pressed_buttons[0] is the left mouse button state
        self.camera_drag_handler.update(is_in_cam_area, mouse_pressed_buttons[0])

        # Process all inputs through UIManager (discrete actions)
        ui_actions = self.ui_manager.process_inputs(mouse_pos, mouse_pressed, keys_pressed)
        keyboard_actions = self.ui_manager.process_keyboard_shortcuts(keys_pressed)

        # Handle all actions returned by UIManager
        self._process_ui_actions(ui_actions + keyboard_actions)

        # Process continuous state for streaming behavior (RESTORED)
        self._process_continuous_state(mouse_pos, mouse_pressed, keys_pressed)

        # Handle keyboard shortcuts edge detection (RESTORED)
        self._handle_keyboard_shortcuts_edge_detection(keys_pressed)

        # Draw everything using UIManager
        self.ui_manager.draw()

        return True  # Continue running

    def _process_continuous_state(self, mouse_pos, mouse_pressed, keys_pressed):
        """Process continuous state that needs streaming every frame (RESTORED)"""
        # This ensures continuous streaming for held inputs that need constant updates
        # NOTE: This complements the discrete action system with continuous state processing
        # Movement is already handled properly by the UI manager, so we focus on button holds

        # Only process continuous streaming in pygame mode
        if self.state.mode != "pygame":
            return

        # Check for continuous button holds (mining/building)
        # In pygame mode, we need to send continuous "button held" commands
        left_click_state = self.state.action_states.get("left_click", {})
        if left_click_state.get("active", False):
            # Left click is being held - send continuous mining command
            command = {
                "type": "documentMouseEvent",
                "button": 0,
                "action": "down",
                "updateMouse": True,
            }
            self.send_command_sync(command)

        right_click_state = self.state.action_states.get("right_click", {})
        if right_click_state.get("active", False):
            # Right click is being held - send continuous right click command
            command = {"type": "rightDown"}
            self.send_command_sync(command)

        # NOTE: Movement streaming is already handled properly by the UI manager
        # in process_inputs() -> handle_movement() flow, so we don't duplicate it here

    def _handle_keyboard_shortcuts_edge_detection(self, keys_pressed):
        """Handle keyboard shortcuts that require edge detection (RESTORED)"""
        # This method handles keyboard shortcuts that need precise press/release detection
        # It was removed in the refactor but is essential for proper keyboard handling

        # Handle hotbar slot shortcuts (1-9 keys)
        for i, key in enumerate(
            [
                pygame.K_1,
                pygame.K_2,
                pygame.K_3,
                pygame.K_4,
                pygame.K_5,
                pygame.K_6,
                pygame.K_7,
                pygame.K_8,
                pygame.K_9,
            ]
        ):
            key_name = f"hotbar_{i}"
            just_pressed, just_released = self._detect_key_edge(
                key_name, keys_pressed[key]
            )

            if just_pressed:
                self.handle_hotbar_slot(i)

        # Handle drop item (Q key)
        just_pressed, just_released = self._detect_key_edge(
            "drop_item", keys_pressed[pygame.K_q]
        )
        if just_pressed:
            self.handle_drop_item()

        # Handle swap hands (F key)
        just_pressed, just_released = self._detect_key_edge(
            "swap_hands", keys_pressed[pygame.K_f]
        )
        if just_pressed:
            self.handle_swap_hands()

        # Handle inventory (E key)
        just_pressed, just_released = self._detect_key_edge(
            "inventory", keys_pressed[pygame.K_e]
        )
        if just_pressed:
            self.handle_inventory()

    def run(self):
        print(f"Starting Minecraft Controller in {self.state.mode.upper()} mode...")

        # Initialize connection using strategy
        self.strategy.connect()

        if self.state.mode == "pygame":
            print("Commands will be forwarded to the Minecraft bot")
            print(
                "Make sure the Minecraft web client server is running on localhost:8081"
            )
            # Use traditional pygame event loop for pygame mode
            self._run_pygame_loop()
        else:
            print("Commands will be converted to MCP format and executed via callback")
            print("No WebSocket connection needed in MCP mode")
            # MCP mode is now handled by handle_interactive_session function
            print("MCP mode should be started via handle_interactive_session()")

    def _run_pygame_loop(self):
        """Traditional pygame event loop for pygame mode."""
        while self.state.running:
            if not self._process_frame():
                break
            self.clock.tick(FPS)

    def _process_ui_actions(self, actions: List[Tuple[str, Any]]):
        """Process actions returned by UIManager using dispatch dictionary."""
        for action_name, value in actions:
            handler = self._action_handlers.get(action_name)
            if handler:
                handler(value)
            else:
                # Unknown action - log warning but don't crash
                if action_name:  # Don't warn for empty action names
                    print(f"Warning: No handler for action '{action_name}'")

    async def animation_loop(self):
        """Main animation loop for async modes."""
        while self.state.running:
            if not self._process_frame():
                break
            # Async frame rate limiting
            await asyncio.sleep(1 / FPS)

    async def test_get_bot_status_startup(self, chain):
        """Test getBotStatus at startup"""
        try:
            print("🧪 Testing getBotStatus at startup...")
            result = await chain.tools_mapping["getBotStatus"]()
            print(f"📊 Startup getBotStatus result: {result}")
        except Exception as e:
            print(f"❌ Startup getBotStatus failed: {e}")

    async def execute_mcp_command_async(self, command_name, **params):
        """Execute MCP command asynchronously and return result"""
        if not self.command_queue:
            print("❌ Command queue not initialized")
            return None

        # Put command in queue
        await self.command_queue.put({"command": command_name, "params": params})

        # Wait for result
        if self.result_queue:
            try:
                result_data = await asyncio.wait_for(
                    self.result_queue.get(), timeout=10.0
                )
                if result_data.get("success"):
                    return result_data.get("result")
                else:
                    print(f"❌ MCP command failed: {result_data.get('error')}")
                    return None
            except asyncio.TimeoutError:
                print(f"⏰ MCP command timed out: {command_name}")
                return None

        return None

    def handle_test_status(self):
        """Handle test getBotStatus button click"""
        if self.mode == "mcp" and self.chain and self.chain.tools_mapping:
            print("🧪 Manual getBotStatus test triggered!")
            # Create a task to run the test
            asyncio.create_task(self._trigger_get_bot_status())
        else:
            print("⚠️ getBotStatus test only available in MCP mode")

    async def _trigger_get_bot_status(self):
        """Trigger getBotStatus command asynchronously"""
        try:
            result = await self.chain.tools_mapping["getBotStatus"]()
            print(f"🎯 Manual getBotStatus result: {result}")
        except Exception as e:
            print(f"❌ Manual getBotStatus failed: {e}")

    def handle_save_demonstration(self):
        """Handle saving a demonstration step"""
        if self.mode == "mcp" and self.mcp_executor:
            print("💾 Saving demonstration step...")
            # Generate a context description based on recent actions
            user_context = "exploring and performing actions"
            success = self.mcp_executor.save_demonstration_step(user_context)
            if success:
                print("✅ Demonstration step saved successfully!")
            else:
                print("⚠️ No actions to save in this step")
        else:
            print("⚠️ Demonstration saving only available in MCP mode")
