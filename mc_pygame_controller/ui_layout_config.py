"""
UI Layout Configuration

Data-driven layout configuration for the MinecraftController UI.
This removes hardcoded "magic numbers" and makes the layout easily customizable.
"""

from .constants import *
from .ui_elements import Button, ToggleButton


# Core UI layout dimensions and positions
UI_LAYOUT_CONFIG = {
    # Core UI elements
    "core_elements": {
        "movement_joystick": {
            "x": 150,
            "y": WINDOW_HEIGHT - 200,
            "radius": 100,
            "label": {"text": "Movement", "offset_x": -40, "offset_y": 120}
        },
        "camera_area": {
            "x": 400,
            "y": 50,
            "width": 800,
            "height": 500
        },
        "look_visualization": {
            "x": 1230,
            "y": 50,
            "width": 350,
            "height": 300,
            "label": {"text": "Look Path Visualization", "x": 1230, "y": 30}
        }
    },
    
    # Action buttons layout
    "action_buttons": {
        "base_config": {
            "width": 100,
            "height": 40,
            "start_x": 1300,
            "start_y": 600,
            "spacing": 50,
            "row_offset": 90  # Horizontal offset for second column
        },
        "buttons": [
            # Row 1
            {
                "name": "left_click_btn",
                "class": Button,
                "text": "Left Click",
                "color": RED,
                "row": 0,
                "col": 0
            },
            {
                "name": "right_click_btn", 
                "class": Button,
                "text": "Right Click",
                "color": BLUE,
                "row": 0,
                "col": 1
            },
            # Row 2
            {
                "name": "jump_btn",
                "class": Button,
                "text": "Jump",
                "color": GREEN,
                "row": 1,
                "col": 0
            },
            {
                "name": "sneak_btn",
                "class": ToggleButton,
                "text": "Sneak",
                "color": ORANGE,
                "row": 1,
                "col": 1
            },
            # Row 3
            {
                "name": "sprint_btn",
                "class": ToggleButton,
                "text": "Sprint",
                "color": PURPLE,
                "row": 2,
                "col": 0
            },
            {
                "name": "inventory_btn",
                "class": ToggleButton,
                "text": "Inventory",
                "color": GRAY,
                "row": 2,
                "col": 1
            },
            # Row 4 - Item management
            {
                "name": "drop_btn",
                "class": Button,
                "text": "Drop Item",
                "color": YELLOW,
                "row": 3,
                "col": 0
            },
            {
                "name": "swap_hands_btn",
                "class": Button,
                "text": "Swap Hands",
                "color": (255, 100, 255),  # Pink/magenta
                "row": 3,
                "col": 1
            },
            # Row 5 - Utility buttons (full width)
            {
                "name": "clear_path_btn",
                "class": Button,
                "text": "Clear Look Path",
                "color": (150, 75, 0),  # Brown
                "row": 4,
                "col": 0,
                "width": 210,  # button_width * 2 + row_offset + 10
                "span_cols": 2
            },
            # Row 6 - Debug buttons (full width)
            {
                "name": "test_status_btn",
                "class": Button,
                "text": "Test getBotStatus",
                "color": (0, 150, 75),  # Teal
                "row": 5,
                "col": 0,
                "width": 210,
                "span_cols": 2
            },
            # Row 7 - Demo button (full width)
            {
                "name": "save_demo_btn",
                "class": Button,
                "text": "Save Demo Step",
                "color": (150, 0, 150),  # Purple
                "row": 6,
                "col": 0,
                "width": 210,
                "span_cols": 2
            }
        ]
    },
    
    # Hotbar configuration
    "hotbar": {
        "button_width": 50,
        "button_height": 40,
        "start_x": 50,
        "y": WINDOW_HEIGHT - 60,  # Bottom of screen
        "spacing": 55,
        "count": 9,
        "label": {
            "text": "Hotbar Slots (1-9)",
            "x": 50,
            "y": WINDOW_HEIGHT - 85
        },
        "highlight": {
            "color": YELLOW,
            "border_width": 3,
            "border_offset": 3
        }
    },
    
    # Status display areas
    "status_display": {
        "title": {
            "text": "Minecraft Web Client Controller",
            "x": 10,
            "y": 10,
            "color": WHITE,
            "font_size": 36
        },
        "connection_status": {
            "x": 10,
            "y": 50,
            "color_connected": GREEN,
            "color_disconnected": RED,
            "font_size": 24
        },
        "mode_status": {
            "x": 10,
            "y": 75,
            "color_mcp": BLUE,
            "color_pygame": WHITE,
            "font_size": 24
        },
        "movement_info": {
            "x": 400,
            "y": 570,
            "color": WHITE,
            "font_size": 24
        },
        "keyboard_status": {
            "x": 400,
            "y": 590,
            "color": WHITE,
            "font_size": 24
        },
        "shortcuts_status": {
            "x": 400,
            "y": 610,
            "color": WHITE,
            "font_size": 24
        },
        "hotbar_status": {
            "x": 400,
            "y": 630,
            "color": WHITE,
            "font_size": 24
        }
    },
    
    # Instructions area
    "instructions": {
        "start_x": 10,
        "start_y": WINDOW_HEIGHT - 180,
        "line_spacing": 22,
        "color": WHITE,
        "font_size": 24,
        "text": [
            "WASD: Move character (keyboard)",
            "Left joystick: Move character (mouse)",
            "Camera area: Look around (drag)",
            "Buttons: Click actions",
            "Ctrl/Z: Left click | Tab/X: Right click",
            "Spacebar: Jump | Q: Drop item | F: Swap hands",
            "1-9: Hotbar slots | C: Clear look path",
            "ESC: Quit | R: Reconnect",
        ]
    }
}


def calculate_button_position(button_config: dict, base_config: dict) -> tuple[int, int]:
    """Calculate the actual position of a button based on its row/col and base config."""
    x = base_config["start_x"] + (button_config["col"] * base_config["row_offset"])
    y = base_config["start_y"] + (button_config["row"] * base_config["spacing"])
    return x, y


def calculate_button_size(button_config: dict, base_config: dict) -> tuple[int, int]:
    """Calculate the actual size of a button, accounting for column spanning."""
    width = button_config.get("width", base_config["width"])
    height = button_config.get("height", base_config["height"])
    return width, height


def get_font_size(font_type: str) -> int:
    """Get font size for different UI elements."""
    font_sizes = {
        "title": 36,
        "small": 24
    }
    return font_sizes.get(font_type, 24)