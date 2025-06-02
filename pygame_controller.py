import pygame
import asyncio
import json
import websockets
import threading
import math
import sys
from typing import Optional, Tuple

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1000  # Increased width for more buttons
WINDOW_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)


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
        pygame.draw.rect(surface, color, self.rect, 2)

        # Draw label
        font = pygame.font.Font(None, 24)
        text = font.render("Camera Look Area", True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)


class MinecraftController:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Minecraft Web Client Controller")
        self.clock = pygame.time.Clock()
        self.running = True

        # UI Elements
        self.movement_joystick = VirtualJoystick(150, WINDOW_HEIGHT - 150, 80)
        self.camera_area = TouchArea(350, 50, 350, 250)

        # Action Buttons
        button_width = 80
        button_height = 35
        start_x = 750
        start_y = 350
        spacing = 45

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

        # WebSocket connection
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self.connection_thread = None

        # State tracking
        self.last_movement = (0.0, 0.0)
        self.left_clicking = False
        self.right_clicking = False
        self.jumping = False
        self.sneaking = False
        self.sprinting = False
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

    async def connect_websocket(self):
        try:
            uri = "ws://localhost:8081"
            print(f"Connecting to {uri}...")
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print("Connected to Minecraft Web Client!")

            # Keep connection alive
            while self.connected and self.running:
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connected = False

    def start_websocket_connection(self):
        """Start WebSocket connection in a separate thread"""

        def run_async():
            asyncio.run(self.connect_websocket())

        self.connection_thread = threading.Thread(target=run_async, daemon=True)
        self.connection_thread.start()

    async def send_command(self, command: dict):
        if self.websocket and self.connected:
            try:
                await self.websocket.send(json.dumps(command))
            except Exception as e:
                print(f"Error sending command: {e}")
                self.connected = False

    def send_command_sync(self, command: dict):
        """Send command synchronously from main thread"""
        if self.websocket and self.connected:
            try:
                # Use a simple approach - create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.websocket.send(json.dumps(command)))
                loop.close()
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
            command = {"type": "move", "x": movement_x, "z": movement_z}
            self.send_command_sync(command)
            self.last_movement = (movement_x, movement_z)

    def handle_camera_look(self, delta_x: int, delta_y: int):
        if delta_x != 0 or delta_y != 0:
            # Scale the movement for better sensitivity
            scaled_x = delta_x * 2
            scaled_y = delta_y * 2

            command = {"type": "look", "movementX": scaled_x, "movementY": scaled_y}
            self.send_command_sync(command)

    def handle_left_click(self, pressed: bool):
        if pressed and not self.left_clicking:
            # Click the break/pickaxe button
            self.send_command_sync(
                {
                    "type": "clickElement",
                    "selector": "#ui-root > div:nth-child(1) > div:nth-child(5)",
                    "action": "down",
                }
            )
            self.left_clicking = True
        elif not pressed and self.left_clicking:
            # Release the break/pickaxe button
            self.send_command_sync(
                {
                    "type": "clickElement",
                    "selector": "#ui-root > div:nth-child(1) > div:nth-child(5)",
                    "action": "up",
                }
            )
            self.left_clicking = False

    def handle_right_click(self, pressed: bool):
        if pressed and not self.right_clicking:
            # Click the place/circle button
            self.send_command_sync(
                {
                    "type": "clickElement",
                    "selector": "#ui-root > div:nth-child(1) > div:nth-child(4)",
                    "action": "down",
                }
            )
            self.right_clicking = True
        elif not pressed and self.right_clicking:
            # Release the place/circle button
            self.send_command_sync(
                {
                    "type": "clickElement",
                    "selector": "#ui-root > div:nth-child(1) > div:nth-child(4)",
                    "action": "up",
                }
            )
            self.right_clicking = False

    def handle_jump(self, pressed: bool):
        if pressed and not self.jumping:
            self.send_command_sync(
                {"type": "control", "control": "jump", "state": True}
            )
            self.jumping = True
        elif not pressed and self.jumping:
            self.send_command_sync(
                {"type": "control", "control": "jump", "state": False}
            )
            self.jumping = False

    def handle_sneak(self, toggled: bool):
        if toggled != self.sneaking:
            self.send_command_sync(
                {"type": "control", "control": "sneak", "state": toggled}
            )
            self.sneaking = toggled

    def handle_sprint(self, toggled: bool):
        if toggled != self.sprinting:
            self.send_command_sync(
                {"type": "control", "control": "sprint", "state": toggled}
            )
            self.sprinting = toggled

    def handle_control_button(self, control: str, state: bool):
        command = {"type": "control", "control": control, "state": state}
        self.send_command_sync(command)

    def handle_inventory(self):
        # Send 'e' key command for inventory
        command = {"type": "control", "control": "inventory", "state": True}
        self.send_command_sync(command)
        # Immediately release
        command = {"type": "control", "control": "inventory", "state": False}
        self.send_command_sync(command)

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

        # Draw movement joystick
        self.movement_joystick.draw(self.screen)
        move_label = self.small_font.render("Movement", True, WHITE)
        self.screen.blit(
            move_label,
            (
                self.movement_joystick.center_x - 40,
                self.movement_joystick.center_y + 100,
            ),
        )

        # Draw camera area
        self.camera_area.draw(self.screen)

        # Draw action buttons
        self.left_click_btn.draw(self.screen)
        self.right_click_btn.draw(self.screen)
        self.jump_btn.draw(self.screen)
        self.sneak_btn.draw(self.screen)
        self.sprint_btn.draw(self.screen)
        self.inventory_btn.draw(self.screen)

        # Draw instructions
        instructions = [
            "Left joystick: Move character",
            "Camera area: Look around (drag)",
            "Buttons: Click actions",
            "ESC: Quit | R: Reconnect",
        ]

        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, WHITE)
            self.screen.blit(text, (10, WINDOW_HEIGHT - 100 + i * 20))

        # Draw current movement values
        move_text = self.small_font.render(
            f"Movement: X={self.last_movement[0]:.2f}, Z={self.last_movement[1]:.2f}",
            True,
            WHITE,
        )
        self.screen.blit(move_text, (350, 320))

        pygame.display.flip()

    def run(self):
        print("Starting Minecraft Controller...")
        print("Make sure the Minecraft web client server is running on localhost:8081")

        # Start WebSocket connection
        self.start_websocket_connection()

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

            # Handle movement joystick
            move_x, move_y = self.movement_joystick.handle_mouse(
                mouse_pos, mouse_pressed
            )
            self.handle_movement(move_x, move_y)

            # Handle camera look area
            delta_x, delta_y = self.camera_area.handle_mouse(mouse_pos, mouse_pressed)
            self.handle_camera_look(delta_x, delta_y)

            # Handle action buttons
            if self.left_click_btn.handle_mouse(mouse_pos, mouse_pressed):
                pass  # Handle on hold/release
            self.handle_left_click(self.left_click_btn.is_pressed)

            if self.right_click_btn.handle_mouse(mouse_pos, mouse_pressed):
                pass  # Handle on hold/release
            self.handle_right_click(self.right_click_btn.is_pressed)

            # Handle jump button - check both press and release
            self.jump_btn.handle_mouse(mouse_pos, mouse_pressed)
            self.handle_jump(self.jump_btn.is_pressed)

            # Handle toggle buttons - only send command when toggled
            if self.sneak_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_sneak(self.sneak_btn.is_toggled)

            if self.sprint_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_sprint(self.sprint_btn.is_toggled)

            if self.inventory_btn.handle_mouse(mouse_pos, mouse_pressed):
                self.handle_inventory()

            # Draw everything
            self.draw_ui()
            self.clock.tick(FPS)

        # Cleanup
        self.connected = False
        if self.websocket:
            asyncio.run(self.websocket.close())

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    controller = MinecraftController()
    controller.run()
