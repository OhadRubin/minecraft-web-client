import asyncio
import json
import websockets

from ws_cross_mode_sim import CrossModeServer

async def reconnecting_bots(host="localhost", port=8773):
    async with websockets.connect(f"ws://{host}:{port}") as ws:
        await ws.send(json.dumps({"init": "bot"}))
        msg = json.loads(await ws.recv())
        print("first bot got", msg)
        await ws.send(json.dumps({"ack": "first"}))
    await asyncio.sleep(0.1)
    async with websockets.connect(f"ws://{host}:{port}") as ws:
        await ws.send(json.dumps({"init": "bot"}))
        msg = json.loads(await ws.recv())
        print("second bot got", msg)
        await ws.send(json.dumps({"ack": "second"}))

async def multiple_mcps(host="localhost", port=8773):
    async with websockets.connect(f"ws://{host}:{port}") as ws1, \
        websockets.connect(f"ws://{host}:{port}") as ws2:
        await ws1.send(json.dumps({"init": "mcp"}))
        await ws2.send(json.dumps({"init": "mcp"}))
        await ws1.send(json.dumps({"cmd": "a"}))
        await ws2.send(json.dumps({"cmd": "b"}))
        for ws in (ws1, ws2):
            for _ in range(2):
                msg = json.loads(await ws.recv())
                print("mcp got", msg)

async def main():
    server = CrossModeServer(host="localhost", port=8773)
    await server.start()
    await asyncio.gather(reconnecting_bots(), multiple_mcps())
    await server.stop()

if __name__ == "__main__":
    asyncio.run(main())

