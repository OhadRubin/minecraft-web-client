import asyncio
import json
import pytest

try:
    import websockets
    from ws_client import WebSocketClient
except Exception:  # pragma: no cover - optional dependency
    WebSocketClient = None

async def echo(websocket, _path):
    async for message in websocket:
        await websocket.send(message)

@pytest.mark.asyncio
async def test_basic_send(tmp_path):
    if WebSocketClient is None:
        pytest.skip("WebSocketClient dependency not available")
    server = await websockets.serve(echo, "localhost", 8765)
    received = []
    done = asyncio.Event()

    def on_connect():
        pass

    def on_disconnect():
        done.set()

    client = WebSocketClient("ws://localhost:8765", on_disconnect=on_disconnect)
    client.start()
    await asyncio.sleep(0.2)
    client.send({"ping": 1})
    await asyncio.sleep(0.2)
    await client.stop()
    await done.wait()
    server.close()
    await server.wait_closed()
