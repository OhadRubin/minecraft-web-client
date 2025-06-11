import asyncio
import json
from typing import List, Dict, Any

import websockets

from ws_client import WebSocketClient
from mc_pygame_controller.action_converter import ActionConverter

async def run_cross_mode_sequence(sequence: List[Dict[str, Any]]):
    """Send a sequence of WebSocket actions and return received messages and MCP conversions."""
    received: List[Dict[str, Any]] = []

    async def collector(websocket, *args):
        async for message in websocket:
            received.append(json.loads(message))

    server = await websockets.serve(collector, "localhost", 8767)
    done = asyncio.Event()

    client = WebSocketClient("ws://localhost:8767", on_disconnect=lambda: done.set())
    client.start()
    await asyncio.sleep(0.2)

    for msg in sequence:
        client.send(msg)
        await asyncio.sleep(0.05)

    await client.stop()
    await done.wait()
    server.close()
    await server.wait_closed()

    mcp_commands = [ActionConverter.convert_pygame_action(m) for m in received]
    return received, mcp_commands


async def run_direction_sequence():
    """Convenience helper sending all 8 directions for cross mode comparison."""
    dirs = [
        {"type": "move", "x": 1.0, "z": 0.0},
        {"type": "move", "x": 0.0, "z": 1.0},
        {"type": "move", "x": -1.0, "z": 0.0},
        {"type": "move", "x": 0.0, "z": -1.0},
        {"type": "move", "x": 1.0, "z": 1.0},
        {"type": "move", "x": -1.0, "z": 1.0},
        {"type": "move", "x": -1.0, "z": -1.0},
        {"type": "move", "x": 1.0, "z": -1.0},
    ]
    return await run_cross_mode_sequence(dirs)


async def run_camera_sequence():
    """Send a basic look sequence for cross mode comparison."""
    looks = [
        {"type": "look", "movementX": 50, "movementY": -25},
        {"type": "look", "movementX": -25, "movementY": 10},
    ]
    return await run_cross_mode_sequence(looks)

if __name__ == "__main__":
    seq = [
        {"type": "move", "x": 1.0, "z": 0.0},
        {"type": "look", "movementX": 40, "movementY": 0},
    ]
    messages, conversions = asyncio.run(run_cross_mode_sequence(seq))
    print("WebSocket messages:", messages)
    print("MCP conversions:", conversions)

