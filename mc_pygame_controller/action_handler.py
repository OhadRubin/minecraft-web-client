import time
from typing import Dict, Any, Callable, List, Tuple, Optional
import pygame # For key constants

# Forward references for type hinting
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .controller_state import ControllerState
    from .mode_strategy import ModeStrategy
    from .controller_base import MinecraftController


class ActionHandler:
    def __init__(
        self,
        controller_state: "ControllerState",
        mode_strategy: "ModeStrategy",
        controller: "MinecraftController",
    ):
        self.state: "ControllerState" = controller_state
        self.strategy: "ModeStrategy" = mode_strategy
        self.controller: "MinecraftController" = controller
        self._last_jump_state: bool = False

        self._action_handlers: Dict[str, Callable[[Any], None]] = {
            "movement": lambda v: self.handle_movement(v[0], v[1]) if v else None,
            "camera_look": lambda v: self.handle_camera_look(v[0], v[1]) if v else None,
            # camera_drag_state will be handled by CameraDragHandler in a later refactoring,
            # but for now, it needs to call a method on the controller.
            "camera_drag_state": lambda v: (
                self.controller._handle_camera_drag_state(v[0]) if v else None
            ),
            "left_click": lambda v: self.handle_left_click(
                v, self._detect_inventory_mode()
            ),
            "right_click": lambda v: self.handle_right_click(
                v, self._detect_inventory_mode()
            ),
            "left_click_keyboard": self._handle_left_click_keyboard,
            "right_click_keyboard": self._handle_right_click_keyboard,
            "jump": self._handle_jump_action,  # This is a helper that calls self.handle_jump
            "jump_keyboard": self._handle_jump_action,  # Same helper
            "sneak_toggled": self.handle_sneak,
            "sprint_toggled": self.handle_sprint,
            "inventory_pressed": lambda _: self.handle_inventory(),
            "drop_item_pressed": lambda _: self.handle_drop_item(),
            "swap_hands_pressed": lambda _: self.handle_swap_hands(),
            "clear_path_pressed": lambda _: self.handle_clear_path(),
            "test_status_pressed": lambda _: self.controller.handle_test_status(),  # Stays on controller
            "save_demo_pressed": lambda _: self.controller.handle_save_demonstration(),  # Stays on controller
            "context_debug_pressed": lambda _: self.handle_context_debug(),  # Debug context detection
            "hotbar_slot_pressed": self.handle_hotbar_slot,
            # Data collection actions
            "start_data_collection_session": self.handle_start_data_collection_session,
            "save_data_collection_session": self.handle_save_data_collection_session,
            "cancel_data_collection_session": self.handle_cancel_data_collection_session,
            "task_description_entered": self.handle_task_description_entered,
        }

    def _detect_inventory_mode(self) -> bool:
        """Detect if we should use inventory mode for clicks based on current context."""
        return self.state.inventory_open or self.state.current_context == "inventory"

    def _detect_current_context(self) -> str:
        """
        Detect the current interaction context.
        This is a simplified version - in a full implementation, this could
        check game state, UI elements, etc. like the WebSocket handlers do.
        """
        # For now, rely on manual tracking via inventory toggles
        # In the future, this could be enhanced with more sophisticated detection
        return self.state.current_context

    def set_context(self, context: str) -> None:
        """
        Manually set the interaction context (useful for debugging).
        Args:
            context: Either "world" or "inventory"
        """
        if context not in ["world", "inventory"]:
            if self.state.enable_logging:
                print(
                    f"Warning: Invalid context '{context}'. Must be 'world' or 'inventory'"
                )
            return

        previous_context = self.state.current_context
        self.state.current_context = context
        self.state.inventory_open = context == "inventory"

        if self.state.enable_logging:
            print(f"Context manually changed from '{previous_context}' to '{context}'")

    def get_context_info(self) -> Dict[str, Any]:
        """Get current context information for debugging."""
        return {
            "current_context": self.state.current_context,
            "inventory_open": self.state.inventory_open,
            "last_inventory_toggle": self.state.last_inventory_toggle_time,
            "time_since_toggle": (
                time.time() - self.state.last_inventory_toggle_time
                if self.state.last_inventory_toggle_time > 0
                else 0
            ),
        }

    # Helper methods for action dispatch dictionary
    def _handle_jump_action(self, state: bool):
        """Handle jump action, managing combined state from button and keyboard."""
        # Removed: if not hasattr(self, '_last_jump_state'): self._last_jump_state = False
        # _last_jump_state is now initialized in __init__

        if state != self._last_jump_state:
            self.handle_jump(state)
            self._last_jump_state = state

    def _handle_left_click_keyboard(self, keyboard_state: bool):
        """Handle left click keyboard input, combining with button state."""
        # Get button state from UI manager
        button_pressed = getattr(self.controller.ui_manager, "left_click_btn", None)
        button_state = button_pressed.is_pressed if button_pressed else False

        # Combine keyboard and button states (OR logic)
        combined_state = keyboard_state or button_state
        inventory_mode = self._detect_inventory_mode()
        self.handle_left_click(combined_state, inventory_mode)

    def _handle_right_click_keyboard(self, keyboard_state: bool):
        """Handle right click keyboard input, combining with button state."""
        # Get button state from UI manager
        button_pressed = getattr(self.controller.ui_manager, "right_click_btn", None)
        button_state = button_pressed.is_pressed if button_pressed else False

        # Combine keyboard and button states (OR logic)
        combined_state = keyboard_state or button_state
        inventory_mode = self._detect_inventory_mode()
        self.handle_right_click(combined_state, inventory_mode)

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
            if self.state.enable_logging:
                print(f"{action_name.upper()} DOWN - sending command")
            state["start_time"] = time.time()
            state["active"] = True

        elif not pressed and state["active"]:
            if self.state.enable_logging:
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

    def handle_movement(self, x: float, y: float):
        # Convert joystick coordinates to movement commands
        # y maps directly to z: joystick up (negative y) = forward (negative z)
        movement_x = x
        movement_z = y  # Remove the inversion - up should be forward (negative z)

        # Only send if movement changed significantly
        if (
            abs(movement_x - self.state.last_movement[0]) > 0.1
            or abs(movement_z - self.state.last_movement[1]) > 0.1
        ):
            self.strategy.handle_movement(movement_x, movement_z)
            self.state.last_movement = (movement_x, movement_z)

    def handle_camera_look(self, delta_x: int, delta_y: int):
        if delta_x != 0 or delta_y != 0:
            # Scale the movement for better sensitivity
            scaled_x = delta_x * 2
            scaled_y = delta_y * 2

            # Add to path tracker
            self.controller.look_path_tracker.add_movement(scaled_x, scaled_y)

            # Only send WebSocket command in pygame mode
            # In MCP mode, LookPathTracker will handle conversion via callback
            if self.state.mode == "pygame":
                command = {"type": "look", "movementX": scaled_x, "movementY": scaled_y}
                self.controller.send_command_sync(command)

    def handle_left_click(self, pressed: bool, inventory_mode: bool = False):
        """
        Handle left click using context-sensitive commands.

        Args:
            pressed: Whether the button is currently pressed
            inventory_mode: Whether to use inventory interaction mode
                          - True: Uses documentMouseEvent (for UI/inventory interactions)
                          - False: Uses standard leftDown/leftUp (for game world interactions)

        The inventory_mode is automatically detected based on:
        - Current inventory state (self.state.inventory_open)
        - Current interaction context (self.state.current_context)
        """
        if not inventory_mode:
            # Inventory mode: Use documentMouseEvent for UI interactions
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
        else:
            # World mode: Use standard game click commands
            self._handle_timed_action(
                "left_click",
                pressed,
                {"type": "leftDown"},
                {"type": "leftUp"},
                "leftClick",
            )

    def handle_right_click(self, pressed: bool, inventory_mode: bool = False):
        """
        Handle right click using context-sensitive commands.

        Args:
            pressed: Whether the button is currently pressed
            inventory_mode: Whether to use inventory interaction mode
                          - True: Uses documentMouseEvent (for UI/inventory interactions)
                          - False: Uses standard rightDown/rightUp (for game world interactions)

        The inventory_mode is automatically detected based on:
        - Current inventory state (self.state.inventory_open)
        - Current interaction context (self.state.current_context)
        """
        if not inventory_mode:
            # Inventory mode: Use documentMouseEvent for UI interactions
            self._handle_timed_action(
                "right_click",
                pressed,
                {
                    "type": "documentMouseEvent",
                    "button": 2,
                    "action": "down",
                    "updateMouse": True,
                },
                {
                    "type": "documentMouseEvent",
                    "button": 2,
                    "action": "up",
                    "updateMouse": False,
                },
                "rightClick",
            )
        else:
            # World mode: Use standard game click commands
            self._handle_timed_action(
                "right_click",
                pressed,
                {"type": "rightDown"},
                {"type": "rightUp"},
                "rightClick",
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

    def handle_inventory(self):
        # Toggle inventory state tracking
        self.state.inventory_open = not self.state.inventory_open
        self.state.current_context = (
            "inventory" if self.state.inventory_open else "world"
        )
        self.state.last_inventory_toggle_time = time.time()

        if self.state.enable_logging:
            print(
                f"INVENTORY {'OPENED' if self.state.inventory_open else 'CLOSED'} - context: {self.state.current_context}"
            )

        # Send inventory command (toggle)
        self.strategy.handle_simple_action(
            "toggleInventory",
            pygame_cmd={"type": "inventory"}
        )

    def handle_hotbar_slot(self, slot: int):
        """Handle hotbar slot selection (slot should be 0-8)"""
        if 0 <= slot <= 8 and slot != self.state.last_hotbar_slot:
            if self.state.enable_logging:
                print(f"HOTBAR SLOT {slot + 1} - sending command")
            self.strategy.handle_simple_action(
                "setHotbarSlot",
                pygame_cmd={"type": "setHotbarSlot", "slot": slot},
                slot=slot
            )
            self.state.current_hotbar_slot = slot
            self.state.last_hotbar_slot = slot

    def handle_drop_item(self):
        """Handle dropping 1 item from current hotbar slot"""
        if self.state.enable_logging:
            print("DROP ITEM - sending command")
        self.strategy.handle_simple_action(
            "dropItem",
            pygame_cmd={"type": "dropItem", "amount": 1},
            amount=1
        )

    def handle_swap_hands(self):
        """Handle swapping main hand and off-hand items"""
        if self.state.enable_logging:
            print("SWAP HANDS - sending command")
        self.strategy.handle_simple_action(
            "swapHands",
            pygame_cmd={"type": "swapHands"}
        )

    def handle_clear_path(self):
        """Handle clearing the look path"""
        self.controller.look_path_tracker.clear_history()
        if self.state.enable_logging:
            print("Look path cleared!")

    def process_actions(self, actions: List[Tuple[str, Any]]) -> None:
        """Process actions returned by UIManager using dispatch dictionary."""
        for action_name, value in actions:
            handler = self._action_handlers.get(action_name)
            if handler:
                handler(value)
            else:
                # Unknown action - log warning but don't crash
                if action_name:  # Don't warn for empty action names
                    # TODO: Consider a more robust logging mechanism
                    if self.state.enable_logging:
                        print(f"Warning: No handler for action '{action_name}'")

    def process_edge_detections(self, keys_pressed: Any) -> None: # pygame.key.ScancodeWrapper type for keys_pressed
        """Handle keyboard shortcuts that require edge detection."""
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
            just_pressed, _ = self._detect_key_edge( # We only care about just_pressed here
                key_name, keys_pressed[key]
            )

            if just_pressed:
                self.handle_hotbar_slot(i)

        # Handle drop item (Q key)
        just_pressed, _ = self._detect_key_edge(
            "drop_item", keys_pressed[pygame.K_q]
        )
        if just_pressed:
            self.handle_drop_item()

        # Handle swap hands (F key)
        just_pressed, _ = self._detect_key_edge(
            "swap_hands", keys_pressed[pygame.K_f]
        )
        if just_pressed:
            self.handle_swap_hands()

        # Handle inventory (E key)
        just_pressed, _ = self._detect_key_edge(
            "inventory", keys_pressed[pygame.K_e]
        )
        if just_pressed:
            self.handle_inventory()

        # Handle context debug (G key)
        just_pressed, _ = self._detect_key_edge(
            "context_debug", keys_pressed[pygame.K_g]
        )
        if just_pressed:
            self.handle_context_debug()

    def _log_mcp_command(self, tool: str, parameters: Dict[str, Any]):
        """Log MCP command if logging is enabled"""
        # Access enable_logging through self.state, which is ControllerState
        if self.state.enable_logging:
            mcp_command = {"tool": tool, "parameters": parameters}
            print(f"LOGGED: {mcp_command}")

    def handle_start_data_collection_session(self, value=None):
        """Handle starting a new data collection session (F5 key)"""
        if not self.state.data_collection_enabled:
            print("⚠️ Data collection not enabled. Use --data-collection flag.")
            return

        if self.controller.data_collection_session_active:
            print("⚠️ Data collection session already active. Save or cancel first.")
            return

        # Get task description from embedded text input field
        task_description = self.controller.ui_manager.task_input_field.value.strip()

        if not task_description:
            task_description = "Spatial reasoning task"
            # Set default in the text field so user can see what was used
            self.controller.ui_manager.task_input_field.value = task_description

        # Start session via strategy
        if hasattr(self.strategy, "start_data_collection_session"):
            session_id = self.strategy.start_data_collection_session(task_description)
            if session_id:
                self.controller.data_collection_session_active = True
                self.controller.current_task_description = task_description
                print(f"🎬 Started data collection session: {session_id}")
                print(
                    "💡 Perform your spatial reasoning actions. Press F6 to save when done."
                )
            else:
                print("❌ Failed to start data collection session")
        else:
            print("⚠️ Data collection not supported in current mode")

    def handle_save_data_collection_session(self, value=None):
        """Handle saving the current data collection session (F6 key)"""
        if not self.state.data_collection_enabled:
            print("⚠️ Data collection not enabled. Use --data-collection flag.")
            return

        if not self.controller.data_collection_session_active:
            print("⚠️ No active data collection session. Press F5 to start one.")
            return

        # Save session via strategy
        if hasattr(self.strategy, "save_data_collection_session"):
            filepath = self.strategy.save_data_collection_session()
            if filepath:
                print(f"💾 Data collection session saved to: {filepath}")
                self.controller.data_collection_session_active = False
                self.controller.current_task_description = ""
                print("✅ Ready to start a new session with F5")
            else:
                print("❌ Failed to save data collection session")
        else:
            print("⚠️ Data collection not supported in current mode")

    def handle_cancel_data_collection_session(self, value=None):
        """Handle canceling the current data collection session (F7 key)"""
        if not self.state.data_collection_enabled:
            print("⚠️ Data collection not enabled. Use --data-collection flag.")
            return

        if not self.controller.data_collection_session_active:
            print("⚠️ No active data collection session to cancel.")
            return

        # Cancel session via strategy
        if hasattr(self.strategy, "cancel_data_collection_session"):
            self.strategy.cancel_data_collection_session()
            self.controller.data_collection_session_active = False
            self.controller.current_task_description = ""
            print("❌ Data collection session cancelled")
            print("💡 Press F5 to start a new session")
        else:
            print("⚠️ Data collection not supported in current mode")

    def handle_task_description_entered(self, task_description: str):
        """Handle when user enters a task description in the text field"""
        if not self.state.data_collection_enabled:
            return

        task_description = task_description.strip()
        if task_description:
            print(f"📝 Task description updated: '{task_description}'")
            print("💡 Press F5 to start data collection with this task")
        else:
            print("⚠️ Empty task description entered")

    def handle_context_debug(self):
        """Handle context debug action"""
        context_info = self.get_context_info()
        print("🔍 Current context debug information:")
        for key, value in context_info.items():
            print(f"  {key}: {value}")

        # Also show what mode clicks will use
        inventory_mode = self._detect_inventory_mode()
        print(f"  clicks_will_use_inventory_mode: {inventory_mode}")

        if inventory_mode:
            print("  ➡️ Next clicks will use documentMouseEvent (inventory mode)")
        else:
            print("  ➡️ Next clicks will use standard game clicks (world mode)")
