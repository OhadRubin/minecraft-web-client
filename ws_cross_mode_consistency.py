import asyncio
import json
import websockets

from ws_cross_mode_sim import CrossModeServer

async def bot(name: str, host: str = "localhost", port: int = 8767):
    async with websockets.connect(f"ws://{host}:{port}") as ws:
        await ws.send(json.dumps({"init": "bot"}))
        for _ in range(2):
            msg = json.loads(await ws.recv())
            print(f"{name} received {msg}")
            await ws.send(json.dumps({"ack": f"{name}:{msg['cmd']}"}))

async def mcp(host: str = "localhost", port: int = 8767):
    async with websockets.connect(f"ws://{host}:{port}") as ws:
        await ws.send(json.dumps({"init": "mcp"}))
        for cmd in ["left", "right"]:
            await ws.send(json.dumps({"cmd": cmd}))
            ack = json.loads(await ws.recv())
            print(f"MCP got {ack}")

async def pygame_client(host: str = "localhost", port: int = 8767):
    async with websockets.connect(f"ws://{host}:{port}") as ws:
        await ws.send(json.dumps({"init": "pygame"}))
        await ws.send(json.dumps({"cmd": "jump"}))
        await asyncio.sleep(0.1)

async def main():
    server = CrossModeServer()
    await server.start()
    await asyncio.gather(
        bot("b1"),
        bot("b2"),
        mcp(),
        pygame_client(),
    )
    await server.stop()

if __name__ == "__main__":
    asyncio.run(main())

