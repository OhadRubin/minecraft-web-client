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
WINDOW_WIDTH = 800
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
        self.camera_area = TouchArea(350, 50, 400, 300)

        # WebSocket connection
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self.connection_thread = None

        # State tracking
        self.last_movement = (0.0, 0.0)
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

        # Draw instructions
        instructions = [
            "Left joystick: Move character",
            "Right area: Look around (drag mouse)",
            "ESC: Quit",
            "R: Reconnect",
        ]

        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, WHITE)
            self.screen.blit(text, (10, WINDOW_HEIGHT - 120 + i * 25))

        # Draw current movement values
        move_text = self.small_font.render(
            f"Movement: X={self.last_movement[0]:.2f}, Z={self.last_movement[1]:.2f}",
            True,
            WHITE,
        )
        self.screen.blit(move_text, (350, 370))

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
