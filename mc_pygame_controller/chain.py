from dataclasses import dataclass, field, replace
import json
from typing import List, Dict, Union, Any, Optional, Tuple
import asyncio
from functools import wraps
import inspect
import os
import base64
import httpx
import mimetypes
from openai import AsyncOpenAI
from pydantic import BaseModel
try:
    from .chain_utils import (
        chain_method,
        encode_base64_content_from_url,
        _encode_to_data_uri,
        _resolve_multimodal_args,
        _resolve_multimodal_output,
    )
    from .conversation import Message
except ImportError:
    from chain_utils import (
        chain_method,
        encode_base64_content_from_url,
        _encode_to_data_uri,
        _resolve_multimodal_args,
        _resolve_multimodal_output,
    )
    from conversation import Message

@dataclass(frozen=True)
class PygameMCPAsyncMessageChain:
    messages: Tuple[Message] = field(default_factory=tuple)
    system_prompt: Any = None
    cache_system: bool = False
    metric_list: List[Dict[str, Any]] = field(default_factory=tuple)
    response_list: List[Any] = field(default_factory=tuple)
    verbose: bool = False
    response_format: Optional[Any] = None
    tools_list: Optional[List[Any]] = None
    tools_mapping: Optional[Dict[str, Any]] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    persistent_interface: Optional[Any] = None

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
        assert not should_cache, "OpenAI does not support caching for individual messages in this way"
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
    def user(self, content: Union[str, List[Dict[str, str]]], should_cache: bool = False):
        return self.add_message(role="user", content=content, should_cache=should_cache)

    @chain_method
    def user_image_url(self, prompt: str, image_urls: List[str]):
        content = [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": url}} for url in image_urls
        ]
        return self.user(content)

    @chain_method
    async def user_image_base64(self, prompt: str, image_urls: List[str]):
        encoded_images = [await encode_base64_content_from_url(url) for url in image_urls]
        content = [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
            for img in encoded_images
        ]
        return self.user(content)

    @chain_method
    async def user_image_file(self, prompt: str, image_paths: List[str]):
        encoded_images = [await _encode_to_data_uri(path) for path in image_paths]
        content = [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": data_uri}}
            for data_uri in encoded_images
        ]
        return self.user(content)

    @chain_method
    def user_audio_url(self, prompt: str, audio_urls: List[str]):
        content = [{"type": "text", "text": prompt}] + [
            {"type": "audio_url", "audio_url": {"url": url}} for url in audio_urls
        ]
        return self.user(content)

    @chain_method
    async def user_audio_base64(self, prompt: str, audio_urls: List[str], mime_type: str = "audio/ogg"):
        encoded_audio = [await encode_base64_content_from_url(url) for url in audio_urls]
        content = [{"type": "text", "text": prompt}] + [
            {"type": "audio_url", "audio_url": {"url": f"data:{mime_type};base64,{audio}"}}
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
    ):
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
        self = replace(self, tools_list=tools_list, tools_mapping=tools_mapping)
        return self

    def serialize(self) -> list:
        output = []
        if self.system_prompt is not None:
            output.append({"role": "system", "content": self.system_prompt})
        for m in self.messages:
            msg_dict = {"role": m.role}
            if m.content is not None:
                msg_dict["content"] = m.content
            if m.role == "assistant" and m.tool_calls is not None:
                msg_dict["tool_calls"] = m.tool_calls
            if m.role == "tool" and m.tool_call_id is not None:
                msg_dict["tool_call_id"] = m.tool_call_id
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
                input_tokens_cache_read=0,
                input_tokens_cache_create=0,
            )
        except Exception as e:
            print(f"Error parsing metrics: {e}")
            return dict(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                input_tokens_cache_read=0,
                input_tokens_cache_create=0,
            )

    @chain_method
    async def generate(self):
        while True:
            msgs = self.serialize()
            api_params = {
                "messages": msgs,
                "max_tokens": self.max_tokens,
                "temperature": 1.0,
            }
            if self.tools_list is not None:
                api_params["tools"] = self.tools_list
            assert self.persistent_interface is not None, "persistent_interface is not set"
            interface = self.persistent_interface
            interface.conv_panel.messages = msgs
            response = await interface.conv_panel._render_messages(**api_params)
            msg = response.choices[0].message
            resp = msg.content
            self = replace(
                self,
                metric_list=self.metric_list + (self.parse_metrics(response),),
                response_list=self.response_list + (resp,),
            )
            if msg.tool_calls and len(msg.tool_calls) > 0:
                self = self.bot(content=msg.content, tool_calls=msg.tool_calls)
                print(f"Bot (thinking): {msg.content}")
                for tool_call in msg.tool_calls:
                    print(f"Tool call: {tool_call}")
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_args = await _resolve_multimodal_args(tool_args)
                    if self.tools_mapping and tool_name in self.tools_mapping:
                        tool_response = await self.tools_mapping[tool_name](**tool_args)
                        tool_response = await _resolve_multimodal_output(tool_response)
                        if isinstance(tool_response, dict) and "multimodal_content" in tool_response:
                            multimodal_content = tool_response["multimodal_content"]
                            print("Tool response contained multimodal content")
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
                            if any(
                                item.get("type") == "image_url" for item in multimodal_content
                            ):
                                user_prompt = f"Here's the result from {tool_name}:"
                                self = self.user(
                                    [{"type": "text", "text": user_prompt}] + multimodal_content
                                )
                        else:
                            tool_response_str = (
                                json.dumps(tool_response)
                                if not isinstance(tool_response, str)
                                else tool_response
                            )
                            print(f"Tool response: {tool_response_str}")
                            self = self.tool(
                                content=tool_response_str,
                                tool_call_id=tool_call.id,
                                name=tool_name,
                            )
                            if (
                                tool_response_str
                                and isinstance(tool_response_str, dict)
                                and "content" in tool_response_str
                            ):
                                content = tool_response_str["content"]
                                if isinstance(content, list) and len(content) > 0:
                                    text_content = content[0].get("text", "")
                                    if text_content:
                                        first_line = text_content.split("\n")[0]
                                        print(f"📋 Result: {first_line}")
                            if tool_name == "lookAngle" and "getBotStatus" in self.tools_mapping:
                                # ✅ REFACTORED: Use shared BotStatusProcessor to eliminate duplication
                                from .bot_status_utils import BotStatusProcessor

                                await BotStatusProcessor.get_status_after_look(
                                    self.tools_mapping
                                )
                    else:
                        error_msg = f"Tool '{tool_name}' not found in tools_mapping"
                        self = self.tool(
                            content=error_msg, tool_call_id=tool_call.id, name=tool_name
                        )
            else:
                break
        return self

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
        return self.messages[-1]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "messages": self.serialize(),
            "system_prompt": self.system_prompt,
            "cache_system": self.cache_system,
            "verbose": self.verbose,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PygameMCPAsyncMessageChain":
        messages = tuple(Message(**msg) for msg in data.get("messages", []))
        return cls(
            messages=messages,
            system_prompt=data.get("system_prompt"),
            cache_system=data.get("cache_system", False),
            verbose=data.get("verbose", False),
            base_url=data.get("base_url"),
            max_tokens=data.get("max_tokens", 4096),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "PygameMCPAsyncMessageChain":
        import json
        return cls.from_dict(json.loads(json_str))
