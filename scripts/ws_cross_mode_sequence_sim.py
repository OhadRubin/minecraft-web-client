import asyncio
import json
import websockets
from typing import List

async def relay(websocket, path, clients):
    clients.add(websocket)
    try:
        async for msg in websocket:
            for c in list(clients):
                if c is not websocket and c.open:
                    await c.send(msg)
    finally:
        clients.remove(websocket)

actions = [
    {"type": "leftDown"},
    {"type": "rightDown"},
    {"type": "rightUp"},
    {"type": "leftUp"},
    {"type": "control", "control": "sneak", "state": True},
    {"type": "control", "control": "sneak", "state": False},
]

async def record(port: int, mode: str, acts: List[dict]):
    uri = f"ws://localhost:{port}"
    async with websockets.connect(uri) as bot, websockets.connect(uri) as sender:
        await bot.send(json.dumps({"init": "bot"}))
        await sender.send(json.dumps({"init": mode}))
        for act in acts:
            await sender.send(json.dumps(act))
        received = [json.loads(await bot.recv()) for _ in acts]
        return received

async def main():
    clients = set()
    server = await websockets.serve(lambda w,p: relay(w,p,clients), "localhost", 8781)
    try:
        py_msgs = await record(8781, "pygame", actions)
        mcp_msgs = await record(8781, "mcp", actions)
        print("Pygame messages:", py_msgs)
        print("MCP messages:", mcp_msgs)
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
