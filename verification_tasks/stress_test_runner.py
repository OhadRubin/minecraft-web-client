"""Automated stress test helper for mc_pygame_controller.

This script connects to the WebSocket relay used by the controller and
sends a continuous stream of randomized actions. It is intended as a
lightweight way to exercise the server during integration testing.
"""

import argparse
import asyncio
import json
import random
import time
from typing import Callable, Dict

import websockets

# Available action generators

ActionGenerator = Callable[[], Dict[str, object]]


def move_action() -> Dict[str, object]:
    return {"type": "move", "x": random.uniform(-1, 1), "z": random.uniform(-1, 1)}


def look_action() -> Dict[str, object]:
    return {
        "type": "look",
        "movementX": random.randint(-15, 15),
        "movementY": random.randint(-15, 15),
    }


def click_action() -> Dict[str, object]:
    return {"type": "documentMouseEvent", "button": 0, "action": random.choice(["down", "up"])}


def hotbar_action() -> Dict[str, object]:
    return {"type": "setHotbarSlot", "slot": random.randint(0, 8)}


def jump_action() -> Dict[str, object]:
    return {"type": "jump"}


ACTIONS: list[ActionGenerator] = [
    move_action,
    look_action,
    click_action,
    hotbar_action,
    jump_action,
]


async def stress_test(uri: str, duration: float = 60.0, interval: float = 0.1) -> None:
    """Run stress test for ``duration`` seconds."""
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"init": "pygame"}))
        end = time.time() + duration
        while time.time() < end:
            action = random.choice(ACTIONS)()
            await ws.send(json.dumps(action))
            await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send random actions to WebSocket server for stress testing")
    parser.add_argument("--uri", default="ws://localhost:8081", help="WebSocket server URI")
    parser.add_argument("--duration", type=float, default=60.0, help="Duration of the test in seconds")
    parser.add_argument("--interval", type=float, default=0.1, help="Delay between actions in seconds")
    args = parser.parse_args()
    asyncio.run(stress_test(args.uri, args.duration, args.interval))


if __name__ == "__main__":
    main()
