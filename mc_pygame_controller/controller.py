from .controller_base import MinecraftController

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
import argparse
from .mcp_client import Server, create_tool_functions, Configuration
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

from .message_chain import PygameMCPAsyncMessageChain


@dataclass
class ChatSessionConfig:
    """Configuration for chat session."""

    servers: list["Server"]
    initial_message: str | None = None
    constant_msg: str | None = None


async def cleanup_servers(servers: list[Server]) -> None:
    """Clean up all servers properly."""
    print("🔧 Starting server cleanup...")

    # Give active operations a moment to complete before cleanup
    await asyncio.sleep(0.5)
    print("🔧 Proceeding with MCP server cleanup...")

    for server in reversed(servers):
        try:
            print(f"🔧 Cleaning up server: {server.name}")
            await server.cleanup()
            print(f"✅ Server {server.name} cleaned up successfully")
        except Exception as e:
            print(f"⚠️ Warning during cleanup of {server.name}: {e}")

    print("🔧 Server cleanup completed")


async def initialize_servers(servers: list[Server]) -> bool:
    for server in servers:
        try:
            await server.initialize()
        except Exception as e:
            print(f"Failed to initialize server: {e}")
            await cleanup_servers(servers)
            return False
    return True


def pygame_event_loop(loop, event_queue):
    """Handle pygame events in separate thread"""
    while True:
        try:
            event = pygame.event.wait()
            asyncio.run_coroutine_threadsafe(event_queue.put(event), loop=loop)
        except Exception as e:
            print(f"Error in pygame event loop: {e}")
            break


async def handle_interactive_session(
    chain: PygameMCPAsyncMessageChain,
    servers: list = None,
    initial_message: str | None = None,
    constant_msg: str | None = None,
    sensitivity: float = 5.0,
) -> PygameMCPAsyncMessageChain:
    """Run pygame controller with MCP integration using asyncio pattern"""

    # Initialize pygame
    pygame.init()
    pygame.display.set_caption("Minecraft Web Client Controller - MCP Mode")

    # Create MinecraftControllerInterface for human demonstration capture
    from .message_chain import MinecraftControllerInterface

    interface = MinecraftControllerInterface(mode="mcp")
    interface.tools_mapping = chain.tools_mapping or {}

    # Start trajectory recording for human demonstrations
    interface.start_trajectory_recording("human_demo_session")

    # Set interface as persistent interface for the chain
    chain = replace(chain, persistent_interface=interface)

    # Create controller with sensitivity
    print(f"🎮 MCP mode sensitivity: {sensitivity} pixels per degree")
    controller = MinecraftController(
        mode="mcp", chain_args=(servers, chain), sensitivity=sensitivity
    )

    # Connect controller to interface for command capture
    interface.set_controller(controller)

    # Start async tasks (no separate thread for events)
    animation_task = asyncio.create_task(controller.animation_loop())

    # Test getBotStatus at startup
    if chain and chain.tools_mapping and "getBotStatus" in chain.tools_mapping:
        test_task = asyncio.create_task(controller.test_get_bot_status_startup(chain))

    try:
        # Run until controller signals to stop
        while controller.state.running:
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        controller.state.running = False

        # Save any remaining demonstration data
        trajectory = interface.stop_trajectory_recording()
        if trajectory:
            print(
                f"💾 Human demonstration saved with {len(trajectory.get('messages', []))} messages"
            )

        animation_task.cancel()
        if 'test_task' in locals():
            test_task.cancel()
        pygame.quit()

    return chain


async def run_chat_session(config: ChatSessionConfig, sensitivity: float = 5.0) -> None:
    """Main chat session handler using functional paradigm.

    Args:
        config: Chat session configuration
        sensitivity: Mouse sensitivity for MCP mode
    """
    try:
        # Initialize servers
        if not await initialize_servers(config.servers):
            return

        # Create tool functions and schemas
        tool_schemas, tool_mapping = await create_tool_functions(config.servers)

        # Initialize the chain
        chain = (
            PygameMCPAsyncMessageChain(
                # model_name=config.model_name,
                # base_url=config.base_url,
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
            chain,
            config.servers,
            config.initial_message,
            config.constant_msg,
            sensitivity,
        )

    finally:
        await cleanup_servers(config.servers)


# python -m mc_pygame_controller.controller --mcp
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Minecraft Web Client Controller")
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run in MCP mode (commands sent directly to bot) instead of pygame mode (commands forwarded to bot)",
    )
    parser.add_argument(
        "--sensitivity",
        type=float,
        default=5.0,
        help="Mouse sensitivity for MCP mode (pixels per degree, default: 5.0). Lower = more sensitive",
    )
    parser.add_argument(
        "--enable-logging",
        action="store_true",
        default=True,
        help="Enable logging of pygame commands in MCP format (for data collection)",
    )
    args = parser.parse_args()

    # Determine mode
    mode = "mcp" if args.mcp else "pygame"

    # Create and run controller
    if mode == "pygame":
        controller = MinecraftController(mode=mode, enable_logging=getattr(args, 'enable_logging', False))
        controller.run()
    else:
        async def runner():

            config = Configuration()
            try:
                server_config = config.load_config("servers_config.json")
            except FileNotFoundError:
                server_config = {
                    "mcpServers": {
                        "echo": {
                            "command": "python",
                            "args": ["/Users/ohadr/chains/hello.py"],
                        }
                    }
                }
                server_config = {
                    "mcpServers": {
                        "minecraft-controller_stdio": {
                            "command": "npx",
                            "args": [
                                "tsx",
                                "/Users/ohadr/minecraft-web-client/minecraft-mcp-server.ts",
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
                initial_message=None,
                constant_msg=None,
            )

            await run_chat_session(chat_config, args.sensitivity)

        asyncio.run(runner())
