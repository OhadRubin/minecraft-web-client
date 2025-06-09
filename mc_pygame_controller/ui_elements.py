import pygame
import math
from typing import Optional, Tuple, List

from .constants import *
from .text_input_manager import TextInputManager, TextInputVisualizer

class Button:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: tuple = GRAY,
        text_color: tuple = WHITE,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.is_pressed = False
        self.font = pygame.font.Font(None, 20)

    def handle_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool) -> bool:
        was_pressed = self.is_pressed

        if self.rect.collidepoint(mouse_pos) and mouse_pressed:
            self.is_pressed = True
        elif not mouse_pressed:  # Only release when mouse is actually released
            self.is_pressed = False

        # Return True if button was just pressed (not held)
        return self.is_pressed and not was_pressed

    def draw(self, surface):
        color = LIGHT_GRAY if self.is_pressed else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)

        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class ToggleButton(Button):
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: tuple = GRAY,
        text_color: tuple = WHITE,
    ):
        super().__init__(x, y, width, height, text, color, text_color)
        self.is_toggled = False

    def handle_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool) -> bool:
        was_pressed = self.is_pressed

        if self.rect.collidepoint(mouse_pos) and mouse_pressed:
            self.is_pressed = True
        elif not mouse_pressed:  # Only release when mouse is actually released
            self.is_pressed = False

        # Toggle on button press
        if self.is_pressed and not was_pressed:
            self.is_toggled = not self.is_toggled
            return True
        return False

    def draw(self, surface):
        if self.is_toggled:
            color = GREEN
        else:
            color = LIGHT_GRAY if self.is_pressed else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)

        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class VirtualJoystick:
    def __init__(self, center_x: int, center_y: int, radius: int):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.knob_x = center_x
        self.knob_y = center_y
        self.knob_radius = radius // 3
        self.is_pressed = False

    def handle_mouse(
        self, mouse_pos: Tuple[int, int], mouse_pressed: bool
    ) -> Tuple[float, float]:
        mx, my = mouse_pos
        distance = math.sqrt((mx - self.center_x) ** 2 + (my - self.center_y) ** 2)

        if mouse_pressed and distance <= self.radius:
            self.is_pressed = True

        if not mouse_pressed:
            self.is_pressed = False
            self.knob_x = self.center_x
            self.knob_y = self.center_y
            return 0.0, 0.0

        if self.is_pressed:
            if distance <= self.radius:
                self.knob_x = mx
                self.knob_y = my
            else:
                # Clamp to circle edge
                angle = math.atan2(my - self.center_y, mx - self.center_x)
                self.knob_x = self.center_x + math.cos(angle) * self.radius
                self.knob_y = self.center_y + math.sin(angle) * self.radius

            # Calculate normalized values (-1 to 1)
            norm_x = (self.knob_x - self.center_x) / self.radius
            norm_y = (self.knob_y - self.center_y) / self.radius
            return norm_x, norm_y

        return 0.0, 0.0

    def draw(self, surface):
        # Draw outer circle
        color = BLUE if self.is_pressed else GRAY
        pygame.draw.circle(
            surface, color, (self.center_x, self.center_y), self.radius, 3
        )

        # Draw knob
        knob_color = YELLOW if self.is_pressed else LIGHT_GRAY
        pygame.draw.circle(
            surface, knob_color, (int(self.knob_x), int(self.knob_y)), self.knob_radius
        )


class KeyboardMovement:
    def __init__(self):
        self.w_pressed = False
        self.a_pressed = False
        self.s_pressed = False
        self.d_pressed = False

    def handle_keyboard(self, keys_pressed) -> Tuple[float, float]:
        # Update key states
        self.w_pressed = keys_pressed[pygame.K_w]
        self.a_pressed = keys_pressed[pygame.K_a]
        self.s_pressed = keys_pressed[pygame.K_s]
        self.d_pressed = keys_pressed[pygame.K_d]

        # Calculate normalized values (-1 to 1) similar to joystick
        norm_x = 0.0
        norm_y = 0.0

        if self.a_pressed:
            norm_x -= 1.0
        if self.d_pressed:
            norm_x += 1.0
        if self.w_pressed:
            norm_y -= 1.0  # W = forward = negative Y (like joystick up)
        if self.s_pressed:
            norm_y += 1.0  # S = backward = positive Y (like joystick down)

        # Normalize diagonal movement to maintain consistent speed
        if norm_x != 0.0 and norm_y != 0.0:
            length = math.sqrt(norm_x * norm_x + norm_y * norm_y)
            norm_x /= length
            norm_y /= length

        return norm_x, norm_y

    def is_any_key_pressed(self) -> bool:
        return self.w_pressed or self.a_pressed or self.s_pressed or self.d_pressed


class TouchArea:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.last_mouse_pos: Optional[Tuple[int, int]] = None
        self.is_touching = False

    def handle_mouse(
        self, mouse_pos: Tuple[int, int], mouse_pressed: bool
    ) -> Tuple[int, int]:
        mx, my = mouse_pos

        if self.rect.collidepoint(mx, my) and mouse_pressed:
            if not self.is_touching:
                self.is_touching = True
                self.last_mouse_pos = (mx, my)
                return 0, 0  # No movement on first touch
            else:
                if self.last_mouse_pos:
                    delta_x = mx - self.last_mouse_pos[0]
                    delta_y = my - self.last_mouse_pos[1]
                    self.last_mouse_pos = (mx, my)
                    return delta_x, delta_y

        if not mouse_pressed:
            self.is_touching = False
            self.last_mouse_pos = None

        return 0, 0

    def draw(self, surface):
        color = GREEN if self.is_touching else DARK_GRAY
        pygame.draw.rect(surface, color, self.rect, 3)  # Thicker border for visibility

        # Draw a subtle fill for better visibility
        fill_color = (0, 64, 0) if self.is_touching else (32, 32, 32)
        pygame.draw.rect(surface, fill_color, self.rect)
        pygame.draw.rect(surface, color, self.rect, 3)  # Border on top

        # Draw label
        font = pygame.font.Font(None, 28)  # Larger font for bigger area
        text = font.render("Camera Look Area - Drag to Look Around", True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)


class TextInputField:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        placeholder: str = "Enter task description...",
        font_size: int = 20,
        max_length: int = 100,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.placeholder = placeholder
        self.font_size = font_size
        self.is_focused = False
        self.is_active = False

        # Create text input manager with length validation
        validator = lambda text: len(text) <= max_length
        self.text_manager = TextInputManager(validator=validator)

        # Create visualizer with custom font
        font_object = pygame.font.Font(None, font_size)
        self.text_visualizer = TextInputVisualizer(
            manager=self.text_manager,
            font_object=font_object,
            antialias=True,
            font_color=WHITE,
            cursor_color=WHITE,
            cursor_blink_interval=500,
        )

        # Background and border colors
        self.bg_color = (40, 40, 40)
        self.border_color = WHITE
        self.focused_border_color = BLUE

    def handle_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool) -> bool:
        """Handle mouse input. Returns True if field was clicked."""
        clicked = False
        if self.rect.collidepoint(mouse_pos) and mouse_pressed:
            if not self.is_focused:
                self.is_focused = True
                clicked = True
        elif mouse_pressed and not self.rect.collidepoint(mouse_pos):
            self.is_focused = False

        return clicked

    def handle_events(self, events: List[pygame.event.Event]) -> bool:
        """Handle pygame events. Returns True if Enter was pressed."""
        if not self.is_focused:
            return False

        enter_pressed = False
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                enter_pressed = True
                self.is_focused = False  # Unfocus on enter

        # Update text input
        self.text_visualizer.update(events)
        return enter_pressed

    @property
    def value(self) -> str:
        """Get the current text value."""
        return self.text_manager.value

    @value.setter
    def value(self, text: str):
        """Set the current text value."""
        self.text_manager.value = text

    def clear(self):
        """Clear the text field."""
        self.text_manager.value = ""

    def draw(self, surface):
        """Draw the text input field."""
        # Draw background
        pygame.draw.rect(surface, self.bg_color, self.rect)

        # Draw border (different color when focused)
        border_color = (
            self.focused_border_color if self.is_focused else self.border_color
        )
        pygame.draw.rect(surface, border_color, self.rect, 2)

        # Draw text content
        if self.value or self.is_focused:
            # Show actual text and cursor
            text_surface = self.text_visualizer.surface
            # Position text with some padding
            text_x = self.rect.x + 8
            text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
            surface.blit(text_surface, (text_x, text_y))
        else:
            # Show placeholder text
            font = pygame.font.Font(None, self.font_size)
            placeholder_surface = font.render(self.placeholder, True, (150, 150, 150))
            text_x = self.rect.x + 8
            text_y = (
                self.rect.y + (self.rect.height - placeholder_surface.get_height()) // 2
            )
            surface.blit(placeholder_surface, (text_x, text_y))


class ImageViewer:
    def __init__(self, x: int, y: int, width: int, height: int, image_path: str = ""):
        self.rect = pygame.Rect(x, y, width, height)
        self.image_path = image_path
        self.image = None
        self.scaled_image = None
        self.last_modified_time = 0

        # Styling
        self.border_color = WHITE
        self.border_width = 2
        self.background_color = BLACK
        self.padding = 8  # Internal padding for better appearance

        # Load image if path provided
        if image_path:
            self.load_image(image_path)

    def set_image_path(self, image_path: str):
        """Set a new image path and load the image."""
        self.image_path = image_path
        self.load_image(image_path)

    def load_image(self, image_path: str):
        """Load and scale an image to fit the viewer."""
        try:
            import os

            # Check if file exists and get modification time
            if os.path.exists(image_path):
                current_modified_time = os.path.getmtime(image_path)

                # Only reload if file has changed or first time loading
                if current_modified_time != self.last_modified_time:
                    self.last_modified_time = current_modified_time

                    # Load the image and convert for better performance
                    loaded_image = pygame.image.load(image_path)

                    # Convert with alpha for transparency support (PNG files)
                    if image_path.lower().endswith(".png"):
                        self.image = loaded_image.convert_alpha()
                    else:
                        self.image = loaded_image.convert()

                    # Scale image to fit the viewer while maintaining aspect ratio
                    self._scale_image()
            else:
                self.image = None
                self.scaled_image = None

        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            self.image = None
            self.scaled_image = None

    def _scale_image(self):
        """Scale the image to fit the viewer while maintaining aspect ratio."""
        if not self.image:
            self.scaled_image = None
            return

        # Get original image dimensions
        img_width, img_height = self.image.get_size()

        # Add padding inside the border for better appearance
        available_width = self.rect.width - (self.border_width * 2) - (self.padding * 2)
        available_height = (
            self.rect.height - (self.border_width * 2) - (self.padding * 2)
        )

        # Ensure we have positive dimensions
        if available_width <= 0 or available_height <= 0:
            self.scaled_image = None
            return

            # Calculate scaling factors (use float division for precision)
        scale_x = float(available_width) / float(img_width)
        scale_y = float(available_height) / float(img_height)

        # Use the smaller scale to maintain aspect ratio (fit within bounds)
        base_scale = min(scale_x, scale_y)

        # Apply display scaling compensation for high-DPI displays (macOS Retina)
        # The pygame window might be scaled down by the OS, so we need to scale up
        # Try different values: 1.5, 2.0, or 2.5 depending on your display
        display_scale_factor = 5  # Start with 1.8x to test
        scale = min(base_scale * display_scale_factor, max(scale_x, scale_y))

        # Calculate new dimensions with proper rounding
        new_width = max(1, int(round(img_width * scale)))
        new_height = max(1, int(round(img_height * scale)))

        # # Debug logging for testing - always print to see changes
        # print(f"ImageViewer SCALING DEBUG:")
        # print(f"  Viewer rect: {self.rect.width}x{self.rect.height}")
        # print(f"  Border width: {self.border_width}, Padding: {self.padding}")
        # print(f"  Available space: {available_width}x{available_height}")
        # print(f"  Original image: {img_width}x{img_height}")
        # print(
        #     f"  Base scale factors: x={scale_x:.3f}, y={scale_y:.3f}, base={base_scale:.3f}"
        # )
        # print(f"  Display scale factor: {display_scale_factor}")
        # print(f"  Final scale chosen: {scale:.3f}")
        # print(f"  Final scaled: {new_width}x{new_height}")

        # Scale the image with proper aspect ratio
        self.scaled_image = pygame.transform.scale(self.image, (new_width, new_height))

    def update(self):
        """Update the image if the file has changed."""
        if self.image_path:
            self.load_image(self.image_path)

    def draw(self, surface):
        """Draw the image viewer."""
        # Draw background
        pygame.draw.rect(surface, self.background_color, self.rect)

        # Draw border
        pygame.draw.rect(surface, self.border_color, self.rect, self.border_width)

        # Draw image if available
        if self.scaled_image:
            # Center the scaled image within the padded border area
            img_rect = self.scaled_image.get_rect()

            # Calculate the inner area (excluding border and padding)
            inner_rect = pygame.Rect(
                self.rect.x + self.border_width + self.padding,
                self.rect.y + self.border_width + self.padding,
                self.rect.width - (self.border_width * 2) - (self.padding * 2),
                self.rect.height - (self.border_width * 2) - (self.padding * 2),
            )

            # Center the image within the inner area
            img_rect.center = inner_rect.center

            # # Debug the actual drawing - only print once to avoid spam
            # if not hasattr(self, "_draw_debug_printed"):
            #     print(f"ImageViewer DRAW DEBUG:")
            #     print(f"  Scaled image size: {self.scaled_image.get_size()}")
            #     print(f"  img_rect: {img_rect}")
            #     print(f"  inner_rect: {inner_rect}")
            #     print(f"  Drawing at position: ({img_rect.x}, {img_rect.y})")
            #     self._draw_debug_printed = True

            surface.blit(self.scaled_image, img_rect)
        else:
            # Draw "No Image" text if no image is loaded
            font = pygame.font.Font(None, 24)
            text = font.render("No Image", True, WHITE)
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)
