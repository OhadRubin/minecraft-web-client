import asyncio
import json
import websockets

async def main():
    uri = "ws://localhost:8081"
    async with websockets.connect(uri) as ws:
        # Move forward for one second using the touch interface
        await ws.send(json.dumps({"type": "move", "x": 0, "z": -1}))
        await asyncio.sleep(1)
        await ws.send(json.dumps({"type": "move", "x": 0, "z": 0}))

        # Look slightly to the left using simple movement
        await ws.send(json.dumps({"type": "look", "movementX": -30, "movementY": 0}))

        # Example of using raw touch coordinates (like a real touch event)
        # Simulate a drag from (100, 100) to (70, 90)
        await ws.send(
            json.dumps(
                {
                    "type": "lookTouch",
                    "currentX": 70,
                    "lastX": 100,
                    "currentY": 90,
                    "lastY": 100,
                }
            )
        )

        await asyncio.sleep(0.5)

        # Another touch movement - continue the drag
        await ws.send(
            json.dumps(
                {
                    "type": "lookTouch",
                    "currentX": 50,
                    "lastX": 70,
                    "currentY": 80,
                    "lastY": 90,
                }
            )
        )

asyncio.run(main())
