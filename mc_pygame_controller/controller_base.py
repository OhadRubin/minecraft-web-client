"""
Minecraft Web Client Controller - Refactored for DRY Principles

Major refactoring improvements:
1. Eliminated code duplication in click/action handlers using generic _handle_timed_action and _handle_toggle_action
2. Centralized keyboard edge detection with _detect_key_edge method
3. Unified logging with _log_mcp_command utility
4. Updated duration mapping to match MCP server capabilities (very_short to very_very_long)
5. Consolidated UI initialization into _init_ui_buttons and _init_hotbar_buttons
6. Refactored keyboard handling into reusable _handle_keyboard_shortcuts method
7. Extracted camera drag handling into _handle_camera_drag_state method
8. Simplified state management with dictionaries instead of individual attributes
"""

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
        
        # For backward compatibility, keep direct access to commonly used properties
        self.mode = self.state.mode
        self.sensitivity = self.state.sensitivity
        self.enable_logging = self.state.enable_logging
        self.running = self.state.running
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Minecraft Web Client Controller")
        self.clock = pygame.time.Clock()

        # Look path tracking
        self.look_path_tracker = LookPathTracker(
            sensitivity=sensitivity, enable_logging=enable_logging, mode=mode
        )
        self.look_visualization = LookPathVisualizationArea(
            1230, 50, 350, 300
        )  # Right side visualization

        if chain_args is not None:
            self.chain = chain_args[1]
            self.servers = chain_args[0]
        else:
            self.servers = []
            self.chain = None

        # For backward compatibility, provide direct access to state properties
        self.current_hotbar_slot = 0  # Will be updated to use state
        self.last_hotbar_slot = -1  # Will be updated to use state
        self.websocket = None  # Will be updated to use state
        self.connected = False  # Will be updated to use state
        self.connection_thread = None  # Will be updated to use state
        self.loop = None  # Will be updated to use state
        self.last_movement = (0.0, 0.0)  # Will be updated to use state
        self._action_states = self.state.action_states
        self.last_moved_in_mcp_mode = self.state.last_moved_in_mcp_mode
        self.camera_was_touching = False  # Will be updated to use state
        self._key_states = self.state.key_states
        self._last_key_states = self.state.last_key_states
        self.mcp_executor = self.state.mcp_executor

        # Connect LookPathTracker for MCP mode
        if self.mode == "mcp":
            self.look_path_tracker.set_execution_callback(self.execute_mcp_action)

        # Initialize mode strategy
        if self.mode == "pygame":
            self.strategy = PygameModeStrategy(self)
        elif self.mode == "mcp":
            self.strategy = MCPModeStrategy(self)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        # Initialize UI Manager
        self.ui_manager = UIManager(self.screen, self.state, self.look_path_tracker, self.look_visualization)

        # Asyncio integration (following asyncio_pygame_example.py pattern)
        self.event_loop = self.state.event_loop
        self.event_queue = self.state.event_queue
        self.command_queue = self.state.command_queue
        self.result_queue = self.state.result_queue


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
        state = self._action_states[action_name]

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
        state = self._action_states[action_name]

        if toggled != state["active"]:
            self.strategy.handle_toggle_action(mcp_tool, toggled, pygame_control)
            state["active"] = toggled

    def _detect_key_edge(self, key_name: str, current_state: bool) -> tuple[bool, bool]:
        """Detect key press/release edges. Returns (just_pressed, just_released)"""
        last_state = self._last_key_states.get(key_name, False)
        self._last_key_states[key_name] = current_state

        just_pressed = current_state and not last_state
        just_released = not current_state and last_state

        return just_pressed, just_released

    def _handle_camera_drag_state(self, mouse_pressed: bool):
        """Handle camera drag state changes for look tracking"""
        camera_is_clicking = self.ui_manager.camera_area.is_touching and mouse_pressed
        prev_clicking = getattr(self, "camera_was_clicking", False)

        if camera_is_clicking != prev_clicking:
            print(
                f"🔍 Camera state change: clicking={camera_is_clicking}, was_clicking={prev_clicking}"
            )

        if camera_is_clicking and not prev_clicking:
            print("🖱️ Mouse pressed in camera area - starting drag tracking")
            self.look_path_tracker.start_mouse_tracking()
            self.camera_was_clicking = True
        elif not mouse_pressed and prev_clicking:
            print("🖱️ Mouse released - ending drag tracking")
            self.look_path_tracker.stop_mouse_tracking()
            self.camera_was_clicking = False

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


    def run(self):
        print(f"Starting Minecraft Controller in {self.mode.upper()} mode...")
        
        # Initialize connection using strategy
        self.strategy.connect()
        
        if self.mode == "pygame":
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
        """Traditional pygame event loop for pygame mode"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r:
                        # Reconnect
                        self.state.connected = False
                        self.connected = False  # Backward compatibility
                        self.start_websocket_connection()

            # Get mouse state
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()[0]  # Left click

            # Get keyboard state
            keys_pressed = pygame.key.get_pressed()

            # Process UI inputs through UIManager
            ui_actions = self.ui_manager.process_inputs(mouse_pos, mouse_pressed, keys_pressed)
            keyboard_actions = self.ui_manager.process_keyboard_shortcuts(keys_pressed)
            
            # Handle all actions returned by UIManager
            self._process_ui_actions(ui_actions + keyboard_actions)
            
            # Handle keyboard shortcuts that need edge detection
            self._handle_keyboard_shortcuts_edge_detection(keys_pressed)

            # Draw everything using UIManager
            self.ui_manager.draw()
            self.clock.tick(FPS)

    def _process_ui_actions(self, actions: List[Tuple[str, Any]]):
        """Process actions returned by UIManager."""
        for action_name, value in actions:
            if action_name == "movement" and value:
                self.handle_movement(value[0], value[1])
                
            elif action_name == "camera_look" and value:
                self.handle_camera_look(value[0], value[1])
                
            elif action_name == "camera_drag_state":
                mouse_pressed, camera_is_clicking = value
                self._handle_camera_drag_state(mouse_pressed)
                
            elif action_name == "left_click":
                self.handle_left_click(value)
                
            elif action_name == "right_click":
                self.handle_right_click(value)
                
            elif action_name == "left_click_keyboard":
                # Combine with button state
                button_pressed = getattr(self.ui_manager, 'left_click_btn', None)
                combined = value or (button_pressed and button_pressed.is_pressed)
                self.handle_left_click(combined)
                
            elif action_name == "right_click_keyboard":
                # Combine with button state
                button_pressed = getattr(self.ui_manager, 'right_click_btn', None)
                combined = value or (button_pressed and button_pressed.is_pressed)
                self.handle_right_click(combined)
                
            elif action_name == "jump" or action_name == "jump_keyboard":
                # Combine button and keyboard input
                button_state = action_name == "jump" and value
                keyboard_state = action_name == "jump_keyboard" and value
                if hasattr(self, '_last_jump_state'):
                    combined = button_state or keyboard_state
                    if combined != self._last_jump_state:
                        self.handle_jump(combined)
                        self._last_jump_state = combined
                else:
                    self._last_jump_state = button_state or keyboard_state
                    self.handle_jump(self._last_jump_state)
                
            elif action_name == "sneak_toggled":
                self.handle_sneak(value)
                
            elif action_name == "sprint_toggled":
                self.handle_sprint(value)
                
            elif action_name == "inventory_pressed":
                self.handle_inventory()
                
            elif action_name == "drop_item_pressed":
                self.handle_drop_item()
                
            elif action_name == "swap_hands_pressed":
                self.handle_swap_hands()
                
            elif action_name == "clear_path_pressed":
                self.handle_clear_path()
                
            elif action_name == "test_status_pressed":
                self.handle_test_status()
                
            elif action_name == "save_demo_pressed":
                self.handle_save_demonstration()
                
            elif action_name == "hotbar_slot_pressed":
                self.handle_hotbar_slot(value)
                
            elif action_name == "keyboard_shortcuts":
                # Handle special keyboard shortcuts that need edge detection
                # This is processed separately in _handle_keyboard_shortcuts_edge_detection
                pass
    
    def _handle_keyboard_shortcuts_edge_detection(self, keys_pressed):
        """Handle keyboard shortcuts that require edge detection."""
        # Handle Q key (drop item)
        q_current = keys_pressed[pygame.K_q]
        q_just_pressed, _ = self._detect_key_edge("q_action", q_current)
        if q_just_pressed:
            print("Q pressed detected! (Drop item)")
            self.handle_drop_item()

        # Handle F key (swap hands)
        f_current = keys_pressed[pygame.K_f]
        f_just_pressed, _ = self._detect_key_edge("f_action", f_current)
        if f_just_pressed:
            print("F pressed detected! (Swap hands)")
            self.handle_swap_hands()

        # Handle hotbar keys (1-9)
        hotbar_keys = [
            pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
            pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9,
        ]
        for i, key in enumerate(hotbar_keys):
            key_current = keys_pressed[key]
            key_just_pressed, _ = self._detect_key_edge(f"hotbar_{i}", key_current)
            if key_just_pressed:
                print(f"Hotbar key {i + 1} pressed!")
                self.handle_hotbar_slot(i)

        # Handle C key (clear path)
        c_current = keys_pressed[pygame.K_c]
        c_just_pressed, _ = self._detect_key_edge("c_action", c_current)
        if c_just_pressed:
            print("Look path cleared with C key!")
            self.handle_clear_path()

    def _handle_all_inputs(self, mouse_pos, mouse_pressed, keys_pressed):
        """Legacy input handler - replaced by UIManager.process_inputs()"""
        # This method is deprecated and replaced by UIManager
        # Keeping for backward compatibility but delegating to UIManager
        ui_actions = self.ui_manager.process_inputs(mouse_pos, mouse_pressed, keys_pressed)
        keyboard_actions = self.ui_manager.process_keyboard_shortcuts(keys_pressed)
        
        # Process all actions
        self._process_ui_actions(ui_actions + keyboard_actions)
        
        # Handle keyboard shortcuts that need edge detection
        self._handle_keyboard_shortcuts_edge_detection(keys_pressed)

    def _handle_keyboard_shortcuts(self, q_current, f_current, keys_pressed):
        """Handle keyboard shortcuts with proper press/release detection"""
        # Handle Q key (drop item)
        q_just_pressed, _ = self._detect_key_edge("q_action", q_current)
        if q_just_pressed:
            print("Q pressed detected! (Drop item)")
            self.handle_drop_item()

        # Handle F key (swap hands)
        f_just_pressed, _ = self._detect_key_edge("f_action", f_current)
        if f_just_pressed:
            print("F pressed detected! (Swap hands)")
            self.handle_swap_hands()

        # Handle hotbar keys (1-9)
        hotbar_keys = [
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
        for i, key in enumerate(hotbar_keys):
            key_current = keys_pressed[key]
            key_just_pressed, _ = self._detect_key_edge(f"hotbar_{i}", key_current)
            if key_just_pressed:
                print(f"Hotbar key {i + 1} pressed!")
                self.handle_hotbar_slot(i)

        # Handle C key (clear path)
        c_current = keys_pressed[pygame.K_c]
        self._key_states["c"] = c_current
        c_just_pressed, _ = self._detect_key_edge("c_action", c_current)
        if c_just_pressed:
            print("Look path cleared with C key!")
            self.handle_clear_path()

    async def animation_loop(self):
        """Main animation loop following asyncio_pygame_example.py pattern"""
        current_time = 0

        while self.running:
            last_time, current_time = current_time, time.time()

            # Handle pygame events on main thread
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        break
                    elif event.key == pygame.K_r and self.mode == "pygame":
                        self.connected = False
                        self.start_websocket_connection()

            if not self.running:
                break

            # Handle input and rendering
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()[0]
            keys_pressed = pygame.key.get_pressed()

            # Process UI inputs through UIManager (same as pygame loop)
            ui_actions = self.ui_manager.process_inputs(mouse_pos, mouse_pressed, keys_pressed)
            keyboard_actions = self.ui_manager.process_keyboard_shortcuts(keys_pressed)
            
            # Handle all actions returned by UIManager
            self._process_ui_actions(ui_actions + keyboard_actions)
            
            # Handle keyboard shortcuts that need edge detection
            self._handle_keyboard_shortcuts_edge_detection(keys_pressed)

            # Draw everything using UIManager
            self.ui_manager.draw()

            # Frame rate limiting (similar to asyncio_pygame_example.py)
            sleep_time = min(1 / FPS - (current_time - last_time - 1 / FPS), 1 / FPS)
            await asyncio.sleep(max(sleep_time, 0.001))

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
