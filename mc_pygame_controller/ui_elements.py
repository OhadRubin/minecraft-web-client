import pygame
import math
from typing import Optional, Tuple

from .constants import *

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



