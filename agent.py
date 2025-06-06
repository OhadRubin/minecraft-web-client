from dataclasses import dataclass, field, replace
import json
from typing import List, Dict, Union, Any, Optional, Tuple, Type
from openai import AsyncOpenAI
from functools import wraps
import inspect
import os
import base64
import httpx
import mimetypes
from pydantic import BaseModel
import argparse
import asyncio
import sys
from dataclasses import dataclass


import asyncio
import json
import logging
import os
import shutil
from contextlib import AsyncExitStack
from typing import Any
from dataclasses import dataclass

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


import pygame
import json
import os
import textwrap
from typing import Dict, List, Any, Optional, Tuple

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


class Configuration:
    """Manages configuration and environment variables for the MCP client."""

    def __init__(self) -> None:
        """Initialize configuration with environment variables."""
        self.load_env()
        self.api_key = os.getenv("OPENROUTER_API_KEY")

    @staticmethod
    def load_env() -> None:
        """Load environment variables from .env file."""
        load_dotenv()

    @staticmethod
    def load_config(file_path: str) -> dict[str, Any]:
        """Load server configuration from JSON file.

        Args:
            file_path: Path to the JSON configuration file.

        Returns:
            Dict containing server configuration.

        Raises:
            FileNotFoundError: If configuration file doesn't exist.
            JSONDecodeError: If configuration file is invalid JSON.
        """
        with open(file_path, "r") as f:
            return json.load(f)

    @property
    def llm_api_key(self) -> str:
        """Get the LLM API key.

        Returns:
            The API key as a string.

        Raises:
            ValueError: If the API key is not found in environment variables.
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        return self.api_key


class Server:
    """Manages MCP server connections and tool execution."""

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name: str = name
        self.config: dict[str, Any] = config
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    async def initialize(self) -> None:
        """Initialize the server connection."""
        command = (
            shutil.which("npx")
            if self.config["command"] == "npx"
            else self.config["command"]
        )
        if command is None:
            raise ValueError("The command must be a valid string and cannot be None.")

        server_params = StdioServerParameters(
            command=command,
            args=self.config["args"],
            env=(
                {**os.environ, **self.config["env"]} if self.config.get("env") else None
            ),
        )
        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.session = session
        except Exception as e:
            logging.error(f"Error initializing server {self.name}: {e}")
            await self.cleanup()
            raise

    async def list_tools(self) -> list[Any]:
        """List available tools from the server.

        Returns:
            A list of available tools.

        Raises:
            RuntimeError: If the server is not initialized.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                tools.extend(
                    Tool(tool.name, tool.description, tool.inputSchema)
                    for tool in item[1]
                )

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """Execute a tool with retry mechanism.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Tool arguments.
            retries: Number of retry attempts.
            delay: Delay between retries in seconds.

        Returns:
            Tool execution result.

        Raises:
            RuntimeError: If server is not initialized.
            Exception: If tool execution fails after all retries.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        attempt = 0
        while attempt < retries:
            try:
                logging.info(f"Executing {tool_name}...")
                result = await self.session.call_tool(tool_name, arguments)

                return result

            except Exception as e:
                attempt += 1
                logging.warning(
                    f"Error executing tool: {e}. Attempt {attempt} of {retries}."
                )
                if attempt < retries:
                    logging.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logging.error("Max retries reached. Failing.")
                    raise

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                self.stdio_context = None
            except Exception as e:
                logging.error(f"Error during cleanup of server {self.name}: {e}")


class Tool:
    """Represents a tool with its properties and formatting."""

    def __init__(
        self, name: str, description: str, input_schema: dict[str, Any]
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema: dict[str, Any] = input_schema

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert tool to OpenAI function schema format.

        Returns:
            A dictionary in OpenAI function schema format.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


async def create_tool_functions(servers: list[Server]) -> tuple[list[dict], dict]:
    tool_schemas = []
    tool_mapping = {}

    for server in servers:
        tools = await server.list_tools()
        for tool in tools:
            # Create the schema
            tool_schemas.append(tool.to_openai_schema())

            # Create a proper async tool function that calls MCP directly
            def make_tool_function(srv, tool_name):
                async def tool_function(**kwargs):
                    try:
                        result = await srv.execute_tool(tool_name, kwargs)

                        # Handle CallToolResult properly - preserve multimodal content
                        if hasattr(result, "content"):
                            if (
                                isinstance(result.content, list)
                                and len(result.content) > 0
                            ):
                                # Return the full content list to preserve multimodal data
                                return {
                                    "content": [
                                        {
                                            "type": getattr(item, "type", "text"),
                                            "text": getattr(item, "text", None),
                                            "data": getattr(item, "data", None),
                                            "mimeType": getattr(item, "mimeType", None),
                                        }
                                        for item in result.content
                                    ]
                                }
                            else:
                                return str(result.content)
                        else:
                            return str(result)
                    except Exception as e:
                        return f"Error executing tool {tool_name}: {str(e)}"

                return tool_function

            tool_mapping[tool.name] = make_tool_function(server, tool.name)

    return tool_schemas, tool_mapping


async def encode_base64_content_from_url(content_url: str) -> str:
    """Asynchronously fetch content from a URL and encode it in base64."""

    async with httpx.AsyncClient() as client:
        response = await client.get(content_url)
        response.raise_for_status()
        result = base64.b64encode(response.content).decode("utf-8")

    return result


async def _resolve_multimodal_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """Convert any URL fields in tool arguments to base64-encoded strings."""

    resolved = {}
    for key, value in args.items():
        if isinstance(value, list):
            resolved[key] = [
                (
                    await encode_base64_content_from_url(v)
                    if isinstance(v, str) and v.startswith("http")
                    else v
                )
                for v in value
            ]
        elif isinstance(value, str) and value.startswith("http"):
            resolved[key] = await encode_base64_content_from_url(value)
        else:
            resolved[key] = value
    return resolved


async def _encode_to_data_uri(source: str, mime_type: Optional[str] = None) -> str:
    """Encode a local file or remote URL to a base64 data URI."""

    if source.startswith("http"):
        async with httpx.AsyncClient() as client:
            response = await client.get(source)
            response.raise_for_status()
            content = response.content
            if not mime_type:
                mime_type = response.headers.get("content-type")
    else:
        with open(source, "rb") as f:
            content = f.read()
        if not mime_type:
            mime_type = mimetypes.guess_type(source)[0]

    mime_type = mime_type or "application/octet-stream"
    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


async def _resolve_multimodal_output(output: Any) -> Any:
    """Convert MCP multimodal content to OpenAI message format."""

    if isinstance(output, dict) and "content" in output:
        # Handle MCP multimodal content structure
        content_items = output["content"]

        # If there's only text content, return just the text
        text_items = [item for item in content_items if item.get("type") == "text"]
        image_items = [item for item in content_items if item.get("type") == "image"]

        if len(content_items) == 1 and content_items[0].get("type") == "text":
            return content_items[0].get("text", "")

        # For multimodal content, we'll return structured data that the chain can handle
        result = []

        for item in content_items:
            if item.get("type") == "text" and item.get("text"):
                result.append({"type": "text", "text": item["text"]})
            elif item.get("type") == "image" and item.get("data"):
                # Convert to OpenAI format
                mime_type = item.get("mimeType", "image/png")
                data_uri = f"data:{mime_type};base64,{item['data']}"
                result.append({"type": "image_url", "image_url": {"url": data_uri}})

        return {"multimodal_content": result}

    elif isinstance(output, str):
        if output.startswith("http") or os.path.exists(output):
            return await _encode_to_data_uri(output)
        return output
    elif isinstance(output, list):
        return [await _resolve_multimodal_output(v) for v in output]
    elif isinstance(output, dict):
        return {k: await _resolve_multimodal_output(v) for k, v in output.items()}
    else:
        return output


def chain_method(func):
    """Decorator to convert a function into a chainable method that supports
    both synchronous and asynchronous functions."""

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            return await func(self, *args, **kwargs)

        return async_wrapper
    else:

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        return wrapper


@dataclass(frozen=True)
class Message:
    role: str
    content: Optional[Union[str, List[Dict[str, str]]]] = None
    tool_calls: Optional[List[Any]] = (
        None  # Can store OpenAI's ToolCall objects or dicts
    )
    tool_call_id: Optional[str] = None  # For role 'tool'
    name: Optional[str] = None  # For tool messages to specify function name
    should_cache: bool = False


USE_LM = os.environ.get("USE_LM", "False").lower() == "true"


class MockUsage:
    """Mock usage object for MockResponse."""

    def __init__(self, prompt_tokens: int, completion_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens


class MockFunction:
    """Mock function object for tool calls."""

    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class MockToolCall:
    """Mock tool call object."""

    def __init__(self, tool_name: str, arguments: dict):
        self.id = f"call_{tool_name}_{hash(str(arguments)) % 10000}"
        self.type = "function"
        self.function = MockFunction(tool_name, json.dumps(arguments))


class MockMessage:
    """Mock message object that mimics OpenAI message structure."""

    def __init__(self, content: str, tool_calls: list = None):
        self.content = content
        self.tool_calls = tool_calls or []


class MockChoice:
    """Mock choice object for MockResponse."""

    def __init__(self, message: MockMessage):
        self.message = message


class MockResponse:
    """Mock response object that mimics OpenAI response structure."""

    def __init__(self, **api_params):
        self.api_params = api_params
        msgs = api_params.get("messages", [])
        tools = api_params.get("tools", [])

        # Print the conversation context for the user to see
        print("\n" + "=" * 50)
        print("CONVERSATION CONTEXT:")
        print("=" * 50)
        for message in msgs:
            role = message["role"].upper()
            content = message.get("content", "")
            if isinstance(content, list):
                # Handle multimodal content
                text_parts = [
                    item.get("text", "")
                    for item in content
                    if item.get("type") == "text"
                ]
                content = " ".join(text_parts)
            print(f"{role}: {content}")
        print("=" * 50)

        if tools:
            print("\nAVAILABLE TOOLS:")
            for tool in tools:
                tool_name = tool["function"]["name"]
                tool_desc = tool["function"]["description"]
                print(f"- {tool_name}: {tool_desc}")
            print("=" * 50)

        # Get response from stdin
        print(
            "\nEnter your response as the assistant (or 'TOOL:tool_name:arguments_json' to call a tool):"
        )
        user_response = input().strip()

        # Check if user wants to make a tool call
        if user_response.startswith("TOOL:"):
            # Parse tool call format: TOOL:tool_name:arguments_json
            parts = user_response.split(":", 2)
            if len(parts) >= 3:
                tool_name = parts[1]
                try:
                    tool_args = json.loads(parts[2]) if parts[2] else {}
                except json.JSONDecodeError:
                    tool_args = {}

                tool_call = MockToolCall(tool_name, tool_args)
                message = MockMessage(f"I'll use the {tool_name} tool.", [tool_call])
            else:
                # Invalid tool format, treat as regular response
                message = MockMessage(user_response, [])
        else:
            # Regular text response
            message = MockMessage(user_response, [])

        # Create mock usage metrics
        prompt_tokens = len(str(msgs)) // 4  # Rough estimate
        completion_tokens = len(message.content) // 4  # Rough estimate

        self.usage = MockUsage(prompt_tokens, completion_tokens)
        self.choices = [MockChoice(message)]


@dataclass(frozen=True)
class OpenAIAsyncMessageChain:
    model_name: str = "gpt-4o"
    messages: Tuple[Message] = field(default_factory=tuple)
    system_prompt: Any = None  # Changed from anthropic.NOT_GIVEN
    cache_system: bool = False
    metric_list: List[Dict[str, Any]] = field(default_factory=tuple)
    response_list: List[Any] = field(default_factory=tuple)
    verbose: bool = False
    response_format: Optional[Any] = None
    tools_list: Optional[List[Any]] = None
    tools_mapping: Optional[Dict[str, Any]] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    persistent_interface: Optional[Any] = None  # For trajectory recording

    @chain_method
    def quiet(self):
        self = replace(self, verbose=False)
        return self

    @chain_method
    def verbose(self):
        self = replace(self, verbose=True)
        return self

    @chain_method
    def add_message(
        self,
        role: str,
        content: Optional[Union[str, List[Dict[str, Any]], BaseModel]] = None,
        tool_calls: Optional[List[Any]] = None,
        tool_call_id: Optional[str] = None,
        name: Optional[str] = None,
        should_cache: bool = False,
    ):
        assert (
            not should_cache
        ), "OpenAI does not support caching for individual messages in this way"
        # Ensure content is not assigned if it's meant to be None (e.g. assistant message with only tool_calls)
        msg = Message(
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            name=name,
            should_cache=should_cache,
        )
        return replace(self, messages=self.messages + (msg,))

    @chain_method
    def user(
        self, content: Union[str, List[Dict[str, str]]], should_cache: bool = False
    ):
        return self.add_message(role="user", content=content, should_cache=should_cache)

    @chain_method
    def user_image_url(self, prompt: str, image_urls: List[str]):
        """Send a user message with a text prompt and one or more image URLs."""
        content = [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": url}} for url in image_urls
        ]
        return self.user(content)

    @chain_method
    async def user_image_base64(self, prompt: str, image_urls: List[str]):
        """Send a user message with image content encoded in base64."""
        encoded_images = [
            await encode_base64_content_from_url(url) for url in image_urls
        ]
        content = [{"type": "text", "text": prompt}] + [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img}"},
            }
            for img in encoded_images
        ]
        return self.user(content)

    @chain_method
    async def user_image_file(self, prompt: str, image_paths: List[str]):
        """Send a user message with local image files encoded as base64 data URIs."""
        encoded_images = [await _encode_to_data_uri(path) for path in image_paths]
        content = [{"type": "text", "text": prompt}] + [
            {
                "type": "image_url",
                "image_url": {"url": data_uri},
            }
            for data_uri in encoded_images
        ]
        return self.user(content)

    @chain_method
    def user_audio_url(self, prompt: str, audio_urls: List[str]):
        """Send a user message with a text prompt and one or more audio URLs."""
        content = [{"type": "text", "text": prompt}] + [
            {"type": "audio_url", "audio_url": {"url": url}} for url in audio_urls
        ]
        return self.user(content)

    @chain_method
    async def user_audio_base64(
        self, prompt: str, audio_urls: List[str], mime_type: str = "audio/ogg"
    ):
        """Send a user message with audio content encoded in base64."""
        encoded_audio = [
            await encode_base64_content_from_url(url) for url in audio_urls
        ]
        content = [{"type": "text", "text": prompt}] + [
            {
                "type": "audio_url",
                "audio_url": {"url": f"data:{mime_type};base64,{audio}"},
            }
            for audio in encoded_audio
        ]
        return self.user(content)

    @chain_method
    def bot(
        self,
        content: Optional[Union[str, List[Dict[str, Any]], BaseModel]] = None,
        tool_calls: Optional[List[Any]] = None,
        should_cache: bool = False,
    ):
        return self.add_message(
            role="assistant",
            content=content,
            tool_calls=tool_calls,
            should_cache=should_cache,
        )

    @chain_method
    def tool(
        self,
        content: str,
        tool_call_id: str,
        name: Optional[str] = None,
        should_cache: bool = False,
    ):  # content for tool is stringified result
        return self.add_message(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            should_cache=should_cache,
        )

    @chain_method
    def system(self, content: str, should_cache: bool = False):
        self = replace(self, system_prompt=content, cache_system=should_cache)
        return self

    @chain_method
    def with_structure(self, response_format: Type[BaseModel]):
        """Set a Pydantic model as the expected response format."""
        self = replace(self, response_format=response_format)
        return self

    @chain_method
    def with_tools(self, tools_list: List, tools_mapping: Dict[str, Any]):
        """Set a Pydantic model as the expected response format."""
        self = replace(self, tools_list=tools_list, tools_mapping=tools_mapping)
        return self

    def serialize(self) -> list:
        output = []
        if self.system_prompt is not None:
            output.append({"role": "system", "content": self.system_prompt})

        for m in self.messages:
            msg_dict = {"role": m.role}

            # Add content if it exists
            if m.content is not None:
                msg_dict["content"] = m.content

            # Add tool_calls for assistant messages
            if m.role == "assistant" and m.tool_calls is not None:
                msg_dict["tool_calls"] = m.tool_calls

            # Add tool_call_id for tool messages
            if m.role == "tool" and m.tool_call_id is not None:
                msg_dict["tool_call_id"] = m.tool_call_id

            # Add name for tool messages
            if m.role == "tool" and m.name is not None:
                msg_dict["name"] = m.name

            output.append(msg_dict)

        return output

    @staticmethod
    def parse_metrics(resp):
        try:
            return dict(
                input_tokens=resp.usage.prompt_tokens,
                output_tokens=resp.usage.completion_tokens,
                total_tokens=resp.usage.total_tokens,
                input_tokens_cache_read=0,  # OpenAI doesn't have cache metrics
                input_tokens_cache_create=0,
            )
        except Exception as e:
            print(f"Error parsing metrics: {e}")
            return dict(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                input_tokens_cache_read=0,  # OpenAI doesn't have cache metrics
                input_tokens_cache_create=0,
            )

    @chain_method
    async def generate(self):
        while True:
            if self.base_url == "https://openrouter.ai/api/v1":
                client = AsyncOpenAI(
                    base_url=self.base_url, api_key=os.getenv("OPENROUTER_API_KEY")
                )
            elif self.base_url is not None:
                client = AsyncOpenAI(
                    base_url=self.base_url, api_key="lm-studio"
                )  # Or a configurable key for other base URLs
            else:
                client = AsyncOpenAI()
            msgs = self.serialize()

            # Prepare common parameters
            api_params = {
                "model": self.model_name,
                "messages": msgs,
                "max_tokens": self.max_tokens,
                "temperature": 1.0,
            }

            # Only add tools if they exist
            if self.tools_list is not None:
                api_params["tools"] = self.tools_list
            if USE_LM:

                response = await client.chat.completions.create(**api_params)
            else:
                # Use persistent PygameInterface if available, otherwise create new one
                if hasattr(self, "persistent_interface") and self.persistent_interface:
                    # Use the persistent interface (for trajectory recording)
                    interface = self.persistent_interface
                    # Update interface with current messages for display
                    interface.conv_panel.messages = msgs
                    interface.conv_panel._render_messages()
                    user_response = interface.get_response()
                else:
                    # Fallback: create new interface (old behavior)
                    interface = PygameInterface(msgs, self.tools_list or [])
                    interface.tool_mapping = (
                        self.tools_mapping or {}
                    )  # Pass tool mapping for trajectory recording
                    user_response = interface.get_response()

                # Handle tool responses from PygameInterface
                if user_response.startswith("TOOL:"):
                    # Parse tool response: "TOOL:tool_name:arguments_json"
                    parts = user_response.split(":", 2)
                    if len(parts) == 3:
                        tool_name = parts[1]
                        args_json = parts[2]

                        # Create a mock response with tool calls
                        response = MockResponse(
                            content=f"Using tool {tool_name}",
                            tool_calls=[MockToolCall(tool_name, json.loads(args_json))],
                        )
                    else:
                        response = MockResponse(content=user_response)
                else:
                    response = MockResponse(content=user_response)

            msg = response.choices[0].message
            resp = msg.content

            self = replace(
                self,
                metric_list=self.metric_list + (self.parse_metrics(response),),
                response_list=self.response_list + (resp,),
            )

            # Check if the assistant made tool calls
            if msg.tool_calls and len(msg.tool_calls) > 0:
                # Add the assistant message with tool calls to the conversation
                self = self.bot(content=msg.content, tool_calls=msg.tool_calls)
                print(f"Bot (thinking): {msg.content}")

                # Execute each tool call and add the results
                for tool_call in msg.tool_calls:
                    print(f"Tool call: {tool_call}")
                    tool_name = tool_call.function.name

                    tool_args = json.loads(tool_call.function.arguments)
                    tool_args = await _resolve_multimodal_args(tool_args)

                    # Execute the tool function
                    if self.tools_mapping and tool_name in self.tools_mapping:

                        tool_response = await self.tools_mapping[tool_name](**tool_args)
                        tool_response = await _resolve_multimodal_output(tool_response)

                        # Handle multimodal content specially
                        if (
                            isinstance(tool_response, dict)
                            and "multimodal_content" in tool_response
                        ):
                            # Add multimodal content as a user message so the LLM can see images
                            multimodal_content = tool_response["multimodal_content"]
                            print("Tool response contained multimodal content")

                            # Add tool result as text first
                            text_parts = [
                                item["text"]
                                for item in multimodal_content
                                if item.get("type") == "text"
                            ]
                            tool_text = (
                                " ".join(text_parts)
                                if text_parts
                                else f"Tool {tool_name} executed successfully"
                            )
                            print(tool_text)

                            self = self.tool(
                                content=tool_text,
                                tool_call_id=tool_call.id,
                                name=tool_name,
                            )

                            # Then add the multimodal content as a user message
                            if any(
                                item.get("type") == "image_url"
                                for item in multimodal_content
                            ):
                                user_prompt = f"Here's the result from {tool_name}:"
                                self = self.user(
                                    [{"type": "text", "text": user_prompt}]
                                    + multimodal_content
                                )
                        else:
                            # Convert tool response to string for the API
                            tool_response_str = (
                                json.dumps(tool_response)
                                if not isinstance(tool_response, str)
                                else tool_response
                            )
                            print(f"Tool response: {tool_response_str}")

                            # Add tool result with proper tool_call_id and function name
                            self = self.tool(
                                content=tool_response_str,
                                tool_call_id=tool_call.id,
                                name=tool_name,
                            )
                    else:
                        # Handle case where tool is not found
                        error_msg = f"Tool '{tool_name}' not found in tools_mapping"
                        self = self.tool(
                            content=error_msg, tool_call_id=tool_call.id, name=tool_name
                        )
            else:
                # No tool calls, we're done
                break

        return self

    # genrates and appends the last assistant message into the chain
    @chain_method
    async def generate_bot(self):
        self = await self.generate()
        self = self.bot(self.response_list[-1])
        return self

    @chain_method
    def emit_last(self):
        return self, self.response_list[-1], self.metric_list[-1]

    @chain_method
    def print_last(self, response=None, metrics=None, mode="response_all"):
        if mode == "response_all":
            if response is None:
                response = self.last_response
                metrics = self.last_metrics
            print(f"{response=}")
            print(f"{metrics=}")
        if mode == "full_completion":
            response = self.last_full_completion
            print(f"{response=}")

        return self

    @property
    def last_response(self):
        return self.response_list[-1]

    @property
    def last_metrics(self):
        return self.metric_list[-1]

    @property
    def last_full_completion(self):
        rev_messages = self.messages[::-1]
        output = []
        for msg in rev_messages:
            if msg.role == "user":
                break
            output.append(msg.content)
        return "".join(output[::-1])

    @chain_method
    def apply(self, func):
        func(self)
        return self

    @chain_method
    def map(self, func):
        return self.apply(func)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary, excluding non-serializable fields."""
        import json

        def is_json_serializable(obj):
            """Check if an object is JSON serializable."""
            try:
                json.dumps(obj)
                return True
            except (TypeError, ValueError):
                return False

        # Convert messages to serializable format
        serialized_messages = []
        for msg in self.messages:
            msg_dict = {
                "role": msg.role,
                "tool_call_id": msg.tool_call_id,
                "name": msg.name,
                "should_cache": msg.should_cache,
            }

            # Handle content carefully - only include if serializable
            if msg.content is not None and is_json_serializable(msg.content):
                msg_dict["content"] = msg.content
            else:
                msg_dict["content"] = None

            # Convert tool_calls to serializable format (dict instead of ToolCall objects)
            if msg.tool_calls:
                msg_dict["tool_calls"] = []
                for tool_call in msg.tool_calls:
                    if hasattr(tool_call, "model_dump"):  # Pydantic object
                        msg_dict["tool_calls"].append(tool_call.model_dump())
                    elif hasattr(tool_call, "dict"):  # Older pydantic
                        msg_dict["tool_calls"].append(tool_call.dict())
                    elif isinstance(tool_call, dict):
                        msg_dict["tool_calls"].append(tool_call)
                    else:
                        # Convert OpenAI ToolCall object to dict manually
                        msg_dict["tool_calls"].append(
                            {
                                "id": getattr(tool_call, "id", None),
                                "type": getattr(tool_call, "type", "function"),
                                "function": {
                                    "name": (
                                        getattr(tool_call.function, "name", "")
                                        if hasattr(tool_call, "function")
                                        else ""
                                    ),
                                    "arguments": (
                                        getattr(tool_call.function, "arguments", "{}")
                                        if hasattr(tool_call, "function")
                                        else "{}"
                                    ),
                                },
                            }
                        )
            else:
                msg_dict["tool_calls"] = None

            serialized_messages.append(msg_dict)

        # Only include serializable response_list items
        serializable_responses = []
        for response in self.response_list:
            if is_json_serializable(response):
                serializable_responses.append(response)
            else:
                # Convert to string representation for non-serializable objects
                serializable_responses.append(str(response))

        return {
            "model_name": self.model_name,
            "messages": serialized_messages,
            "system_prompt": (
                self.system_prompt
                if is_json_serializable(self.system_prompt)
                else str(self.system_prompt) if self.system_prompt is not None else None
            ),
            "cache_system": self.cache_system,
            "metric_list": list(self.metric_list),
            "response_list": serializable_responses,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            # Skip verbose, response_format and tools_mapping as they're not needed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OpenAIAsyncMessageChain":
        """Deserialize from dictionary."""
        # Convert messages back to Message objects
        messages = []
        for msg_data in data.get("messages", []):
            msg = Message(
                role=msg_data["role"],
                content=msg_data.get("content"),
                tool_calls=msg_data.get("tool_calls"),  # Keep as dicts
                tool_call_id=msg_data.get("tool_call_id"),
                name=msg_data.get("name"),
                should_cache=msg_data.get("should_cache", False),
            )
            messages.append(msg)

        return cls(
            model_name=data.get("model_name", "gpt-4o"),
            messages=tuple(messages),
            system_prompt=data.get("system_prompt"),
            cache_system=data.get("cache_system", False),
            metric_list=tuple(data.get("metric_list", [])),
            response_list=tuple(data.get("response_list", [])),
            verbose=data.get("verbose", False),
            base_url=data.get("base_url"),
            max_tokens=data.get("max_tokens", 4096),
            # response_format and tools_mapping will be None
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        import json

        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "OpenAIAsyncMessageChain":
        """Deserialize from JSON string."""
        import json

        return cls.from_dict(json.loads(json_str))


def test_chain1():
    chain1 = OpenAIAsyncMessageChain()
    chain1 = (
        chain1.user("Hello!")
        .bot("Hi there!")
        .user("How are you?")
        .generate()
        .print_last()
    )


def test_chain2():
    chain2 = OpenAIAsyncMessageChain()
    chain2 = (
        chain2.user("Come up with a name, respond with a single word")
        .bot("Donny")
        .user("Tell me a story about Donny")
        .generate()
        .print_last()
    )


def test_system():
    chain2 = OpenAIAsyncMessageChain()
    chain2 = (
        chain2.system("Answer in rhyming words")
        .user("Come up with a name, respond with a single word")
        .bot("Donny")
        .user("Tell me a story about Donny")
        .generate()
        .print_last()
    )

    # .bot("Hi there!")


def test_serialization():
    """Test that serialization and deserialization work correctly."""
    # Create a chain with various message types
    chain = OpenAIAsyncMessageChain(model_name="gpt-4o")
    chain = (
        chain.system("You are a helpful assistant")
        .user("Hello!")
        .bot("Hi there! How can I help you?")
        .user("What's 2+2?")
    )

    # Add some mock data to test serialization
    chain = replace(
        chain,
        response_list=("Hi there! How can I help you?", "2+2 equals 4"),
        metric_list=(
            {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            {"input_tokens": 8, "output_tokens": 3, "total_tokens": 11},
        ),
    )

    # Test serialization
    json_str = chain.to_json()
    print("Serialized chain:")
    print(json_str[:200] + "..." if len(json_str) > 200 else json_str)

    # Test deserialization
    restored_chain = OpenAIAsyncMessageChain.from_json(json_str)

    # Verify the data matches
    assert restored_chain.model_name == chain.model_name
    assert restored_chain.system_prompt == chain.system_prompt
    assert len(restored_chain.messages) == len(chain.messages)
    assert restored_chain.response_list == chain.response_list
    assert restored_chain.metric_list == chain.metric_list

    print("✅ Serialization test passed!")


def test_serialization_debug():
    """Debug serialization issues by testing each field individually."""
    import json

    # Create a minimal chain
    chain = OpenAIAsyncMessageChain(model_name="gpt-4o")
    chain = chain.system("Test").user("Hello")

    print("Testing individual fields:")

    # Test each field individually
    test_data = {
        "model_name": chain.model_name,
        "system_prompt": chain.system_prompt,
        "cache_system": chain.cache_system,
        "verbose": chain.verbose,
        "base_url": chain.base_url,
        "max_tokens": chain.max_tokens,
    }

    for key, value in test_data.items():
        try:
            json.dumps({key: value})
            print(f"✅ {key}: OK")
        except Exception as e:
            print(f"❌ {key}: {type(value)} - {e}")

    # Test messages
    try:
        messages_data = []
        for i, msg in enumerate(chain.messages):
            msg_dict = {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "tool_call_id": msg.tool_call_id,
                "name": msg.name,
                "should_cache": msg.should_cache,
            }
            try:
                json.dumps(msg_dict)
                print(f"✅ Message {i}: OK")
            except Exception as e:
                print(f"❌ Message {i}: {e}")
                # Test each field in the message
                for field, val in msg_dict.items():
                    try:
                        json.dumps({field: val})
                        print(f"  ✅ {field}: OK")
                    except Exception as fe:
                        print(f"  ❌ {field}: {type(val)} - {fe}")
    except Exception as e:
        print(f"❌ Messages: {e}")

    # Test tuples
    try:
        json.dumps(list(chain.metric_list))
        print("✅ metric_list: OK")
    except Exception as e:
        print(f"❌ metric_list: {e}")

    try:
        json.dumps(list(chain.response_list))
        print("✅ response_list: OK")
    except Exception as e:
        print(f"❌ response_list: {e}")


async def test_image_serialization():
    """Test image handling with serialization."""
    # Create initial chain with image
    chain = OpenAIAsyncMessageChain(model_name="gpt-4o")
    chain = await chain.user_image_file(
        "Describe this image in detail.",
        [
            "/Users/ohadr/chains/a_solid_black_silhouette_of_a_a_man_and_woman_holding_hands__-shading__sky_2061071959.png"
        ],
    )

    # Get initial description
    chain = await chain.generate_bot()
    print("\nInitial description:")
    print(chain.last_response)

    # Serialize the chain
    json_str = chain.to_json()
    print("\nSerialized chain (truncated):")
    print(json_str[:200] + "..." if len(json_str) > 200 else json_str)

    # Deserialize and ask follow-up
    restored_chain = OpenAIAsyncMessageChain.from_json(json_str)
    restored_chain = restored_chain.user(
        "What is the woman holding? Answer in one word."
    )
    restored_chain = await restored_chain.generate_bot()
    print("\nFollow-up answer about what she's holding:")
    print(restored_chain.last_response)

    # Ask about the type
    restored_chain = restored_chain.user("What type is it?")
    restored_chain = await restored_chain.generate_bot()
    print("\nFollow-up about the type:")
    print(restored_chain.last_response)

    print("\n✅ Image serialization test completed!")


def test_test_image_serialization_sync():
    import asyncio

    async def main():
        await test_image_serialization()

    asyncio.run(main())


# if __name__ == "__main__":


@dataclass
class ChatSessionConfig:
    """Configuration for chat session."""

    servers: list["Server"]
    api_key: str
    model_name: str = "google/gemini-flash-1.5"
    base_url: str = "https://openrouter.ai/api/v1"
    initial_message: str | None = None
    constant_msg: str | None = None


async def cleanup_servers(servers: list[Server]) -> None:
    """Clean up all servers properly."""
    for server in reversed(servers):
        try:
            await server.cleanup()
        except Exception as e:
            print(f"Warning during final cleanup: {e}")


async def initialize_servers(servers: list[Server]) -> bool:
    for server in servers:
        try:
            await server.initialize()
        except Exception as e:
            print(f"Failed to initialize server: {e}")
            await cleanup_servers(servers)
            return False
    return True


async def handle_interactive_session(
    chain: OpenAIAsyncMessageChain,
    initial_message: str | None = None,
    constant_msg: str | None = None,
) -> OpenAIAsyncMessageChain:
    # Create persistent PygameInterface for trajectory recording if USE_LM=False
    persistent_interface = None
    if not USE_LM:
        # Create a persistent interface that will be reused across generate() calls
        persistent_interface = PygameInterface([], chain.tools_list or [])
        persistent_interface.tool_mapping = chain.tools_mapping or {}

        # Store reference in chain for generate() method to use
        chain = replace(chain, persistent_interface=persistent_interface)
        print("🎮 Persistent PygameInterface created for trajectory recording")
        print("💡 Use F7 to switch to controller mode, F5/F6 to start/stop recording")

    # Send initial message if provided
    if initial_message:
        print(f"You: {initial_message}")
        chain = await chain.user(initial_message).generate_bot()
        print(f"Assistant: {chain.last_response}")

    print("Chat session started. Type 'quit' or 'exit' to end.")

    while True:
        try:
            if constant_msg is not None:
                user_input = constant_msg
            else:
                if USE_LM:
                    user_input = input("You: ").strip()
                    if user_input.lower() in ["quit", "exit"]:
                        print("\nExiting...")
                        break
                else:
                    # For PygameInterface mode, get input from the persistent interface
                    if persistent_interface:
                        user_input = persistent_interface.get_response()
                        if user_input == "exit":
                            print("\nExiting...")
                            break
                    else:
                        user_input = input("You: ").strip()
                        if user_input.lower() in ["quit", "exit"]:
                            print("\nExiting...")
                            break

            if not user_input:
                continue

            # Use the new async-aware method
            chain = await chain.user(user_input).generate_bot()
            print(f"Assistant: {chain.last_response}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error during interaction: {e}")
            continue

    # Clean up pygame interface
    if persistent_interface:
        persistent_interface.cleanup()

    return chain


async def run_chat_session(config: ChatSessionConfig) -> None:
    """Main chat session handler using functional paradigm.

    Args:
        config: Chat session configuration
    """
    try:
        # Initialize servers
        if not await initialize_servers(config.servers):
            return

        # Create tool functions and schemas
        tool_schemas, tool_mapping = await create_tool_functions(config.servers)

        # Initialize the chain
        chain = (
            OpenAIAsyncMessageChain(
                model_name=config.model_name,
                base_url=config.base_url,
                verbose=True,
            )
            .with_tools(tool_schemas, tool_mapping)
            .system(
                """You are a *very* ambitious minecraft player.
Your goal is to find and aquire dirt, wood, stone, iron and diamonds. All in your quest to kill the Ender dragon.
Follow Minecraft progression - wood first for tools, then stone, then dig deep for iron and diamonds.
You are autonomous and you can do anything you want.
I suggest making rotations of plus/minus 45 degrees at a time.
Craft wooden tools before trying to mine harder materials like stone or terracotta (remember that they take a while to mine).
Look for surface stone exposures, caves, or ravines rather than digging through hard blocks with bare hands
Don't call multiple tools at once.
"""
            )
        )

        # Handle interactive session with optional initial message
        chain = await handle_interactive_session(
            chain, config.initial_message, config.constant_msg
        )

    finally:
        await cleanup_servers(config.servers)


async def main() -> None:
    """Initialize and run the chat session."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP Client with OpenAI Message Chain")
    parser.add_argument(
        "--model",
        # default="google/gemini-flash-1.5",
        default="gpt-4.1-nano",
        help="Model name to use (default: google/gemini-flash-1.5)",
    )
    parser.add_argument(
        "--base-url",
        # default="https://openrouter.ai/api/v1",
        default=None,
        help="API base URL (default: https://openrouter.ai/api/v1)",
    )
    parser.add_argument(
        "--msg",
        default=None,
        help="An optional first message to send to the assistant",
    )
    parser.add_argument(
        "--constant-msg",
        default=None,
        help="An optional constant message to send to the assistant",
    )

    args = parser.parse_args()

    config = Configuration()
    try:
        server_config = config.load_config("servers_config.json")
    except FileNotFoundError:
        server_config = {
            "mcpServers": {
                "echo": {"command": "python", "args": ["/Users/ohadr/chains/hello.py"]}
            }
        }
        server_config = {
            "mcpServers": {
                "minecraft-controller_stdio": {
                    "command": "npx",
                    "args": [
                        "tsx",
                        "/Users/ohadr/scrape_lm_copy/minecraft-web-client/minecraft-mcp-server.ts",
                        "--transport",
                        "stdio",
                    ],
                    "env": {"NODE_NO_WARNINGS": "1"},
                },
            }
        }

    servers = [
        Server(name, srv_config)
        for name, srv_config in server_config["mcpServers"].items()
    ]

    chat_config = ChatSessionConfig(
        servers=servers,
        api_key=config.llm_api_key,
        model_name=args.model,
        base_url=args.base_url,
        initial_message=args.msg,
        constant_msg=args.constant_msg,
    )

    await run_chat_session(chat_config)


# python simple_client.py --msg "walk forwards in minecraft"
# python simple_client.py --model "google/gemma-3-12b" --base-url "http://localhost:1234/v1" --msg "walk forwards in minecraft"
# python simple_client.py --model "google/gemma-3-12b" --base-url "http://localhost:1234/v1" --msg "what's the weather in seattle?"
# python simple_client.py --model "google/gemma-3-12b" --base-url "http://localhost:1234/v1" --msg "what's the weather in tel aviv?"
if __name__ == "__main__":
    asyncio.run(main())
