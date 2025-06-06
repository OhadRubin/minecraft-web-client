from dataclasses import dataclass, field, replace
import json
from typing import List, Dict, Union, Any, Optional, Tuple, Type
from functools import wraps
import inspect
import os
import base64
import httpx
import mimetypes
from openai import AsyncOpenAI
from pydantic import BaseModel
import asyncio
from .mcp_server import Server, create_tool_functions, Configuration
# from mc_pygame_controller import MinecraftController
import pygame
import threading
import time
from .chain_utils import (
    chain_method,
    encode_base64_content_from_url,
    _encode_to_data_uri,
    _resolve_multimodal_args,
    _resolve_multimodal_output,
)


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


class ConversationPanel:
    """Simple panel to manage conversation messages for display"""

    def __init__(self):
        self.messages = []
        self.captured_actions = []  # Store MCP commands from controller
        self.human_demo_mode = True  # Flag for human demo mode

    def capture_mcp_action(self, mcp_command):
        """Capture MCP commands from controller for trajectory recording"""
        self.captured_actions.append(mcp_command)
        print(f"📝 Captured action: {mcp_command['tool']}({mcp_command['parameters']})")

    def convert_actions_to_mock_response(self):
        """Convert captured human actions to mock AI response format"""
        if not self.captured_actions:
            # No actions captured, return basic response
            return {
                "content": "I'll explore and take some actions in Minecraft.",
                "tool_calls": None,
            }

        # Generate mock reasoning based on captured actions
        action_descriptions = []
        tool_calls = []

        for i, action in enumerate(self.captured_actions):
            tool_name = action["tool"]
            params = action["parameters"]

            # Generate mock tool call ID
            tool_call_id = f"call_{i}_{tool_name}"

            # Add to tool calls list
            tool_calls.append(
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {"name": tool_name, "arguments": json.dumps(params)},
                }
            )

            # Generate human-like reasoning
            if tool_name == "lookAngle":
                x_angle = params.get("xAngle", 0)
                y_angle = params.get("yAngle", 0)
                action_descriptions.append(
                    f"look around (x: {x_angle}°, y: {y_angle}°)"
                )
            elif tool_name == "walk":
                duration = params.get("duration", 1000)
                action_descriptions.append(f"move forward for {duration}ms")
            elif tool_name == "leftClick":
                action_descriptions.append("break/attack with left click")
            elif tool_name == "rightClick":
                action_descriptions.append("place/use with right click")
            elif tool_name == "setHotbarSlot":
                slot = params.get("slot", 0)
                action_descriptions.append(f"select hotbar slot {slot + 1}")
            else:
                action_descriptions.append(f"use {tool_name}")

        # Generate mock reasoning content
        if len(action_descriptions) == 1:
            content = f"I'll {action_descriptions[0]} to explore the area."
        else:
            content = f"I'll {', '.join(action_descriptions[:-1])} and {action_descriptions[-1]} to navigate and explore."

        # Clear captured actions after converting
        self.captured_actions.clear()

        return {"content": content, "tool_calls": tool_calls if tool_calls else None}

    async def _render_messages(self, **api_params):
        """Render messages for display - mock response for pygame/MCP mode"""
        if self.messages:
            print(f"📄 Conversation has {len(self.messages)} messages")

        # Return mock response that looks like OpenAI response for compatibility
        class MockResponse:

            def __init__(self, message_data):
                self.choices = [MockChoice(message_data)]
                self.usage = MockUsage()

        class MockChoice:

            def __init__(self, message_data):
                self.message = MockMessage(message_data)

        class MockMessage:

            def __init__(self, message_data):
                self.content = message_data["content"]
                self.tool_calls = message_data["tool_calls"]
                # Convert dict tool calls to mock objects if needed
                if self.tool_calls:
                    mock_tool_calls = []
                    for tc in self.tool_calls:
                        mock_tc = type(
                            "MockToolCall",
                            (),
                            {
                                "id": tc["id"],
                                "type": tc["type"],
                                "function": type(
                                    "MockFunction",
                                    (),
                                    {
                                        "name": tc["function"]["name"],
                                        "arguments": tc["function"]["arguments"],
                                    },
                                )(),
                            },
                        )()
                        mock_tool_calls.append(mock_tc)
                    self.tool_calls = mock_tool_calls

        class MockUsage:
            def __init__(self):
                self.prompt_tokens = 0
                self.completion_tokens = 0
                self.total_tokens = 0

        # Generate mock response from captured actions
        if self.human_demo_mode:
            message_data = self.convert_actions_to_mock_response()
        else:
            # Default response for non-demo mode
            message_data = {
                "content": "MCP/Pygame mode - no OpenAI call made",
                "tool_calls": None,
            }

        return MockResponse(message_data)

def create_user_message(captured_actions):
    # Create a user message based on the captured actions
    action_descriptions = []
    for action in captured_actions:
        tool_name = action["tool"]
        params = action["parameters"]
        if tool_name == "lookAngle":
            x_angle = params.get("xAngle", 0)
            y_angle = params.get("yAngle", 0)
            action_descriptions.append(
                f"look {x_angle:.1f}° horizontally, {y_angle:.1f}° vertically"
            )
        else:
            action_descriptions.append(f"use {tool_name}")

    user_message = (
        f"I performed these actions: {', '.join(action_descriptions)}"
    )
    return user_message


@dataclass(frozen=True)
class PygameMCPAsyncMessageChain:
    # model_name: str = "gpt-4o"
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

            msgs = self.serialize()

            # Prepare common parameters
            api_params = {
                "messages": msgs,
                "max_tokens": self.max_tokens,
                "temperature": 1.0,
            }

            # Only add tools if they exist
            if self.tools_list is not None:
                api_params["tools"] = self.tools_list

            # Update interface with current messages for display
            assert self.persistent_interface is not None, "persistent_interface is not set"
            interface = self.persistent_interface
            interface.conv_panel.messages = msgs

            # Make the actual OpenAI API call
            response = await interface.conv_panel._render_messages(**api_params)

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

                            # Print result if it's informative (like getBotStatus)
                            if (
                                tool_response_str
                                and isinstance(tool_response_str, dict)
                                and "content" in tool_response_str
                            ):
                                content = tool_response_str["content"]
                                if isinstance(content, list) and len(content) > 0:
                                    text_content = content[0].get("text", "")
                                    if text_content:
                                        # Print first line of result for feedback
                                        first_line = text_content.split("\n")[0]
                                        print(f"📋 Result: {first_line}")

                            # Special handling for lookAngle - get updated bot status to see effect
                            if (
                                tool_name == "lookAngle"
                                and "getBotStatus" in self.tools_mapping
                            ):
                                try:
                                    print(
                                        "👁️ Getting updated view after look command..."
                                    )
                                    status_result = await self.tools_mapping[
                                        "getBotStatus"
                                    ]()
                                    if (
                                        status_result
                                        and isinstance(status_result, dict)
                                        and "content" in status_result
                                    ):
                                        status_content = status_result["content"]
                                        if (
                                            isinstance(status_content, list)
                                            and len(status_content) > 0
                                        ):
                                            status_text = status_content[0].get(
                                                "text", ""
                                            )
                                            if status_text:
                                                # Extract just the position and facing info
                                                lines = status_text.split("\n")
                                                position_line = (
                                                    lines[0] if lines else ""
                                                )
                                                looking_at_line = [
                                                    line
                                                    for line in lines
                                                    if "Looking at:" in line
                                                ]
                                                if looking_at_line:
                                                    print(f"🎯 {position_line}")
                                                    print(f"🎯 {looking_at_line[0]}")
                                                else:
                                                    print(f"🎯 {position_line}")
                                except Exception as e:
                                    print(
                                        f"⚠️ Could not get updated status after look: {e}"
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
    def from_dict(cls, data: Dict[str, Any]) -> "PygameMCPAsyncMessageChain":
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
    def from_json(cls, json_str: str) -> "PygameMCPAsyncMessageChain":
        """Deserialize from JSON string."""
        import json

        return cls.from_dict(json.loads(json_str))


class MinecraftControllerInterface:
    """Interface for capturing human demonstrations in MCP mode and converting to trajectory data"""

    def __init__(self, mode="mcp"):
        from . import MinecraftController

        self.mode = mode
        self.conv_panel = ConversationPanel()
        self.tools_mapping = {}
        self.controller = None
        self.trajectory_storage = TrajectoryStorage()

        # Set up controller with MCP mode
        if mode == "mcp":
            self.conv_panel.human_demo_mode = True
            print(f"🎮 MinecraftControllerInterface initialized in {mode} mode")

    def capture_command(self, mcp_command):
        """Capture MCP commands from controller AND execute them through MCP server"""
        # First capture for trajectory recording
        self.conv_panel.capture_mcp_action(mcp_command)
        print(
            f"📝 Interface captured: {mcp_command['tool']}({mcp_command['parameters']})"
        )

        # IMPORTANT: Also execute the command immediately through MCP server
        # Create async task to execute the command (like getBotStatus)
        import asyncio

        try:
            # Try to execute in current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule execution without blocking
                asyncio.create_task(self.execute_command(mcp_command))
            else:
                print("⚠️ No running event loop for command execution")
        except Exception as e:
            print(f"⚠️ Could not schedule command execution: {e}")

    async def execute_command(self, action):
        """Execute MCP command through existing tools_mapping (like getBotStatus)"""
        tool_name = action["tool"]
        params = action["parameters"]

        print(f"🎮 Executing: {tool_name}({params})")

        # Execute via existing tools_mapping (same as getBotStatus)
        if tool_name in self.tools_mapping:
            try:
                result = await self.tools_mapping[tool_name](**params)
                print(f"✅ Executed {tool_name} successfully")

                # Print result if it's informative (like getBotStatus)
                if result and isinstance(result, dict) and "content" in result:
                    content = result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        text_content = content[0].get("text", "")
                        if text_content:
                            # Print first line of result for feedback
                            first_line = text_content.split("\n")[0]
                            print(f"📋 Result: {first_line}")

                # Special handling for lookAngle - get updated bot status to see effect
                if tool_name == "lookAngle" and "getBotStatus" in self.tools_mapping:
                    try:
                        print("👁️ Getting updated view after look command...")
                        status_result = await self.tools_mapping["getBotStatus"]()
                        if (
                            status_result
                            and isinstance(status_result, dict)
                            and "content" in status_result
                        ):
                            status_content = status_result["content"]
                            if (
                                isinstance(status_content, list)
                                and len(status_content) > 0
                            ):
                                status_text = status_content[0].get("text", "")
                                if status_text:
                                    # Extract just the position and facing info
                                    lines = status_text.split("\n")
                                    position_line = lines[0] if lines else ""
                                    looking_at_line = [
                                        line for line in lines if "Looking at:" in line
                                    ]
                                    if looking_at_line:
                                        print(f"🎯 {position_line}")
                                        print(f"🎯 {looking_at_line[0]}")
                                    else:
                                        print(f"🎯 {position_line}")
                    except Exception as e:
                        print(f"⚠️ Could not get updated status after look: {e}")

                return result
            except Exception as e:
                print(f"❌ Error executing {tool_name}: {e}")
                import traceback

                traceback.print_exc()
                return None
        else:
            print(f"⚠️ Tool {tool_name} not found in tools_mapping")
            available_tools = (
                list(self.tools_mapping.keys()) if self.tools_mapping else []
            )
            print(f"💡 Available tools: {available_tools}")
            return None

    def set_controller(self, controller):
        """Set the minecraft controller instance"""
        self.controller = controller
        controller.set_mcp_executor(self)
        print(f"🔗 Controller connected to interface")

    def start_trajectory_recording(self, session_name="human_demo"):
        """Start recording human demonstration trajectory"""
        self.trajectory_storage.start_session(session_name)
        print(f"🎬 Started trajectory recording: {session_name}")

    def stop_trajectory_recording(self):
        """Stop recording and save trajectory"""
        if self.conv_panel.captured_actions:
            # Convert remaining actions to mock response
            mock_response = self.conv_panel.convert_actions_to_mock_response()
            trajectory = self.trajectory_storage.end_session(mock_response)
            print(
                f"🎬 Stopped recording. Saved trajectory with {len(trajectory.get('messages', []))} messages"
            )
            return trajectory
        else:
            print(f"🎬 Stopped recording. No actions captured.")
            return None

    def save_demonstration_step(self, user_context="exploring"):
        """Save a demonstration step with captured actions"""
        if self.conv_panel.captured_actions:
            mock_response = self.conv_panel.convert_actions_to_mock_response()
            self.trajectory_storage.add_step(user_context, mock_response)
            print(f"💾 Saved demonstration step: {user_context}")
            return True
        return False


class TrajectoryStorage:
    """Handles storage and management of human demonstration trajectories"""

    def __init__(self):
        self.current_session = None
        self.session_data = []

    def start_session(self, session_name):
        """Start a new trajectory recording session"""
        self.current_session = {
            "session_name": session_name,
            "timestamp": time.time(),
            "messages": [],
            "actions": [],
        }

    def add_step(self, user_context, mock_response):
        """Add a demonstration step to current session"""
        if not self.current_session:
            return

        # Add user message describing context
        user_message = {
            "role": "user",
            "content": user_context,
            "timestamp": time.time(),
        }

        # Add assistant response with tool calls
        assistant_message = {
            "role": "assistant",
            "content": mock_response["content"],
            "tool_calls": mock_response["tool_calls"],
            "timestamp": time.time(),
        }

        self.current_session["messages"].extend([user_message, assistant_message])

        # Add tool results if there were tool calls
        if mock_response["tool_calls"]:
            for tool_call in mock_response["tool_calls"]:
                tool_result = {
                    "role": "tool",
                    "content": f"Executed {tool_call['function']['name']} successfully",
                    "tool_call_id": tool_call["id"],
                    "name": tool_call["function"]["name"],
                    "timestamp": time.time(),
                }
                self.current_session["messages"].append(tool_result)

    def end_session(self, final_response=None):
        """End current session and save trajectory"""
        if not self.current_session:
            return None

        # Add final response if provided
        if final_response:
            self.add_step("final actions", final_response)

        # Save to file
        filename = f"trajectories/{self.current_session['session_name']}_{int(self.current_session['timestamp'])}.json"

        # Create directory if it doesn't exist
        import os

        os.makedirs("trajectories", exist_ok=True)

        # Save trajectory
        with open(filename, "w") as f:
            json.dump(self.current_session, f, indent=2)

        trajectory = self.current_session
        self.current_session = None

        print(f"💾 Saved trajectory to {filename}")
        return trajectory


# if __name__ == "__main__":


# result = await self.chain.tools_mapping["getBotStatus"]()


# Use the working tools_mapping from the chain (which was set by run_chat_session)
# persistent_interface.tools_mapping = chain.tools_mapping or {}

# print(f"🔍 DEBUG: Setting up persistent_interface...")
# print(f"🔍 DEBUG: servers passed: {servers}")
# print(f"🔍 DEBUG: chain.tools_mapping: {chain.tools_mapping}")
# print(
#     f"🔍 DEBUG: persistent_interface.tools_mapping: {persistent_interface.tools_mapping}"
# )
# if persistent_interface.tools_mapping:
#     print(
#         f"🔍 DEBUG: Available tools in interface: {list(persistent_interface.tools_mapping.keys())}"
#     )
# else:
#     print(f"🔍 DEBUG: No tools found in interface!")
#     print(f"🔍 DEBUG: This means the MCP server connection failed!")

# # Test MCP connection BEFORE starting pygame controller
# print(f"🔍 DEBUG: Testing MCP connection with getBotStatus...")
# if (
#     persistent_interface.tools_mapping
#     and "getBotStatus" in persistent_interface.tools_mapping
# ):
#     try:
#         import asyncio


#         print(f"✅ MCP connection test successful!")
#         print(f"📊 getBotStatus result: {result}")
#     except Exception as e:
#         print(f"❌ MCP connection test failed: {e}")
#         print(f"💡 This suggests the MCP server is not running or not connected")
#         print(f"💡 Please start: npx tsx minecraft-mcp-server.ts --transport stdio")
#         import traceback

#         print(f"🔍 DEBUG: MCP test error traceback:")
#         traceback.print_exc()
# else:
#     print(f"❌ getBotStatus tool not found in tools_mapping")
#     print(
#         f"Available tools: {list(persistent_interface.tools_mapping.keys()) if persistent_interface.tools_mapping else 'None'}"
#     )

# Store reference in chain for generate() method to use
# chain = replace(chain, persistent_interface=persistent_interface)

# Start the controller in the background
# persistent_interface.start_controller()


# print(f"🎯 IMPORTANT: Make sure you have:")
# print(f"   1. Minecraft web client running (browser)")
# print(f"   2. MCP server running: npx tsx minecraft-mcp-server.ts")
# print(f"   3. Both should be connected on ws://localhost:8081")

# # Send initial message if provided
# if initial_message:
#     print(f"You: {initial_message}")

#     # Handle special case for controller launch
#     if initial_message.lower() == "controller":
#         print("🎮 Launching Minecraft Controller...")
#         print("💡 Controller will run with auto-generation of captured actions.")

#         # Set up the chain for auto-processing
#         persistent_interface.chain = chain
#         persistent_interface.launch_controller()

#         # Return the updated chain after controller session
#         return (
#             persistent_interface.chain
#             if hasattr(persistent_interface, "chain")
#             else chain
#         )

#     chain = await chain.user(initial_message).generate_bot()
#     print(f"Assistant: {chain.last_response}")

# print("Chat session started. Type 'quit' or 'exit' to end.")

# while True:
#     try:
#         if constant_msg is not None:
#             user_input = constant_msg
#         else:

#             user_input = input("You: ").strip()
#             if user_input.lower() in ["quit", "exit"]:
#                 print("\nExiting...")
#                 break

#         if not user_input:
#             continue

#         # Handle special commands
#         if user_input.lower() == "controller":
#             print("🎮 Launching Minecraft Controller...")
#             print(
#                 "💡 This will open the controller window. Close it to return to chat."
#             )
#             persistent_interface.launch_controller()
#             continue

#         # Use the new async-aware method
#         chain = await chain.user(user_input).generate_bot()
#         print(f"Assistant: {chain.last_response}")

#     except KeyboardInterrupt:
#         print("\nExiting...")
#         break
#     except Exception as e:
#         print(f"Error during interaction: {e}")
#         continue

# # Clean up pygame interface
# if persistent_interface:
#     persistent_interface.cleanup()

# return chain


# python simple_client.py --msg "walk forwards in minecraft"
# python simple_client.py --model "google/gemma-3-12b" --base-url "http://localhost:1234/v1" --msg "walk forwards in minecraft"
# python simple_client.py --model "google/gemma-3-12b" --base-url "http://localhost:1234/v1" --msg "what's the weather in seattle?"
# python simple_client.py --model "google/gemma-3-12b" --base-url "http://localhost:1234/v1" --msg "what's the weather in tel aviv?"
