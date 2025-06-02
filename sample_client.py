import asyncio
import json
import websockets

async def main():
    uri = "ws://localhost:8081"
    async with websockets.connect(uri) as ws:
        for _ in range(10):
            # Example: move forward for one second
            await ws.send(json.dumps({"type": "control", "control": "forward", "state": True}))
            await asyncio.sleep(1)
            await ws.send(json.dumps({"type": "control", "control": "forward", "state": False}))

asyncio.run(main())


