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
WINDOW_WIDTH = 1600  # Increased from 1000
WINDOW_HEIGHT = 900  # Increased from 600
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


class MinecraftController:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Minecraft Web Client Controller")
        self.clock = pygame.time.Clock()
        self.running = True

        # UI Elements
        self.movement_joystick = VirtualJoystick(
            150, WINDOW_HEIGHT - 200, 100
        )  # Larger joystick, adjusted position
        self.keyboard_movement = KeyboardMovement()
        self.camera_area = TouchArea(
            400, 50, 800, 500
        )  # Much larger camera area: 800x500

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

        # Hotbar Slot Buttons (1-9)
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

        # State tracking for hotbar
        self.current_hotbar_slot = 0  # Currently selected slot (0-8)
        self.last_hotbar_slot = -1  # Track last set slot to avoid duplicate commands

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

        # Keyboard shortcut states
        self._ctrl_pressed = False
        self._tab_pressed = False
        self._z_pressed = False
        self._x_pressed = False
        self._space_pressed = False
        self._q_pressed = False
        self._f_pressed = False

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
            print("LEFT CLICK DOWN - sending command")
            self.send_command_sync(
                {
                    "type": "documentMouseEvent",
                    "button": 0,
                    "action": "down",
                    "updateMouse": True,
                }
            )
            self.left_clicking = True
        elif not pressed and self.left_clicking:
            print("LEFT CLICK UP - sending command")
            self.send_command_sync(
                {
                    "type": "documentMouseEvent",
                    "button": 0,
                    "action": "up",
                    "updateMouse": False,
                }
            )
            self.left_clicking = False

    def handle_right_click(self, pressed: bool):
        if pressed and not self.right_clicking:
            print("RIGHT CLICK DOWN - sending command")
            self.send_command_sync(
                {
                    "type": "documentMouseEvent",
                    "button": 2,
                    "action": "down",
                    "updateMouse": True,
                }
            )
            self.right_clicking = True
        elif not pressed and self.right_clicking:
            print("RIGHT CLICK UP - sending command")
            self.send_command_sync(
                {
                    "type": "documentMouseEvent",
                    "button": 2,
                    "action": "up",
                    "updateMouse": False,
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

    def handle_hotbar_slot(self, slot: int):
        """Handle hotbar slot selection (slot should be 0-8)"""
        if 0 <= slot <= 8 and slot != self.last_hotbar_slot:
            print(f"HOTBAR SLOT {slot + 1} - sending command")
            command = {"type": "setHotbarSlot", "slot": slot}
            self.send_command_sync(command)
            self.current_hotbar_slot = slot
            self.last_hotbar_slot = slot

    def handle_drop_item(self):
        """Handle dropping 1 item from current hotbar slot"""
        print("DROP ITEM - sending command")
        command = {"type": "dropItem", "amount": 1}
        self.send_command_sync(command)

    def handle_swap_hands(self):
        """Handle swapping main hand and off-hand items"""
        print("SWAP HANDS - sending command")
        command = {"type": "swapHands"}
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
                self.movement_joystick.center_y + 120,  # Adjusted for larger joystick
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
        self.drop_btn.draw(self.screen)
        self.swap_hands_btn.draw(self.screen)

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
            "1-9: Hotbar slots",
            "ESC: Quit | R: Reconnect",
        ]

        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, WHITE)
            self.screen.blit(
                text, (10, WINDOW_HEIGHT - 150 + i * 22)
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
        if self._ctrl_pressed:
            shortcut_status.append("Ctrl")
        if self._tab_pressed:
            shortcut_status.append("Tab")
        if self._z_pressed:
            shortcut_status.append("Z")
        if self._x_pressed:
            shortcut_status.append("X")
        if self._space_pressed:
            shortcut_status.append("Space")
        if self._q_pressed:
            shortcut_status.append("Q")
        if self._f_pressed:
            shortcut_status.append("F")

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

            # Get keyboard state
            keys_pressed = pygame.key.get_pressed()

            # Handle keyboard movement (similar to joystick)
            keyboard_move_x, keyboard_move_y = self.keyboard_movement.handle_keyboard(
                keys_pressed
            )

            # Handle keyboard shortcuts for clicking
            ctrl_pressed = keys_pressed[pygame.K_LCTRL] or keys_pressed[pygame.K_RCTRL]
            tab_pressed = keys_pressed[pygame.K_TAB]

            # Add alternative keys that are less likely to be intercepted
            z_pressed = keys_pressed[pygame.K_z]
            x_pressed = keys_pressed[pygame.K_x]

            # Add spacebar for jumping
            space_pressed = keys_pressed[pygame.K_SPACE]

            # Add item management shortcuts
            q_pressed = keys_pressed[pygame.K_q]  # Drop item (standard Minecraft)
            f_pressed = keys_pressed[pygame.K_f]  # Swap hands (standard Minecraft)

            # Combine all left click inputs
            left_click_input = ctrl_pressed or z_pressed
            # Combine all right click inputs
            right_click_input = tab_pressed or x_pressed

            # Store keyboard shortcut states for UI display
            self._ctrl_pressed = ctrl_pressed
            self._tab_pressed = tab_pressed
            self._z_pressed = z_pressed
            self._x_pressed = x_pressed
            self._space_pressed = space_pressed
            self._q_pressed = q_pressed
            self._f_pressed = f_pressed

            # Debug output for keyboard detection
            if ctrl_pressed and not hasattr(self, "_last_ctrl_pressed"):
                print("Ctrl pressed detected!")
                self._last_ctrl_pressed = True
            elif not ctrl_pressed and hasattr(self, "_last_ctrl_pressed"):
                print("Ctrl released detected!")
                delattr(self, "_last_ctrl_pressed")

            if tab_pressed and not hasattr(self, "_last_tab_pressed"):
                print("Tab pressed detected!")
                self._last_tab_pressed = True
            elif not tab_pressed and hasattr(self, "_last_tab_pressed"):
                print("Tab released detected!")
                delattr(self, "_last_tab_pressed")

            # Debug for alternative keys
            if z_pressed and not hasattr(self, "_last_z_pressed"):
                print("Z pressed detected! (Left click)")
                self._last_z_pressed = True
            elif not z_pressed and hasattr(self, "_last_z_pressed"):
                print("Z released detected!")
                delattr(self, "_last_z_pressed")

            if x_pressed and not hasattr(self, "_last_x_pressed"):
                print("X pressed detected! (Right click)")
                self._last_x_pressed = True
            elif not x_pressed and hasattr(self, "_last_x_pressed"):
                print("X released detected!")
                delattr(self, "_last_x_pressed")

            # Debug for spacebar
            if space_pressed and not hasattr(self, "_last_space_pressed"):
                print("Spacebar pressed detected! (Jump)")
                self._last_space_pressed = True
            elif not space_pressed and hasattr(self, "_last_space_pressed"):
                print("Spacebar released detected!")
                delattr(self, "_last_space_pressed")

            # Debug for Q key (drop item)
            if q_pressed and not hasattr(self, "_last_q_pressed"):
                print("Q pressed detected! (Drop item)")
                self.handle_drop_item()
                self._last_q_pressed = True
            elif not q_pressed and hasattr(self, "_last_q_pressed"):
                delattr(self, "_last_q_pressed")

            # Debug for F key (swap hands)
            if f_pressed and not hasattr(self, "_last_f_pressed"):
                print("F pressed detected! (Swap hands)")
                self.handle_swap_hands()
                self._last_f_pressed = True
            elif not f_pressed and hasattr(self, "_last_f_pressed"):
                delattr(self, "_last_f_pressed")

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
            self.handle_jump(self.jump_btn.is_pressed or space_pressed)

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

            # Handle hotbar slot buttons
            for i, button in enumerate(self.hotbar_buttons):
                if button.handle_mouse(mouse_pos, mouse_pressed):
                    self.handle_hotbar_slot(i)  # i is already 0-8

            # Handle keyboard shortcuts for hotbar slots (1-9 keys)
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
                key_pressed = keys_pressed[key]
                last_key_attr = f"_last_hotbar_{i}_pressed"

                # Only trigger on key press (not hold)
                if key_pressed and not hasattr(self, last_key_attr):
                    print(f"Hotbar key {i + 1} pressed!")
                    self.handle_hotbar_slot(i)  # i is already 0-8
                    setattr(self, last_key_attr, True)
                elif not key_pressed and hasattr(self, last_key_attr):
                    delattr(self, last_key_attr)

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
