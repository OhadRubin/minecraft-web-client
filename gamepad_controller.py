#!/usr/bin/env python3
"""
Simple Pygame Gamepad Controller
Visual gamepad interface that sends commands via WebSocket
Now supports both visual interface and physical gamepads
"""

import pygame
import asyncio
import websockets
import json
import math
import sys
from typing import Optional, Tuple, List

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
BLUE = (100, 150, 255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
YELLOW = (255, 255, 100)
ORANGE = (255, 165, 0)


class GamepadButton:
    def __init__(self, x: int, y: int, radius: int, button_id: int, label: str = ""):
        self.x = x
        self.y = y
        self.radius = radius
        self.button_id = button_id
        self.label = label or str(button_id)
        self.pressed = False
        self.hover = False

    def contains_point(self, x: int, y: int) -> bool:
        distance = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        return distance <= self.radius

    def draw(self, screen):
        # Button color based on state
        if self.pressed:
            color = RED
        elif self.hover:
            color = LIGHT_GRAY
        else:
            color = GRAY

        # Draw button circle
        pygame.draw.circle(screen, color, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, BLACK, (self.x, self.y), self.radius, 2)

        # Draw label
        font = pygame.font.Font(None, 24)
        text = font.render(self.label, True, BLACK)
        text_rect = text.get_rect(center=(self.x, self.y))
        screen.blit(text, text_rect)


class GamepadJoystick:
    def __init__(self, x: int, y: int, radius: int, stick_id: int, label: str = ""):
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.stick_id = stick_id
        self.label = label or f"Stick {stick_id}"

        # Current position (-1 to 1 range)
        self.x_pos = 0.0
        self.y_pos = 0.0

        # Visual stick position
        self.stick_x = x
        self.stick_y = y

        self.dragging = False
        self.max_distance = radius - 15  # Leave some margin

    def contains_point(self, x: int, y: int) -> bool:
        distance = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
        return distance <= self.radius

    def update_position(self, mouse_x: int, mouse_y: int):
        # Calculate offset from center
        dx = mouse_x - self.center_x
        dy = mouse_y - self.center_y

        # Limit to circle
        distance = math.sqrt(dx**2 + dy**2)
        if distance > self.max_distance:
            dx = dx * self.max_distance / distance
            dy = dy * self.max_distance / distance

        # Update visual position
        self.stick_x = self.center_x + dx
        self.stick_y = self.center_y + dy

        # Update normalized position (-1 to 1)
        self.x_pos = dx / self.max_distance
        self.y_pos = dy / self.max_distance

    def reset_position(self):
        self.stick_x = self.center_x
        self.stick_y = self.center_y
        self.x_pos = 0.0
        self.y_pos = 0.0

    def draw(self, screen):
        # Draw outer circle
        pygame.draw.circle(
            screen, LIGHT_GRAY, (self.center_x, self.center_y), self.radius
        )
        pygame.draw.circle(
            screen, BLACK, (self.center_x, self.center_y), self.radius, 3
        )

        # Draw inner stick
        stick_radius = 12
        pygame.draw.circle(
            screen, BLUE, (int(self.stick_x), int(self.stick_y)), stick_radius
        )
        pygame.draw.circle(
            screen, BLACK, (int(self.stick_x), int(self.stick_y)), stick_radius, 2
        )

        # Draw label
        font = pygame.font.Font(None, 20)
        text = font.render(self.label, True, BLACK)
        text_rect = text.get_rect(
            center=(self.center_x, self.center_y + self.radius + 20)
        )
        screen.blit(text, text_rect)


class GamepadController:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()  # Initialize joystick module
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Gamepad Controller")
        self.clock = pygame.time.Clock()
        self.running = True

        # WebSocket connection
        self.websocket = None
        self.connected = False

        # Physical gamepad support
        self.physical_gamepads: List[pygame.joystick.Joystick] = []
        self.gamepad_deadzone = 0.15  # Deadzone for analog sticks
        self.setup_physical_gamepads()

        # Create buttons based on standard gamepad layout
        self.buttons = []
        self.joysticks = []

        self.setup_gamepad_layout()

        # Mouse state
        self.mouse_pressed = False
        self.dragging_joystick = None

        # Physical gamepad button mapping (Xbox controller standard)
        # Maps pygame button indices to our button IDs
        self.button_mapping = {
            0: 0,  # A button
            1: 1,  # B button
            2: 2,  # X button
            3: 3,  # Y button
            4: 4,  # Left shoulder (L1)
            5: 5,  # Right shoulder (R1)
            6: 6,  # Left trigger (L2) - if available as button
            7: 7,  # Right trigger (R2) - if available as button
            8: 8,  # Back/Select button
            9: 9,  # Start button
            10: 10,  # Left stick click
            11: 11,  # Right stick click
        }

    def setup_physical_gamepads(self):
        """Detect and initialize physical gamepads"""
        joystick_count = pygame.joystick.get_count()
        print(f"🎮 Found {joystick_count} physical gamepad(s)")

        for i in range(joystick_count):
            try:
                gamepad = pygame.joystick.Joystick(i)
                gamepad.init()
                self.physical_gamepads.append(gamepad)
                print(f"✅ Connected: {gamepad.get_name()}")
                print(f"   Buttons: {gamepad.get_numbuttons()}")
                print(f"   Axes: {gamepad.get_numaxes()}")
                print(f"   Hats: {gamepad.get_numhats()}")
            except Exception as e:
                print(f"❌ Failed to initialize gamepad {i}: {e}")

    def apply_deadzone(self, value: float) -> float:
        """Apply deadzone to analog stick values"""
        if abs(value) < self.gamepad_deadzone:
            return 0.0
        return value

    def setup_gamepad_layout(self):
        # Face buttons (right side) - A, B, X, Y
        face_center_x, face_center_y = 650, 250
        face_spacing = 35

        self.buttons.append(
            GamepadButton(face_center_x, face_center_y + face_spacing, 20, 0, "A")
        )  # A (bottom)
        self.buttons.append(
            GamepadButton(face_center_x + face_spacing, face_center_y, 20, 1, "B")
        )  # B (right)
        self.buttons.append(
            GamepadButton(face_center_x - face_spacing, face_center_y, 20, 2, "X")
        )  # X (left)
        self.buttons.append(
            GamepadButton(face_center_x, face_center_y - face_spacing, 20, 3, "Y")
        )  # Y (top)

        # D-Pad (left side)
        dpad_center_x, dpad_center_y = 150, 250
        dpad_spacing = 30

        self.buttons.append(
            GamepadButton(dpad_center_x - dpad_spacing, dpad_center_y, 15, 14, "←")
        )  # Left
        self.buttons.append(
            GamepadButton(dpad_center_x + dpad_spacing, dpad_center_y, 15, 12, "→")
        )  # Right
        self.buttons.append(
            GamepadButton(dpad_center_x, dpad_center_y - dpad_spacing, 15, 15, "↑")
        )  # Up
        self.buttons.append(
            GamepadButton(dpad_center_x, dpad_center_y + dpad_spacing, 15, 13, "↓")
        )  # Down

        # Shoulder buttons (top)
        self.buttons.append(GamepadButton(200, 80, 25, 4, "L1"))  # L1
        self.buttons.append(GamepadButton(280, 60, 20, 6, "L2"))  # L2
        self.buttons.append(GamepadButton(600, 80, 25, 5, "R1"))  # R1
        self.buttons.append(GamepadButton(520, 60, 20, 7, "R2"))  # R2

        # Center buttons
        self.buttons.append(GamepadButton(350, 200, 18, 8, "SELECT"))  # Select
        self.buttons.append(GamepadButton(450, 200, 18, 9, "START"))  # Start
        self.buttons.append(GamepadButton(400, 150, 15, 16, "HOME"))  # Home

        # Joysticks
        self.joysticks.append(
            GamepadJoystick(250, 400, 45, 0, "Left")
        )  # Left stick (id 10 in diagram)
        self.joysticks.append(
            GamepadJoystick(550, 400, 45, 1, "Right")
        )  # Right stick (id 11 in diagram)

    async def connect_websocket(self):
        try:
            print("🔌 Connecting to WebSocket...")
            self.websocket = await websockets.connect("ws://localhost:8081")

            # Register as MCP client
            init_msg = {"init": "pygame"}
            await self.websocket.send(json.dumps(init_msg))
            print("✅ Connected to WebSocket server")

            # Connect the gamepad
            await self.send_command({"type": "gamepadConnect"})

            self.connected = True
            return True

        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            self.connected = False
            return False

    async def send_command(self, command):
        if not self.websocket:
            return

        try:
            await self.websocket.send(json.dumps(command))
            print(f"📤 Sent: {command}")
        except Exception as e:
            print(f"❌ Error sending command: {e}")

    async def handle_button_press(self, button: GamepadButton):
        await self.send_command(
            {
                "type": "gamepadButtonPress",
                "buttonIndex": button.button_id,
                "duration": 150,
            }
        )

    async def handle_joystick_move(self, joystick: GamepadJoystick):
        await self.send_command(
            {
                "type": "gamepadJoystickMove",
                "stickIndex": joystick.stick_id,
                "x": round(joystick.x_pos, 3),
                "y": round(joystick.y_pos, 3),
            }
        )

    async def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Physical gamepad events
            elif event.type == pygame.JOYBUTTONDOWN:
                button_id = self.button_mapping.get(event.button)
                if button_id is not None:
                    print(
                        f"🎮 Physical button {event.button} pressed (mapped to {button_id})"
                    )
                    # Visual feedback - highlight the corresponding visual button
                    for button in self.buttons:
                        if button.button_id == button_id:
                            button.pressed = True
                    await self.send_command(
                        {
                            "type": "gamepadButtonPress",
                            "buttonIndex": button_id,
                            "duration": 150,
                        }
                    )

            elif event.type == pygame.JOYBUTTONUP:
                button_id = self.button_mapping.get(event.button)
                if button_id is not None:
                    # Remove visual feedback
                    for button in self.buttons:
                        if button.button_id == button_id:
                            button.pressed = False

            elif event.type == pygame.JOYAXISMOTION:
                # Handle analog sticks (typically axes 0,1 for left stick, 2,3 for right stick)
                gamepad_index = event.joy
                axis = event.axis
                value = self.apply_deadzone(event.value)

                if axis in [0, 1]:  # Left stick (X, Y)
                    stick_index = 0
                    joystick = self.joysticks[0] if len(self.joysticks) > 0 else None
                elif axis in [2, 3]:  # Right stick (X, Y)
                    stick_index = 1
                    joystick = self.joysticks[1] if len(self.joysticks) > 1 else None
                else:
                    joystick = None

                if joystick:
                    if axis % 2 == 0:  # X axis (0, 2, 4...)
                        joystick.x_pos = value
                    else:  # Y axis (1, 3, 5...)
                        joystick.y_pos = value

                    # Update visual position
                    joystick.stick_x = joystick.center_x + (
                        joystick.x_pos * joystick.max_distance
                    )
                    joystick.stick_y = joystick.center_y + (
                        joystick.y_pos * joystick.max_distance
                    )

                    await self.send_command(
                        {
                            "type": "gamepadJoystickMove",
                            "stickIndex": stick_index,
                            "x": round(joystick.x_pos, 3),
                            "y": round(joystick.y_pos, 3),
                        }
                    )

            elif event.type == pygame.JOYHATMOTION:
                # Handle D-pad
                hat_x, hat_y = event.value

                # Map D-pad to button presses
                dpad_buttons = {
                    (-1, 0): 14,  # Left
                    (1, 0): 12,  # Right
                    (0, 1): 15,  # Up
                    (0, -1): 13,  # Down
                }

                button_id = dpad_buttons.get(event.value)
                if button_id is not None:
                    print(f"🎮 D-pad pressed: {event.value} (mapped to {button_id})")
                    # Visual feedback
                    for button in self.buttons:
                        if button.button_id == button_id:
                            button.pressed = True

                    await self.send_command(
                        {
                            "type": "gamepadButtonPress",
                            "buttonIndex": button_id,
                            "duration": 150,
                        }
                    )

                    # Schedule button release
                    asyncio.create_task(self.release_dpad_button(button_id))

            # Mouse events for visual interface
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_x, mouse_y = event.pos
                    self.mouse_pressed = True

                    # Check button clicks
                    for button in self.buttons:
                        if button.contains_point(mouse_x, mouse_y):
                            button.pressed = True
                            await self.handle_button_press(button)

                    # Check joystick clicks
                    for joystick in self.joysticks:
                        if joystick.contains_point(mouse_x, mouse_y):
                            joystick.dragging = True
                            self.dragging_joystick = joystick
                            joystick.update_position(mouse_x, mouse_y)
                            await self.handle_joystick_move(joystick)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click release
                    self.mouse_pressed = False

                    # Release all buttons (only those not pressed by physical gamepad)
                    for button in self.buttons:
                        button.pressed = False

                    # Stop dragging joysticks and center them
                    if self.dragging_joystick:
                        self.dragging_joystick.dragging = False
                        self.dragging_joystick.reset_position()
                        await self.handle_joystick_move(self.dragging_joystick)
                        await self.send_command(
                            {
                                "type": "gamepadJoystickCenter",
                                "stickIndex": self.dragging_joystick.stick_id,
                            }
                        )
                        self.dragging_joystick = None

            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos

                # Update button hover states
                for button in self.buttons:
                    button.hover = button.contains_point(mouse_x, mouse_y)

                # Handle joystick dragging
                if self.dragging_joystick and self.dragging_joystick.dragging:
                    self.dragging_joystick.update_position(mouse_x, mouse_y)
                    await self.handle_joystick_move(self.dragging_joystick)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif (
                    event.key == pygame.K_c and pygame.key.get_pressed()[pygame.K_LCTRL]
                ):
                    self.running = False

    async def release_dpad_button(self, button_id: int):
        """Release D-pad button after a short delay"""
        await asyncio.sleep(0.1)
        for button in self.buttons:
            if button.button_id == button_id:
                button.pressed = False

    def draw(self):
        self.screen.fill(WHITE)

        # Draw title
        font = pygame.font.Font(None, 36)
        title = font.render("Gamepad Controller", True, BLACK)
        title_rect = title.get_rect(center=(400, 30))
        self.screen.blit(title, title_rect)

        # Draw connection status
        font = pygame.font.Font(None, 24)
        status_text = "Connected" if self.connected else "Disconnected"
        status_color = GREEN if self.connected else RED
        status = font.render(f"WebSocket: {status_text}", True, status_color)
        self.screen.blit(status, (10, 10))

        # Draw physical gamepad status
        gamepad_text = f"Physical Gamepads: {len(self.physical_gamepads)}"
        gamepad_color = ORANGE if len(self.physical_gamepads) > 0 else GRAY
        gamepad_status = font.render(gamepad_text, True, gamepad_color)
        self.screen.blit(gamepad_status, (10, 35))

        # Draw gamepad body outline
        body_rect = pygame.Rect(120, 120, 560, 400)
        pygame.draw.rect(self.screen, LIGHT_GRAY, body_rect, 0, 30)
        pygame.draw.rect(self.screen, BLACK, body_rect, 3, 30)

        # Draw all buttons
        for button in self.buttons:
            button.draw(self.screen)

        # Draw all joysticks
        for joystick in self.joysticks:
            joystick.draw(self.screen)

        # Draw instructions
        font = pygame.font.Font(None, 20)
        instructions = [
            "Click buttons or use physical gamepad",
            "Drag joysticks or use analog sticks",
            "ESC or Ctrl+C to quit",
        ]

        for i, instruction in enumerate(instructions):
            text = font.render(instruction, True, DARK_GRAY)
            self.screen.blit(text, (10, 550 + i * 20))

        pygame.display.flip()

    async def cleanup(self):
        if self.websocket:
            try:
                # Disconnect gamepad
                await self.send_command({"type": "gamepadDestroy"})
                await self.websocket.close()
                print("🔌 WebSocket disconnected")
            except:
                pass

        # Cleanup physical gamepads
        for gamepad in self.physical_gamepads:
            try:
                gamepad.quit()
            except:
                pass

        pygame.quit()

    async def run(self):
        # Try to connect to WebSocket
        await self.connect_websocket()

        # Main game loop
        try:
            while self.running:
                await self.handle_events()
                self.draw()
                self.clock.tick(60)

                # Small async yield
                await asyncio.sleep(0.001)

        except KeyboardInterrupt:
            print("\n⏹️ Interrupted by user")

        finally:
            await self.cleanup()


async def main():
    controller = GamepadController()
    await controller.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
