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
            "left_click": self.handle_left_click,
            "right_click": self.handle_right_click,
            "left_click_keyboard": self._handle_left_click_keyboard,
            "right_click_keyboard": self._handle_right_click_keyboard,
            "jump": self._handle_jump_action, # This is a helper that calls self.handle_jump
            "jump_keyboard": self._handle_jump_action, # Same helper
            "sneak_toggled": self.handle_sneak,
            "sprint_toggled": self.handle_sprint,
            "inventory_pressed": lambda _: self.handle_inventory(),
            "drop_item_pressed": lambda _: self.handle_drop_item(),
            "swap_hands_pressed": lambda _: self.handle_swap_hands(),
            "clear_path_pressed": lambda _: self.handle_clear_path(),
            "test_status_pressed": lambda _: self.controller.handle_test_status(), # Stays on controller
            "save_demo_pressed": lambda _: self.controller.handle_save_demonstration(), # Stays on controller
            "hotbar_slot_pressed": self.handle_hotbar_slot,
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
        self.handle_left_click(combined_state)

    def _handle_right_click_keyboard(self, keyboard_state: bool):
        """Handle right click keyboard input, combining with button state."""
        # Get button state from UI manager
        button_pressed = getattr(self.controller.ui_manager, "right_click_btn", None)
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

    def handle_inventory(self):
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

    def _log_mcp_command(self, tool: str, parameters: Dict[str, Any]):
        """Log MCP command if logging is enabled"""
        # Access enable_logging through self.state, which is ControllerState
        if self.state.enable_logging:
            mcp_command = {"tool": tool, "parameters": parameters}
            print(f"LOGGED: {mcp_command}")
