import asyncio
import json
import websockets
from typing import List

async def relay(websocket, path, clients):
    clients.add(websocket)
    try:
        async for msg in websocket:
            for client in list(clients):
                if client is not websocket and client.open:
                    await client.send(msg)
    finally:
        clients.remove(websocket)

async def record_actions(port: int, mode: str, actions: List[dict]) -> List[dict]:
    uri = f"ws://localhost:{port}"
    async with websockets.connect(uri) as bot, websockets.connect(uri) as sender:
        await bot.send(json.dumps({"init": "bot"}))
        await sender.send(json.dumps({"init": mode}))
        for act in actions:
            await sender.send(json.dumps(act))
        received = []
        for _ in actions:
            received.append(json.loads(await bot.recv()))
        return received

async def main():
    actions = [{"type": "leftDown"}, {"type": "leftUp"}, {"type": "control", "control": "jump", "state": True}]
    clients = set()
    server = await websockets.serve(lambda w,p: relay(w,p,clients), "localhost", 8771)
    try:
        pygame_msgs = await record_actions(8771, "pygame", actions)
        mcp_msgs = await record_actions(8771, "mcp", actions)
        print("Pygame sequence:", pygame_msgs)
        print("MCP sequence:", mcp_msgs)
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
