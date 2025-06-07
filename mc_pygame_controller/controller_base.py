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
from typing import Optional, Dict, Any, Callable
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
import argparse


class MinecraftController:

    def __init__(
        self, mode="pygame", chain_args=None, sensitivity=5.0, enable_logging=False
    ):
        self.mode = mode  # "pygame" or "mcp"
        self.sensitivity = sensitivity  # Mouse sensitivity for MCP mode
        self.enable_logging = enable_logging  # Enable logging in pygame mode
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Minecraft Web Client Controller")
        self.clock = pygame.time.Clock()
        self.running = True

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

        # UI Elements
        self.movement_joystick = VirtualJoystick(
            150, WINDOW_HEIGHT - 200, 100
        )  # Larger joystick, adjusted position
        self.keyboard_movement = KeyboardMovement()
        self.camera_area = TouchArea(
            400, 50, 800, 500
        )  # Much larger camera area: 800x500

        # Initialize UI buttons
        self._init_ui_buttons()

        # State tracking for hotbar
        self.current_hotbar_slot = 0  # Currently selected slot (0-8)
        self.last_hotbar_slot = -1  # Track last set slot to avoid duplicate commands

        # WebSocket connection
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self.connection_thread = None
        self.loop = None  # Store the event loop for cross-thread communication

        # State tracking
        self.last_movement = (0.0, 0.0)

        # Action state tracking with timing
        self._action_states = {
            "left_click": {"active": False, "start_time": None},
            "right_click": {"active": False, "start_time": None},
            "jump": {"active": False, "start_time": None},
            "sneak": {"active": False},
            "sprint": {"active": False},
        }

        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Mouse tracking state for camera area
        self.camera_was_touching = False

        # Keyboard shortcut states - using a dictionary for cleaner management
        self._key_states = {
            "ctrl": False,
            "tab": False,
            "z": False,
            "x": False,
            "space": False,
            "q": False,
            "f": False,
            "c": False,
        }

        # Key press tracking for edge detection
        self._last_key_states = {}

        # MCP execution state (mode-independent)
        self.mcp_executor = None

        # Connect LookPathTracker for MCP mode
        if self.mode == "mcp":
            self.look_path_tracker.set_execution_callback(self.execute_mcp_action)

        # Asyncio integration (following asyncio_pygame_example.py pattern)
        self.event_loop = None
        self.event_queue = None
        self.command_queue = None
        self.result_queue = None  # Queue for MCP results

    def _init_ui_buttons(self):
        """Initialize all UI buttons with consistent layout"""
        # Action Buttons
        button_width = 100  # Slightly larger buttons
        button_height = 40
        start_x = 1300  # Moved further right for larger window
        start_y = 600  # Moved down to avoid camera area
        spacing = 50

        self.left_click_btn = Button(
            start_x, start_y, button_width, button_height, "Left Click", RED
        )
        self.right_click_btn = Button(
            start_x + 90, start_y, button_width, button_height, "Right Click", BLUE
        )

        self.jump_btn = Button(
            start_x, start_y + spacing, button_width, button_height, "Jump", GREEN
        )
        self.sneak_btn = ToggleButton(
            start_x + 90,
            start_y + spacing,
            button_width,
            button_height,
            "Sneak",
            ORANGE,
        )

        self.sprint_btn = ToggleButton(
            start_x,
            start_y + spacing * 2,
            button_width,
            button_height,
            "Sprint",
            PURPLE,
        )
        self.inventory_btn = Button(
            start_x + 90,
            start_y + spacing * 2,
            button_width,
            button_height,
            "Inventory",
            GRAY,
        )

        # New buttons for item management
        self.drop_btn = Button(
            start_x,
            start_y + spacing * 3,
            button_width,
            button_height,
            "Drop Item",
            YELLOW,
        )
        self.swap_hands_btn = Button(
            start_x + 90,
            start_y + spacing * 3,
            button_width,
            button_height,
            "Swap Hands",
            (255, 100, 255),  # Pink/magenta
        )

        # Add clear path button
        self.clear_path_btn = Button(
            start_x,
            start_y + spacing * 4,
            button_width * 2 + 10,  # Wider button
            button_height,
            "Clear Look Path",
            (150, 75, 0),  # Brown color
        )

        # Add getBotStatus test button
        self.test_status_btn = Button(
            start_x,
            start_y + spacing * 5,
            button_width * 2 + 10,  # Wider button
            button_height,
            "Test getBotStatus",
            (0, 150, 75),  # Teal color
        )

        # Add save demonstration button (MCP mode only)
        self.save_demo_btn = Button(
            start_x,
            start_y + spacing * 6,
            button_width * 2 + 10,  # Wider button
            button_height,
            "Save Demo Step",
            (150, 0, 150),  # Purple color
        )

        # Hotbar Slot Buttons (1-9)
        self._init_hotbar_buttons()

    def _init_hotbar_buttons(self):
        """Initialize hotbar buttons"""
        hotbar_button_width = 50
        hotbar_button_height = 40
        hotbar_start_x = 50
        hotbar_y = WINDOW_HEIGHT - 60  # Bottom of screen
        hotbar_spacing = 55

        self.hotbar_buttons = []
        for i in range(9):
            slot_number = i + 1  # Display 1-9 for user, but use 0-8 internally
            button = Button(
                hotbar_start_x + i * hotbar_spacing,
                hotbar_y,
                hotbar_button_width,
                hotbar_button_height,
                str(slot_number),
                DARK_GRAY,
                WHITE,
            )
            self.hotbar_buttons.append(button)

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

            if self.mode == "pygame":
                self.send_command_sync(pygame_down_cmd)
            state["active"] = True

        elif not pressed and state["active"]:
            print(f"{action_name.upper()} UP - sending command")

            duration = self._calculate_duration(state["start_time"])
            state["start_time"] = None

            if self.mode == "pygame":
                self.send_command_sync(pygame_up_cmd)
                # Log the action in pygame mode
                mcp_params = (
                    mcp_params_func(duration)
                    if mcp_params_func
                    else {"duration": duration}
                )
                self._log_mcp_command(mcp_tool, mcp_params)
            else:  # mcp mode
                mcp_params = (
                    mcp_params_func(duration)
                    if mcp_params_func
                    else {"duration": duration}
                )
                self.handle_other_commands(mcp_tool, **mcp_params)

            state["active"] = False

    def _handle_toggle_action(
        self, action_name: str, toggled: bool, pygame_control: str, mcp_tool: str
    ):
        """Generic handler for toggle actions (sneak, sprint)"""
        state = self._action_states[action_name]

        if toggled != state["active"]:
            if self.mode == "pygame":
                self.send_command_sync(
                    {"type": "control", "control": pygame_control, "state": toggled}
                )
                self._log_mcp_command(mcp_tool, {"state": toggled})
            else:  # mcp mode
                self.handle_other_commands(mcp_tool, state=toggled)
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
        camera_is_clicking = self.camera_area.is_touching and mouse_pressed
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
            if self.mode == "pygame":
                command = {"type": "move", "x": movement_x, "z": movement_z}
                self.send_command_sync(command)

                # Log movement in pygame mode if logging enabled
                if self.enable_logging and (
                    abs(movement_x) > 0.1 or abs(movement_z) > 0.1
                ):
                    # Calculate duration based on movement magnitude (same as MCP mode)
                    magnitude = (movement_x**2 + movement_z**2) ** 0.5
                    duration = int(magnitude * 2000)  # Scale to reasonable duration
                    self._log_mcp_command("walk", {"duration": duration})

            else:  # mcp mode
                # Convert movement to walk command
                if abs(movement_x) > 0.1 or abs(movement_z) > 0.1:
                    # Calculate duration based on movement magnitude
                    magnitude = (movement_x**2 + movement_z**2) ** 0.5
                    duration = int(magnitude * 2000)  # Scale to reasonable duration
                    self.handle_other_commands(
                        "walk",
                        duration=duration,
                        direction={"x": movement_x, "z": movement_z},
                    )

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
            "left_click",
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
        # Send 'e' key command for inventory
        if self.mode == "pygame":
            command = {"type": "control", "control": "inventory", "state": True}
            self.send_command_sync(command)
            # Immediately release
            command = {"type": "control", "control": "inventory", "state": False}
            self.send_command_sync(command)

            self._log_mcp_command("openInventory", {})

        else:  # mcp mode
            self.handle_other_commands("openInventory")

    def handle_hotbar_slot(self, slot: int):
        """Handle hotbar slot selection (slot should be 0-8)"""
        if 0 <= slot <= 8 and slot != self.last_hotbar_slot:
            print(f"HOTBAR SLOT {slot + 1} - sending command")
            if self.mode == "pygame":
                command = {"type": "setHotbarSlot", "slot": slot}
                self.send_command_sync(command)

                self._log_mcp_command("setHotbarSlot", {"slot": slot})

            else:
                self.handle_other_commands("setHotbarSlot", slot=slot)
            self.current_hotbar_slot = slot
            self.last_hotbar_slot = slot

    def handle_drop_item(self):
        """Handle dropping 1 item from current hotbar slot"""
        print("DROP ITEM - sending command")
        if self.mode == "pygame":
            command = {"type": "dropItem", "amount": 1}
            self.send_command_sync(command)

            self._log_mcp_command("dropItem", {"amount": 1})

        else:  # mcp mode
            self.handle_other_commands("dropItem", amount=1)

    def handle_swap_hands(self):
        """Handle swapping main hand and off-hand items"""
        print("SWAP HANDS - sending command")
        if self.mode == "pygame":
            command = {"type": "swapHands"}
            self.send_command_sync(command)

            self._log_mcp_command("swapHands", {})

        else:  # mcp mode
            self.handle_other_commands("swapHands")

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
        if command_type == "left_click":
            return {
                "tool": "leftClick",
                "parameters": {"duration": params.get("duration", "medium")},
            }
        elif command_type == "right_click":
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
        elif command_type == "openInventory":
            return {
                "tool": "openInventory",
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

    def draw_ui(self):
        self.screen.fill(BLACK)

        # Draw title
        title = self.font.render("Minecraft Web Client Controller", True, WHITE)
        self.screen.blit(title, (10, 10))

        # Draw connection status
        status_color = GREEN if self.connected else RED
        status_text = "Connected" if self.connected else "Disconnected"
        status = self.small_font.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status, (10, 50))

        # Draw mode status
        mode_text = f"Mode: {self.mode.upper()}"
        mode_color = BLUE if self.mode == "mcp" else WHITE
        mode = self.small_font.render(mode_text, True, mode_color)
        self.screen.blit(mode, (10, 75))

        # Draw movement joystick
        self.movement_joystick.draw(self.screen)
        move_label = self.small_font.render("Movement", True, WHITE)
        self.screen.blit(
            move_label,
            (
                self.movement_joystick.center_x - 40,
                self.movement_joystick.center_y + 120,  # Adjusted for larger joystick
            ),
        )

        # Draw camera area
        self.camera_area.draw(self.screen)

        # Draw look path visualization
        self.look_visualization.draw(self.screen, self.look_path_tracker)

        # Add label for look visualization
        look_label = self.small_font.render("Look Path Visualization", True, WHITE)
        self.screen.blit(look_label, (1230, 30))

        # Draw action buttons
        self.left_click_btn.draw(self.screen)
        self.right_click_btn.draw(self.screen)
        self.jump_btn.draw(self.screen)
        self.sneak_btn.draw(self.screen)
        self.sprint_btn.draw(self.screen)
        self.inventory_btn.draw(self.screen)
        self.drop_btn.draw(self.screen)
        self.swap_hands_btn.draw(self.screen)
        self.clear_path_btn.draw(self.screen)
        self.test_status_btn.draw(self.screen)
        self.save_demo_btn.draw(self.screen)

        # Draw hotbar slot buttons
        for i, button in enumerate(self.hotbar_buttons):
            # Highlight the currently selected slot
            if i == self.current_hotbar_slot:
                # Draw a highlight background for the selected slot
                highlight_rect = pygame.Rect(
                    button.rect.x - 3,
                    button.rect.y - 3,
                    button.rect.width + 6,
                    button.rect.height + 6,
                )
                pygame.draw.rect(self.screen, YELLOW, highlight_rect, 3)
            button.draw(self.screen)

        # Draw hotbar label
        hotbar_label = self.small_font.render("Hotbar Slots (1-9)", True, WHITE)
        self.screen.blit(hotbar_label, (50, WINDOW_HEIGHT - 85))

        # Draw instructions
        instructions = [
            "WASD: Move character (keyboard)",
            "Left joystick: Move character (mouse)",
            "Camera area: Look around (drag)",
            "Buttons: Click actions",
            "Ctrl/Z: Left click | Tab/X: Right click",
            "Spacebar: Jump | Q: Drop item | F: Swap hands",
            "1-9: Hotbar slots | C: Clear look path",
            "ESC: Quit | R: Reconnect",
        ]

        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, WHITE)
            self.screen.blit(
                text, (10, WINDOW_HEIGHT - 180 + i * 22)
            )  # Adjusted spacing and position

        # Draw current movement values
        move_text = self.small_font.render(
            f"Movement: X={self.last_movement[0]:.2f}, Z={self.last_movement[1]:.2f}",
            True,
            WHITE,
        )
        self.screen.blit(move_text, (400, 570))  # Moved down to be below camera area

        # Draw keyboard status
        keyboard_status = (
            "WASD Active"
            if self.keyboard_movement.is_any_key_pressed()
            else "WASD Inactive"
        )
        kb_text = self.small_font.render(f"Keyboard: {keyboard_status}", True, WHITE)
        self.screen.blit(kb_text, (400, 590))  # Moved down

        # Draw keyboard shortcut status
        shortcut_status = []
        for key, state in self._key_states.items():
            if state:
                shortcut_status.append(key.upper())

        shortcut_text = "Shortcuts: " + (
            ", ".join(shortcut_status) if shortcut_status else "None"
        )
        shortcut_display = self.small_font.render(shortcut_text, True, WHITE)
        self.screen.blit(shortcut_display, (400, 610))  # Moved down

        # Draw current hotbar slot
        hotbar_status = self.small_font.render(
            f"Hotbar Slot: {self.current_hotbar_slot + 1}/9", True, WHITE
        )
        self.screen.blit(hotbar_status, (400, 630))  # Below shortcuts

        pygame.display.flip()

    def run(self):
        print(f"Starting Minecraft Controller in {self.mode.upper()} mode...")
        if self.mode == "pygame":
            print("Commands will be forwarded to the Minecraft bot")
            print(
                "Make sure the Minecraft web client server is running on localhost:8081"
            )
            # Start WebSocket connection only in pygame mode
            self.start_websocket_connection()
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
                        self.connected = False
                        self.start_websocket_connection()

            # Get mouse state
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()[0]  # Left click

            # Get keyboard state
            keys_pressed = pygame.key.get_pressed()

            # Handle all the pygame input logic...

            # Draw everything
            self.draw_ui()
            self.clock.tick(FPS)

            keyboard_move_x, keyboard_move_y = self.keyboard_movement.handle_keyboard(
                keys_pressed
            )

            # Handle keyboard shortcuts for clicking
            ctrl_current = keys_pressed[pygame.K_LCTRL] or keys_pressed[pygame.K_RCTRL]
            tab_current = keys_pressed[pygame.K_TAB]
            z_current = keys_pressed[pygame.K_z]
            x_current = keys_pressed[pygame.K_x]
            space_current = keys_pressed[pygame.K_SPACE]
            q_current = keys_pressed[pygame.K_q]
            f_current = keys_pressed[pygame.K_f]

            # Store current states for UI display
            self._key_states["ctrl"] = ctrl_current
            self._key_states["tab"] = tab_current
            self._key_states["z"] = z_current
            self._key_states["x"] = x_current
            self._key_states["space"] = space_current
            self._key_states["q"] = q_current
            self._key_states["f"] = f_current

            # Combine all left click inputs
            left_click_input = ctrl_current or z_current
            # Combine all right click inputs
            right_click_input = tab_current or x_current

            # Handle keyboard shortcuts using the refactored method
            self._handle_keyboard_shortcuts(q_current, f_current, keys_pressed)

            # Handle movement joystick
            joystick_move_x, joystick_move_y = self.movement_joystick.handle_mouse(
                mouse_pos, mouse_pressed
            )

            # Use joystick input if it's not at the center, otherwise use keyboard
            if abs(joystick_move_x) < 0.1 and abs(joystick_move_y) < 0.1:
                self.handle_movement(keyboard_move_x, keyboard_move_y)
            else:
                self.handle_movement(joystick_move_x, joystick_move_y)

                # Handle camera look area
            delta_x, delta_y = self.camera_area.handle_mouse(mouse_pos, mouse_pressed)

            # Track mouse click-and-drag state changes for camera look
            self._handle_camera_drag_state(mouse_pressed)

            self.handle_camera_look(delta_x, delta_y)

            # Handle action buttons
            if self.left_click_btn.handle_mouse(mouse_pos, mouse_pressed):
                pass  # Handle on hold/release
            self.handle_left_click(self.left_click_btn.is_pressed or left_click_input)

            if self.right_click_btn.handle_mouse(mouse_pos, mouse_pressed):
                pass  # Handle on hold/release
            self.handle_right_click(
                self.right_click_btn.is_pressed or right_click_input
            )

            # Handle jump button - check both press and release
            self.jump_btn.handle_mouse(mouse_pos, mouse_pressed)
            self.handle_jump(self.jump_btn.is_pressed or space_current)

            # Handle toggle buttons - only send command when toggled
            if self.sneak_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_sneak(self.sneak_btn.is_toggled)

            if self.sprint_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_sprint(self.sprint_btn.is_toggled)

            if self.inventory_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_inventory()

            # Handle new item management buttons
            if self.drop_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_drop_item()

            if self.swap_hands_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_swap_hands()

            # Handle clear path button
            if self.clear_path_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_clear_path()

            # Handle test status button
            if self.test_status_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_test_status()

            # Handle save demonstration button (MCP mode only)
            if self.save_demo_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_save_demonstration()

            # Handle hotbar slot buttons
            for i, button in enumerate(self.hotbar_buttons):
                if button.handle_mouse(mouse_pos, mouse_pressed):
                    self.handle_hotbar_slot(i)  # i is already 0-8

            # Hotbar and C key handling is now done in _handle_keyboard_shortcuts

        # MCP tasks are now handled in animation_loop

    def _handle_all_inputs(self, mouse_pos, mouse_pressed, keys_pressed):
        """Handle all input processing (extracted from main loop)"""
        # Handle keyboard shortcuts
        ctrl_current = keys_pressed[pygame.K_LCTRL] or keys_pressed[pygame.K_RCTRL]
        tab_current = keys_pressed[pygame.K_TAB]
        z_current = keys_pressed[pygame.K_z]
        x_current = keys_pressed[pygame.K_x]
        space_current = keys_pressed[pygame.K_SPACE]
        q_current = keys_pressed[pygame.K_q]
        f_current = keys_pressed[pygame.K_f]

        # Store keyboard shortcut states for UI display
        self._key_states["ctrl"] = ctrl_current
        self._key_states["tab"] = tab_current
        self._key_states["z"] = z_current
        self._key_states["x"] = x_current
        self._key_states["space"] = space_current
        self._key_states["q"] = q_current
        self._key_states["f"] = f_current

        # Handle clicks
        left_click_input = ctrl_current or z_current
        right_click_input = tab_current or x_current

        # Handle action buttons
        self.left_click_btn.handle_mouse(mouse_pos, mouse_pressed)
        self.handle_left_click(self.left_click_btn.is_pressed or left_click_input)

        self.right_click_btn.handle_mouse(mouse_pos, mouse_pressed)
        self.handle_right_click(self.right_click_btn.is_pressed or right_click_input)

        self.jump_btn.handle_mouse(mouse_pos, mouse_pressed)
        self.handle_jump(self.jump_btn.is_pressed or space_current)

        # Handle toggle buttons
        if self.sneak_btn.handle_mouse(mouse_pos, mouse_pressed):
            self.handle_sneak(self.sneak_btn.is_toggled)
        if self.sprint_btn.handle_mouse(mouse_pos, mouse_pressed):
            self.handle_sprint(self.sprint_btn.is_toggled)

        # Handle other buttons
        if self.inventory_btn.handle_mouse(mouse_pos, mouse_pressed):
            self.handle_inventory()
        if self.drop_btn.handle_mouse(mouse_pos, mouse_pressed):
            self.handle_drop_item()
        if self.swap_hands_btn.handle_mouse(mouse_pos, mouse_pressed):
            self.handle_swap_hands()
        if self.clear_path_btn.handle_mouse(mouse_pos, mouse_pressed):
            self.handle_clear_path()

        # Handle test status button (MCP mode only)
        if self.test_status_btn.handle_mouse(mouse_pos, mouse_pressed):
            self.handle_test_status()

        # Handle save demonstration button (MCP mode only)
        if self.save_demo_btn.handle_mouse(mouse_pos, mouse_pressed):
            self.handle_save_demonstration()

        # Handle hotbar buttons
        for i, button in enumerate(self.hotbar_buttons):
            if button.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_hotbar_slot(i)

        # Handle keyboard shortcuts for various actions
        self._handle_keyboard_shortcuts(q_current, f_current, keys_pressed)

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

            keyboard_move_x, keyboard_move_y = self.keyboard_movement.handle_keyboard(
                keys_pressed
            )

            # Handle movement
            joystick_move_x, joystick_move_y = self.movement_joystick.handle_mouse(
                mouse_pos, mouse_pressed
            )
            if abs(joystick_move_x) < 0.1 and abs(joystick_move_y) < 0.1:
                self.handle_movement(keyboard_move_x, keyboard_move_y)
            else:
                self.handle_movement(joystick_move_x, joystick_move_y)

            # Handle camera look
            delta_x, delta_y = self.camera_area.handle_mouse(mouse_pos, mouse_pressed)

            # Track mouse click-and-drag state changes for camera look
            self._handle_camera_drag_state(mouse_pressed)

            self.handle_camera_look(delta_x, delta_y)

            # Handle all buttons and controls
            self._handle_all_inputs(mouse_pos, mouse_pressed, keys_pressed)

            # Draw everything
            self.draw_ui()

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
