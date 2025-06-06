import pygame
import textwrap
import json
import os
from typing import Dict, List, Any, Optional
from .message_chain import OpenAIAsyncMessageChain



# --- Constants ---
# Window
WIN_WIDTH = 1400
WIN_HEIGHT = 900
FPS = 60

# Colors
COLOR_BG = (40, 42, 54)
COLOR_SYSTEM_BG = (68, 71, 90)
COLOR_USER_BG = (50, 52, 64)
COLOR_ASSISTANT_BG = (56, 58, 70)
COLOR_TOOL_BG = (80, 82, 98)
COLOR_PANEL_BG = (30, 32, 42)
COLOR_INPUT_BG = (68, 71, 90)
COLOR_INPUT_ACTIVE_BORDER = (189, 147, 249)
COLOR_BUTTON = (98, 114, 164)
COLOR_BUTTON_HOVER = (112, 128, 182)
COLOR_TEXT = (248, 248, 242)
COLOR_TEXT_DIM = (150, 150, 150)
COLOR_TOOL_NAME = (80, 250, 123)
COLOR_BORDER = (20, 21, 26)

# Fonts
pygame.font.init()
FONT_S = pygame.font.SysFont("Menlo", 14)
FONT_M = pygame.font.SysFont("Menlo", 16)
FONT_L = pygame.font.SysFont("Menlo", 20)
FONT_BOLD = pygame.font.SysFont("Menlo", 16, bold=True)


class InputField:
    """A simple text input field widget."""

    def __init__(self, rect: pygame.Rect, initial_text: str = "", font=FONT_M):
        self.rect = rect
        self.text = initial_text
        self.font = font
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                # Let the parent component handle the submission
                pass
            else:
                self.text += event.unicode

    def update(self):
        """Updates the cursor blink state."""
        self.cursor_timer = (self.cursor_timer + 1) % FPS
        self.cursor_visible = self.cursor_timer < FPS / 2

    def render(self, screen: pygame.Surface):
        pygame.draw.rect(screen, COLOR_INPUT_BG, self.rect)
        if self.active:
            pygame.draw.rect(screen, COLOR_INPUT_ACTIVE_BORDER, self.rect, 2)
        else:
            pygame.draw.rect(screen, COLOR_BORDER, self.rect, 1)

        text_surface = self.font.render(self.text, True, COLOR_TEXT)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

        if self.active and self.cursor_visible:
            cursor_pos = self.rect.x + 5 + text_surface.get_width()
            pygame.draw.line(
                screen,
                COLOR_TEXT,
                (cursor_pos, self.rect.y + 5),
                (cursor_pos, self.rect.y + self.rect.height - 5),
                2,
            )


class ConversationPanel:
    """Displays the chat history with scrolling."""

    def __init__(self, rect: pygame.Rect, messages: List[Dict]):
        self.rect = rect
        self.messages = messages
        self.scroll_y = 0
        self.content_height = 0
        self.rendered_messages = []
        self._render_messages()

    def _render_messages(self):
        """Pre-renders message surfaces for efficient display."""
        self.rendered_messages.clear()
        y_offset = 10
        for msg in self.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Handle multimodal content gracefully
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        text_parts.append("[Image Content]")
                content = "\n".join(text_parts)

            if msg.get("tool_calls"):
                content += "\n"
                for tc in msg.get("tool_calls", []):
                    func = tc.get("function", {})
                    name = func.get("name")
                    args = func.get("arguments")
                    content += f"  Tool Call: {name}({args})"

            color_map = {
                "system": COLOR_SYSTEM_BG,
                "user": COLOR_USER_BG,
                "assistant": COLOR_ASSISTANT_BG,
                "tool": COLOR_TOOL_BG,
            }
            bg_color = color_map.get(role, COLOR_SYSTEM_BG)
            wrapped_lines = textwrap.wrap(str(content), width=80)
            msg_height = (
                (len(wrapped_lines) * FONT_M.get_height()) + FONT_BOLD.get_height() + 20
            )
            msg_rect = pygame.Rect(10, y_offset, self.rect.width - 20, msg_height)

            msg_surface = pygame.Surface(msg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                msg_surface, bg_color, msg_surface.get_rect(), border_radius=5
            )

            role_surf = FONT_BOLD.render(role.capitalize(), True, COLOR_TOOL_NAME)
            msg_surface.blit(role_surf, (10, 5))

            line_y = 10 + FONT_BOLD.get_height()
            for line in wrapped_lines:
                line_surf = FONT_M.render(line, True, COLOR_TEXT)
                msg_surface.blit(line_surf, (10, line_y))
                line_y += FONT_M.get_height()

            self.rendered_messages.append((msg_surface, msg_rect))
            y_offset += msg_height + 10

        self.content_height = y_offset
        self.scroll_to_bottom()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(
            pygame.mouse.get_pos()
        ):
            self.scroll_y += event.y * 20
            self.scroll_y = min(0, self.scroll_y)
            max_scroll = max(0, self.content_height - self.rect.height)
            self.scroll_y = max(-max_scroll, self.scroll_y)

    def scroll_to_bottom(self):
        max_scroll = max(0, self.content_height - self.rect.height + 10)
        self.scroll_y = -max_scroll

    def render(self, screen: pygame.Surface):
        panel_surface = pygame.Surface(self.rect.size)
        panel_surface.fill(COLOR_PANEL_BG)

        for surf, rect in self.rendered_messages:
            panel_surface.blit(surf, (rect.x, rect.y + self.scroll_y))

        screen.blit(panel_surface, self.rect.topleft)
        pygame.draw.rect(screen, COLOR_BORDER, self.rect, 2)


class ToolsPanel:
    """Shows available tools and their descriptions."""

    def __init__(self, rect: pygame.Rect, tools: List[Dict]):
        self.rect = rect
        self.tools = tools
        self.tool_rects = []
        self._layout_tools()

    def _layout_tools(self):
        self.tool_rects.clear()
        y_offset = 10
        for tool in self.tools:
            name = tool.get("function", {}).get("name", "Unknown Tool")
            desc = tool.get("function", {}).get("description", "")

            name_surf = FONT_BOLD.render(name, True, COLOR_TOOL_NAME)
            wrapped_desc = textwrap.wrap(desc, width=50)
            desc_surfs = [
                FONT_S.render(line, True, COLOR_TEXT_DIM) for line in wrapped_desc
            ]

            tool_height = (
                name_surf.get_height() + sum(s.get_height() for s in desc_surfs) + 15
            )
            tool_rect = pygame.Rect(
                self.rect.x + 5,
                self.rect.y + y_offset,
                self.rect.width - 10,
                tool_height,
            )
            self.tool_rects.append(tool_rect)
            y_offset += tool_height

    def handle_event(self, event: pygame.event.Event) -> Optional[Dict]:
        """Returns the selected tool schema if a tool is clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.tool_rects):
                if rect.collidepoint(event.pos):
                    return self.tools[i]
        return None

    def render(self, screen: pygame.Surface):
        pygame.draw.rect(screen, COLOR_PANEL_BG, self.rect)
        pygame.draw.rect(screen, COLOR_BORDER, self.rect, 2)

        mouse_pos = pygame.mouse.get_pos()
        for i, tool in enumerate(self.tools):
            rect = self.tool_rects[i]
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, COLOR_INPUT_BG, rect, border_radius=3)

            name = tool.get("function", {}).get("name", "Unknown Tool")
            desc = tool.get("function", {}).get("description", "")
            name_surf = FONT_BOLD.render(name, True, COLOR_TOOL_NAME)
            screen.blit(name_surf, (rect.x + 10, rect.y + 5))

            line_y = rect.y + 5 + name_surf.get_height()
            for line in textwrap.wrap(desc, width=50):
                desc_surf = FONT_S.render(line, True, COLOR_TEXT_DIM)
                screen.blit(desc_surf, (rect.x + 10, line_y))
                line_y += desc_surf.get_height()


class ToolArgumentForm:
    """A dynamic form for tool arguments based on a schema."""

    def __init__(self, rect: pygame.Rect, tool: Dict):
        self.rect = rect
        self.tool = tool
        self.fields: Dict[str, InputField] = {}
        self.labels: Dict[str, pygame.Surface] = {}
        self.submit_button_rect = pygame.Rect(0, 0, 100, 30)
        self.back_button_rect = pygame.Rect(0, 0, 150, 25)
        self.active_field: Optional[InputField] = None
        self._create_fields()

    def _create_fields(self):
        schema = self.tool.get("function", {}).get("parameters", {})
        properties = schema.get("properties", {})
        y_offset = 50
        for name, prop in properties.items():
            label_text = f"{name} ({prop.get('type', 'any')}):"
            label_surf = FONT_M.render(label_text, True, COLOR_TEXT)
            self.labels[name] = label_surf

            field_rect = pygame.Rect(
                self.rect.x + 10, self.rect.y + y_offset + 20, self.rect.width - 20, 30
            )
            self.fields[name] = InputField(field_rect)
            y_offset += 60

        self.submit_button_rect.bottomleft = (self.rect.x + 10, self.rect.bottom - 10)
        self.back_button_rect.topright = (self.rect.right - 10, self.rect.y + 5)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active_field = None
            for field in self.fields.values():
                field.handle_event(event)
                if field.active:
                    self.active_field = field
            for field in self.fields.values():
                if field is not self.active_field:
                    field.active = False
        if self.active_field:
            self.active_field.handle_event(event)

    def get_arguments_string(self) -> str:
        """Returns a formatted JSON string of arguments, converting types."""
        args = {}
        for name, field in self.fields.items():
            val_str = field.text.strip()
            try:
                args[name] = json.loads(val_str)
            except json.JSONDecodeError:
                args[name] = val_str
        return json.dumps(args)

    def render(self, screen: pygame.Surface):
        tool_name = self.tool.get("function", {}).get("name", "")
        name_surf = FONT_L.render(f"Tool: {tool_name}", True, COLOR_TOOL_NAME)
        screen.blit(name_surf, (self.rect.x + 10, self.rect.y + 10))

        y_offset = 50
        for name, label_surf in self.labels.items():
            screen.blit(label_surf, (self.rect.x + 10, self.rect.y + y_offset))
            self.fields[name].render(screen)
            y_offset += 60

        mouse_pos = pygame.mouse.get_pos()
        for btn_rect, text in [
            (self.submit_button_rect, "Use Tool"),
            (self.back_button_rect, "Back to Text"),
        ]:
            hover = btn_rect.collidepoint(mouse_pos)
            btn_color = COLOR_BUTTON_HOVER if hover else COLOR_BUTTON
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=5)
            text_surf = FONT_BOLD.render(text, True, COLOR_TEXT)
            text_rect = text_surf.get_rect(center=btn_rect.center)
            screen.blit(text_surf, text_rect)


class PygameInterface:
    """Main interface class managing the GUI window, panels, and event loop."""

    def __init__(self, messages: List[Dict], tools: List[Dict]):
        os.environ["SDL_VIDEO_WINDOW_POS"] = "50,50"
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.display.set_caption("Minecraft Trajectory Recording Interface")
        self.clock = pygame.time.Clock()

        # Layout Rectangles
        conv_rect = pygame.Rect(0, 0, int(WIN_WIDTH * 0.6), WIN_HEIGHT)
        tools_rect = pygame.Rect(
            int(WIN_WIDTH * 0.6), 0, int(WIN_WIDTH * 0.4), int(WIN_HEIGHT * 0.5)
        )
        self.input_area_rect = pygame.Rect(
            int(WIN_WIDTH * 0.6),
            int(WIN_HEIGHT * 0.5),
            int(WIN_WIDTH * 0.4),
            int(WIN_HEIGHT * 0.5),
        )

        self.conv_panel = ConversationPanel(conv_rect, messages)
        self.tools_panel = ToolsPanel(tools_rect, tools)

        # Input State
        self.input_mode = "text"  # 'text' or 'tool'
        self.text_input_field = InputField(
            pygame.Rect(
                self.input_area_rect.x + 10,
                self.input_area_rect.y + 10,
                self.input_area_rect.width - 20,
                40,
            )
        )
        self.text_input_field.active = True
        self.tool_form: Optional[ToolArgumentForm] = None
        self.submit_text_button_rect = pygame.Rect(
            self.input_area_rect.x + 10, self.input_area_rect.bottom - 40, 150, 30
        )

        # NEW: Recording state for trajectory recording
        self.recording = False
        self.current_chain = None
        self.tool_mapping = {}  # Store tool mapping for direct execution
        self.mode = "chat"  # "chat" or "controller"

        # NEW: Controller state
        self.continuous_movement = {"w": False, "a": False, "s": False, "d": False}
        self.movement_timer = 0
        self.last_tool_time = 0

        self.response: Optional[str] = None
        self.running = True

    def get_response(self) -> str:
        """Main event loop that runs until a response is submitted."""
        while self.running and self.response is None:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(FPS)

        pygame.quit()
        return self.response or "exit"

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.response = "exit"

            # NEW: Recording controls (work in both modes)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    self.start_recording()
                elif event.key == pygame.K_F6:
                    self.stop_recording()
                elif event.key == pygame.K_F7:
                    self.toggle_mode()  # Switch between chat and controller

                # NEW: Minecraft controls (only in controller mode)
                if self.mode == "controller":
                    self.handle_minecraft_controls(event)

            # Handle key releases for continuous movement
            if event.type == pygame.KEYUP and self.mode == "controller":
                self.handle_movement_release(event)

            self.conv_panel.handle_event(event)

            # Only handle tool selection in chat mode
            if self.mode == "chat":
                selected_tool = self.tools_panel.handle_event(event)
                if selected_tool:
                    self.input_mode = "tool"
                    self.tool_form = ToolArgumentForm(
                        self.input_area_rect, selected_tool
                    )
                    self.text_input_field.active = False
                    if self.tool_form.fields:
                        first_field = next(iter(self.tool_form.fields.values()))
                        first_field.active = True
                        self.tool_form.active_field = first_field

                if self.input_mode == "text":
                    self.text_input_field.handle_event(event)
                    if (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and self.submit_text_button_rect.collidepoint(event.pos)
                    ):
                        self.response = self.text_input_field.text

                elif self.input_mode == "tool" and self.tool_form:
                    self.tool_form.handle_event(event)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.tool_form.back_button_rect.collidepoint(event.pos):
                            self.input_mode = "text"
                            self.tool_form = None
                            self.text_input_field.active = True
                        elif self.tool_form.submit_button_rect.collidepoint(event.pos):
                            tool_name = self.tool_form.tool.get("function", {}).get(
                                "name"
                            )
                            args_json = self.tool_form.get_arguments_string()
                            self.response = f"TOOL:{tool_name}:{args_json}"

    def _update(self):
        if self.input_mode == "text":
            self.text_input_field.update()
        elif self.input_mode == "tool" and self.tool_form:
            for field in self.tool_form.fields.values():
                field.update()

    def _render(self):
        self.screen.fill(COLOR_BG)

        # Show mode indicator
        mode_color = COLOR_TOOL_NAME if self.mode == "controller" else COLOR_TEXT
        mode_text = f"Mode: {self.mode.upper()}"
        mode_surf = FONT_BOLD.render(mode_text, True, mode_color)
        self.screen.blit(mode_surf, (10, 10))

        # Show recording status
        if self.recording:
            rec_text = "🎬 RECORDING"
            rec_color = (255, 100, 100)  # Red
        else:
            rec_text = "⏹️ NOT RECORDING"
            rec_color = COLOR_TEXT_DIM

        rec_surf = FONT_BOLD.render(rec_text, True, rec_color)
        self.screen.blit(rec_surf, (10, 40))

        if self.mode == "controller":
            self._render_controller_ui()
        else:
            self._render_chat_ui()

        pygame.display.flip()

    def _render_controller_ui(self):
        """Render controller-specific UI"""
        # Show controls
        controls = [
            "F5: Start Recording | F6: Stop Recording | F7: Switch to Chat",
            "",
            "MINECRAFT CONTROLS:",
            "Arrow Keys: Look around (45° / 30° increments)",
            "W: Walk forward (1 second)",
            "Z: Left Click | X: Right Click",
            "Space: Wait (0.5 seconds)",
            "",
            "ESC: Exit",
        ]

        y_offset = 100
        for control in controls:
            if control == "":
                y_offset += 10
                continue

            color = (
                COLOR_TOOL_NAME
                if ":" in control and not control.startswith("F")
                else COLOR_TEXT
            )
            control_surf = FONT_M.render(control, True, color)
            self.screen.blit(control_surf, (10, y_offset))
            y_offset += 25

        # Show current recording chain info
        if self.current_chain and self.recording:
            tool_count = sum(1 for msg in self.current_chain.messages if msg.tool_calls)
            chain_info = f"Current recording: {tool_count} tool calls"
            chain_surf = FONT_M.render(chain_info, True, COLOR_TEXT)
            self.screen.blit(chain_surf, (10, y_offset + 20))

    def _render_chat_ui(self):
        """Render existing chat UI"""
        self.conv_panel.render(self.screen)
        self.tools_panel.render(self.screen)

        pygame.draw.rect(self.screen, COLOR_PANEL_BG, self.input_area_rect)
        pygame.draw.rect(self.screen, COLOR_BORDER, self.input_area_rect, 2)

        if self.input_mode == "text":
            self.text_input_field.render(self.screen)
            mouse_pos = pygame.mouse.get_pos()
            hover = self.submit_text_button_rect.collidepoint(mouse_pos)
            btn_color = COLOR_BUTTON_HOVER if hover else COLOR_BUTTON
            pygame.draw.rect(
                self.screen, btn_color, self.submit_text_button_rect, border_radius=5
            )
            text_surf = FONT_BOLD.render("Send Response", True, COLOR_TEXT)
            text_rect = text_surf.get_rect(center=self.submit_text_button_rect.center)
            self.screen.blit(text_surf, text_rect)

        elif self.input_mode == "tool" and self.tool_form:
            self.tool_form.render(self.screen)

    def handle_minecraft_controls(self, event):
        """Handle discrete Minecraft control inputs"""
        import time

        current_time = time.time()

        # Discrete look commands
        if event.key == pygame.K_RIGHT:
            self.execute_tool_direct("lookAngle", {"xAngle": 45, "yAngle": 0})
        elif event.key == pygame.K_LEFT:
            self.execute_tool_direct("lookAngle", {"xAngle": -45, "yAngle": 0})
        elif event.key == pygame.K_UP:
            self.execute_tool_direct("lookAngle", {"xAngle": 0, "yAngle": -30})
        elif event.key == pygame.K_DOWN:
            self.execute_tool_direct("lookAngle", {"xAngle": 0, "yAngle": 30})

        # Discrete walk commands
        elif event.key == pygame.K_w:
            self.execute_tool_direct("walk", {"duration": 1000})

        # Mouse actions
        elif event.key == pygame.K_z:  # Left click
            self.execute_tool_direct("leftClick", {"duration": "medium"})
        elif event.key == pygame.K_x:  # Right click
            self.execute_tool_direct("rightClick", {"duration": "medium"})

        # Wait command
        elif event.key == pygame.K_SPACE:
            self.execute_tool_direct("wait", {"duration": 500})

    def handle_movement_release(self, event):
        """Handle key releases for continuous movement (placeholder for future use)"""
        pass

    def execute_tool_direct(self, tool_name: str, arguments: dict):
        """Execute a tool directly and add to recording chain"""
        import time
        import json

        if not self.recording:
            print(f"Not recording - tool {tool_name} not saved")
            return

        if not self.current_chain:
            print("No recording chain active")
            return

        # Create tool call format (same as existing system)
        tool_call_id = f"call_{tool_name}_{int(time.time() * 1000)}"

        # Add assistant message with tool call
        self.current_chain = self.current_chain.bot(
            content=f"Executing {tool_name}",
            tool_calls=[
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {"name": tool_name, "arguments": json.dumps(arguments)},
                }
            ],
        )

        # Add tool result (mock for now - real execution would happen here)
        self.current_chain = self.current_chain.tool(
            content=f"Executed {tool_name} with {arguments}",
            tool_call_id=tool_call_id,
            name=tool_name,
        )

        print(f"Recorded: {tool_name}({arguments})")

    def start_recording(self):
        """Start trajectory recording"""
        if self.recording:
            print("Already recording!")
            return

        # Create new conversation chain
        self.current_chain = OpenAIAsyncMessageChain(model_name="trajectory-recording")
        self.current_chain = self.current_chain.system("Trajectory recording session")
        self.current_chain = self.current_chain.user(
            "Starting Minecraft trajectory recording"
        )

        self.recording = True
        print("🎬 Started recording trajectory")

    def stop_recording(self):
        """Stop trajectory recording and save"""
        import time

        if not self.recording:
            print("Not recording!")
            return

        if not self.current_chain:
            print("No recording chain!")
            return

        # Save trajectory
        timestamp = int(time.time())
        filename = f"trajectory_{timestamp}.json"

        try:
            with open(filename, "w") as f:
                f.write(self.current_chain.to_json())
            print(f"💾 Saved trajectory: {filename}")

            # Show trajectory stats
            tool_calls = 0
            for msg in self.current_chain.messages:
                if msg.tool_calls:
                    tool_calls += len(msg.tool_calls)
            print(f"📊 Recorded {tool_calls} tool calls")

        except Exception as e:
            print(f"❌ Error saving trajectory: {e}")

        self.recording = False
        self.current_chain = None

    def toggle_mode(self):
        """Toggle between chat and controller mode"""
        if self.mode == "chat":
            self.mode = "controller"
            print("🎮 Switched to Controller Mode")
        else:
            self.mode = "chat"
            print("💬 Switched to Chat Mode")

    def cleanup(self):
        """Clean up pygame resources"""
        try:
            pygame.quit()
        except:
            pass  # Ignore errors during cleanup


