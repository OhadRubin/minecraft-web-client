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



def chain_method(func):
    """Decorator for chain methods to ensure they return self for chaining."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if result is None:
            return self
        return result
    return wrapper



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