"""
UI Manager for MinecraftController

Handles all UI elements, drawing, and input processing, separating these concerns
from the main controller logic following the Single Responsibility Principle.
"""

import pygame
from typing import List, Tuple, Any, Dict
from .constants import *
from .ui_elements import (
    Button,
    ToggleButton,
    VirtualJoystick,
    KeyboardMovement,
    TouchArea,
)
from .look_path import LookPathVisualizationArea
from .controller_state import ControllerState
from .ui_layout_config import (
    UI_LAYOUT_CONFIG,
    calculate_button_position,
    calculate_button_size,
    get_font_size
)


class UIManager:
    """Manages all UI elements, drawing, and input processing for the controller."""

    def __init__(self, screen: pygame.Surface, state: ControllerState, look_path_tracker, look_visualization: LookPathVisualizationArea):
        """Initialize UI manager with screen and state references."""
        self.screen = screen
        self.state = state
        self.look_path_tracker = look_path_tracker
        self.look_visualization = look_visualization
        self.layout_config = UI_LAYOUT_CONFIG

        # Initialize fonts based on configuration
        self.font = pygame.font.Font(None, get_font_size("title"))
        self.small_font = pygame.font.Font(None, get_font_size("small"))

        # Dictionary to store all UI buttons for easy access
        self.buttons: Dict[str, Any] = {}

        # Edge detection state for keyboard shortcuts
        self._last_key_states: Dict[str, bool] = {}

        # Initialize UI elements
        self._init_ui_elements()

    def _detect_key_edge(self, key_name: str, current_state: bool) -> tuple[bool, bool]:
        """Detect key press/release edges. Returns (just_pressed, just_released)"""
        last_state = self._last_key_states.get(key_name, False)
        self._last_key_states[key_name] = current_state

        just_pressed = current_state and not last_state
        just_released = not current_state and last_state

        return just_pressed, just_released

    def _init_ui_elements(self):
        """Initialize all UI elements using configuration."""
        # Core UI elements from configuration
        joystick_config = self.layout_config["core_elements"]["movement_joystick"]
        self.movement_joystick = VirtualJoystick(
            joystick_config["x"], 
            joystick_config["y"], 
            joystick_config["radius"]
        )

        self.keyboard_movement = KeyboardMovement()

        camera_config = self.layout_config["core_elements"]["camera_area"]
        self.camera_area = TouchArea(
            camera_config["x"], 
            camera_config["y"], 
            camera_config["width"], 
            camera_config["height"]
        )

        # Initialize buttons from configuration
        self._init_ui_buttons_from_config()

        # Initialize hotbar buttons from configuration
        self._init_hotbar_buttons_from_config()

    def _init_ui_buttons_from_config(self):
        """Initialize UI buttons from layout configuration."""
        button_layout = self.layout_config["action_buttons"]
        base_config = button_layout["base_config"]

        # Create buttons from configuration
        for button_config in button_layout["buttons"]:
            # Calculate position and size
            x, y = calculate_button_position(button_config, base_config)
            width, height = calculate_button_size(button_config, base_config)

            # Create button instance
            button_class = button_config["class"]
            button = button_class(
                x, y, width, height,
                button_config["text"],
                button_config["color"]
            )

            # Store button with its name for easy access
            button_name = button_config["name"]
            self.buttons[button_name] = button
            setattr(self, button_name, button)  # Also set as attribute for backward compatibility

    def _init_hotbar_buttons_from_config(self):
        """Initialize hotbar buttons from configuration."""
        hotbar_config = self.layout_config["hotbar"]

        self.hotbar_buttons = []
        for i in range(hotbar_config["count"]):
            slot_number = i + 1  # Display 1-9 for user, but use 0-8 internally
            x = hotbar_config["start_x"] + (i * hotbar_config["spacing"])
            y = hotbar_config["y"]

            button = Button(
                x, y,
                hotbar_config["button_width"],
                hotbar_config["button_height"],
                str(slot_number),
                DARK_GRAY,
                WHITE,
            )
            self.hotbar_buttons.append(button)

    def process_inputs(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, keys_pressed) -> List[Tuple[str, Any]]:
        """
        Process all UI inputs and return a list of actions to be handled by the controller.
        
        Returns list of (action_name, value) tuples representing user intentions.
        """
        actions = []

        # Handle keyboard movement
        keyboard_move_x, keyboard_move_y = self.keyboard_movement.handle_keyboard(keys_pressed)

        # Handle movement joystick
        joystick_move_x, joystick_move_y = self.movement_joystick.handle_mouse(mouse_pos, mouse_pressed)

        # Use joystick input if it's not at the center, otherwise use keyboard
        if abs(joystick_move_x) < 0.1 and abs(joystick_move_y) < 0.1:
            if abs(keyboard_move_x) > 0.1 or abs(keyboard_move_y) > 0.1:
                actions.append(("movement", (keyboard_move_x, keyboard_move_y)))
        else:
            actions.append(("movement", (joystick_move_x, joystick_move_y)))

        # Handle camera area
        delta_x, delta_y = self.camera_area.handle_mouse(mouse_pos, mouse_pressed)
        if delta_x != 0 or delta_y != 0:
            actions.append(("camera_look", (delta_x, delta_y)))

        # Handle action buttons
        if self.left_click_btn.handle_mouse(mouse_pos, mouse_pressed):
            pass  # Handle on hold/release
        actions.append(("left_click", self.left_click_btn.is_pressed))

        if self.right_click_btn.handle_mouse(mouse_pos, mouse_pressed):
            pass  # Handle on hold/release
        actions.append(("right_click", self.right_click_btn.is_pressed))

        # Handle jump button
        self.jump_btn.handle_mouse(mouse_pos, mouse_pressed)
        actions.append(("jump", self.jump_btn.is_pressed))

        # Handle toggle buttons
        if self.sneak_btn.handle_mouse(mouse_pos, mouse_pressed):
            actions.append(("sneak_toggled", self.sneak_btn.is_toggled))

        if self.sprint_btn.handle_mouse(mouse_pos, mouse_pressed):
            actions.append(("sprint_toggled", self.sprint_btn.is_toggled))

        if self.inventory_btn.handle_mouse(mouse_pos, mouse_pressed):
            actions.append(("inventory_pressed", None))

        # Handle item management buttons
        if self.drop_btn.handle_mouse(mouse_pos, mouse_pressed):
            actions.append(("drop_item_pressed", None))

        if self.swap_hands_btn.handle_mouse(mouse_pos, mouse_pressed):
            actions.append(("swap_hands_pressed", None))

        # Handle utility buttons
        if self.clear_path_btn.handle_mouse(mouse_pos, mouse_pressed):
            actions.append(("clear_path_pressed", None))

        if self.test_status_btn.handle_mouse(mouse_pos, mouse_pressed):
            actions.append(("test_status_pressed", None))

        if self.save_demo_btn.handle_mouse(mouse_pos, mouse_pressed):
            actions.append(("save_demo_pressed", None))

        # Handle hotbar buttons
        for i, button in enumerate(self.hotbar_buttons):
            if button.handle_mouse(mouse_pos, mouse_pressed):
                actions.append(("hotbar_slot_pressed", i))

        return actions

    def process_keyboard_shortcuts(self, keys_pressed) -> List[Tuple[str, Any]]:
        """Process keyboard shortcuts and return actions."""
        actions = []

        # Handle keyboard shortcuts for clicking
        ctrl_current = keys_pressed[pygame.K_LCTRL] or keys_pressed[pygame.K_RCTRL]
        tab_current = keys_pressed[pygame.K_TAB]
        z_current = keys_pressed[pygame.K_z]
        x_current = keys_pressed[pygame.K_x]
        space_current = keys_pressed[pygame.K_SPACE]
        q_current = keys_pressed[pygame.K_q]
        f_current = keys_pressed[pygame.K_f]
        c_current = keys_pressed[pygame.K_c]

        # Store current states for UI display
        self.state.key_states.update({
            "ctrl": ctrl_current,
            "tab": tab_current,
            "z": z_current,
            "x": x_current,
            "space": space_current,
            "q": q_current,
            "f": f_current,
            "c": c_current,
        })

        # Combine all left click inputs (keyboard shortcuts)
        keyboard_left_click = ctrl_current or z_current
        # Combine all right click inputs (keyboard shortcuts)
        keyboard_right_click = tab_current or x_current

        # Add keyboard click actions (will be combined with button states in process_inputs)
        actions.append(("left_click_keyboard", keyboard_left_click))
        actions.append(("right_click_keyboard", keyboard_right_click))
        actions.append(("jump_keyboard", space_current))

        # Handle edge detection for one-time actions
        # Q key (drop item)
        q_just_pressed, _ = self._detect_key_edge("q_action", q_current)
        if q_just_pressed:
            actions.append(("drop_item_pressed", None))

        # F key (swap hands)
        f_just_pressed, _ = self._detect_key_edge("f_action", f_current)
        if f_just_pressed:
            actions.append(("swap_hands_pressed", None))

        # C key (clear path)
        c_just_pressed, _ = self._detect_key_edge("c_action", c_current)
        if c_just_pressed:
            actions.append(("clear_path_pressed", None))

        # Hotbar keys (1-9)
        hotbar_keys = [
            pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
            pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9,
        ]
        for i, key in enumerate(hotbar_keys):
            key_current = keys_pressed[key]
            key_just_pressed, _ = self._detect_key_edge(f"hotbar_{i}", key_current)
            if key_just_pressed:
                actions.append(("hotbar_slot_pressed", i))

        return actions

    def draw(self):
        """Draw all UI elements to the screen using configuration."""
        self.screen.fill(BLACK)

        # Draw status displays using configuration
        self._draw_status_displays()

        # Draw core UI elements
        self._draw_core_elements()

        # Draw all action buttons
        self._draw_action_buttons()

        # Draw hotbar
        self._draw_hotbar()

        # Draw instructions
        self._draw_instructions()

        pygame.display.flip()

    def _draw_status_displays(self):
        """Draw status information using configuration."""
        status_config = self.layout_config["status_display"]

        # Draw title
        title_config = status_config["title"]
        title = self.font.render(title_config["text"], True, title_config["color"])
        self.screen.blit(title, (title_config["x"], title_config["y"]))

        # Draw connection status
        conn_config = status_config["connection_status"]
        status_color = conn_config["color_connected"] if self.state.connected else conn_config["color_disconnected"]
        status_text = "Connected" if self.state.connected else "Disconnected"
        status = self.small_font.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status, (conn_config["x"], conn_config["y"]))

        # Draw mode status
        mode_config = status_config["mode_status"]
        mode_text = f"Mode: {self.state.mode.upper()}"
        mode_color = mode_config["color_mcp"] if self.state.mode == "mcp" else mode_config["color_pygame"]
        mode = self.small_font.render(mode_text, True, mode_color)
        self.screen.blit(mode, (mode_config["x"], mode_config["y"]))

        # Draw movement values
        move_config = status_config["movement_info"]
        move_text = self.small_font.render(
            f"Movement: X={self.state.last_movement[0]:.2f}, Z={self.state.last_movement[1]:.2f}",
            True, move_config["color"]
        )
        self.screen.blit(move_text, (move_config["x"], move_config["y"]))

        # Draw keyboard status
        kb_config = status_config["keyboard_status"]
        keyboard_status = "WASD Active" if self.keyboard_movement.is_any_key_pressed() else "WASD Inactive"
        kb_text = self.small_font.render(f"Keyboard: {keyboard_status}", True, kb_config["color"])
        self.screen.blit(kb_text, (kb_config["x"], kb_config["y"]))

        # Draw keyboard shortcut status
        shortcut_config = status_config["shortcuts_status"]
        shortcut_status = [key.upper() for key, state in self.state.key_states.items() if state]
        shortcut_text = "Shortcuts: " + (", ".join(shortcut_status) if shortcut_status else "None")
        shortcut_display = self.small_font.render(shortcut_text, True, shortcut_config["color"])
        self.screen.blit(shortcut_display, (shortcut_config["x"], shortcut_config["y"]))

        # Draw current hotbar slot
        hotbar_config = status_config["hotbar_status"]
        hotbar_status = self.small_font.render(
            f"Hotbar Slot: {self.state.current_hotbar_slot + 1}/9", True, hotbar_config["color"]
        )
        self.screen.blit(hotbar_status, (hotbar_config["x"], hotbar_config["y"]))

    def _draw_core_elements(self):
        """Draw core UI elements using configuration."""
        # Draw movement joystick
        self.movement_joystick.draw(self.screen)

        # Draw joystick label
        joystick_config = self.layout_config["core_elements"]["movement_joystick"]
        label_config = joystick_config["label"]
        move_label = self.small_font.render(label_config["text"], True, WHITE)
        self.screen.blit(move_label, (
            self.movement_joystick.center_x + label_config["offset_x"],
            self.movement_joystick.center_y + label_config["offset_y"]
        ))

        # Draw camera area
        self.camera_area.draw(self.screen)

        # Draw look path visualization
        self.look_visualization.draw(self.screen, self.look_path_tracker)

        # Draw look visualization label
        look_config = self.layout_config["core_elements"]["look_visualization"]["label"]
        look_label = self.small_font.render(look_config["text"], True, WHITE)
        self.screen.blit(look_label, (look_config["x"], look_config["y"]))

    def _draw_action_buttons(self):
        """Draw all action buttons."""
        for button in self.buttons.values():
            button.draw(self.screen)

    def _draw_hotbar(self):
        """Draw hotbar using configuration."""
        hotbar_config = self.layout_config["hotbar"]

        # Draw hotbar slot buttons
        for i, button in enumerate(self.hotbar_buttons):
            # Highlight the currently selected slot
            if i == self.state.current_hotbar_slot:
                # Draw a highlight background for the selected slot
                highlight_config = hotbar_config["highlight"]
                highlight_rect = pygame.Rect(
                    button.rect.x - highlight_config["border_offset"],
                    button.rect.y - highlight_config["border_offset"],
                    button.rect.width + (highlight_config["border_offset"] * 2),
                    button.rect.height + (highlight_config["border_offset"] * 2),
                )
                pygame.draw.rect(self.screen, highlight_config["color"], highlight_rect, highlight_config["border_width"])
            button.draw(self.screen)

        # Draw hotbar label
        label_config = hotbar_config["label"]
        hotbar_label = self.small_font.render(label_config["text"], True, WHITE)
        self.screen.blit(hotbar_label, (label_config["x"], label_config["y"]))

    def _draw_instructions(self):
        """Draw instructions using configuration."""
        instructions_config = self.layout_config["instructions"]

        for i, instruction in enumerate(instructions_config["text"]):
            text = self.small_font.render(instruction, True, instructions_config["color"])
            y_pos = instructions_config["start_y"] + (i * instructions_config["line_spacing"])
            self.screen.blit(text, (instructions_config["start_x"], y_pos))
