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
from mc_pygame_controller import MinecraftController
import pygame
import threading
import time


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


class ConversationPanel:
    """Simple panel to manage conversation messages for display"""

    def __init__(self):
        self.messages = []

    def _render_messages(self):
        """Render messages for display - currently just prints them"""
        if self.messages:
            print(f"📄 Conversation has {len(self.messages)} messages")


class MinecraftControllerInterface:
    """Interface adapter for MinecraftController to work with the conversation system"""

    def __init__(self, servers_list, tools_list):
        self.servers_list = servers_list
        self.tools_list = tools_list
        self.tool_mapping = {}
        self.conv_panel = ConversationPanel()
        self.controller = None
        self.controller_thread = None
        self.running = False
        self.openai_client = None

    def start_controller(self):
        """Initialize pygame but don't start the controller yet (due to macOS threading restrictions)"""
        if not self.running:
            self.running = True
            print("🎮 MinecraftController interface ready")
            print("💡 Note: On macOS, pygame must run on main thread")
            print("💡 Use 'controller' command to launch controller window")
            print(
                "💡 Controller will be available when needed for trajectory recording"
            )

    def get_response(self):
        """Get response from OpenAI API - this is called by the generate() method"""
        if not self.openai_client:
            # Initialize OpenAI client if not already done
            self.openai_client = AsyncOpenAI()

        # This is a synchronous wrapper that will be called from the async generate() method
        # The actual async work happens in the generate() method
        # We just need to return a mock response that will be replaced
        class MockResponse:
            def __init__(self):
                self.choices = [MockChoice()]

        class MockChoice:
            def __init__(self):
                self.message = MockMessage()

        class MockMessage:
            def __init__(self):
                self.content = "Response will be handled by generate() method"
                self.tool_calls = None

        return MockResponse()

    def launch_controller(self):
        """Launch the MinecraftController on the main thread"""
        try:
            pygame.init()
            self.controller = MinecraftController()
            print("🎮 Starting Minecraft Controller...")
            print("💡 Controller window launched - use F5/F6 for trajectory recording")
            self.controller.run()
        except Exception as e:
            print(f"Error launching controller: {e}")
        finally:
            self.running = False

    def cleanup(self):
        """Clean up the controller"""
        self.running = False
        if self.controller:
            self.controller.running = False
        try:
            pygame.quit()
        except:
            pass
        print("🎮 Minecraft Controller interface cleaned up")


# from controller import MinecraftController
from mc_pygame_controller import MinecraftController


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
                "model": self.model_name,
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
    servers: list = None,
    initial_message: str | None = None,
    constant_msg: str | None = None,
) -> OpenAIAsyncMessageChain:

    # Create a persistent interface that will be reused across generate() calls
    persistent_interface = MinecraftControllerInterface(
        servers or [], chain.tools_list or []
    )
    persistent_interface.tool_mapping = chain.tools_mapping or {}

    # Store reference in chain for generate() method to use
    chain = replace(chain, persistent_interface=persistent_interface)
    print("🎮 Persistent MinecraftController created for trajectory recording")
    print("💡 Use F7 to switch to controller mode, F5/F6 to start/stop recording")

    # Start the controller in the background
    persistent_interface.start_controller()

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

                user_input = input("You: ").strip()
                if user_input.lower() in ["quit", "exit"]:
                    print("\nExiting...")
                    break

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() == "controller":
                print("🎮 Launching Minecraft Controller...")
                print(
                    "💡 This will open the controller window. Close it to return to chat."
                )
                persistent_interface.launch_controller()
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
            chain, config.servers, config.initial_message, config.constant_msg
        )

    finally:
        await cleanup_servers(config.servers)


import argparse


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
