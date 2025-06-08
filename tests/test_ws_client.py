import os
import sys
import asyncio
import json
import websockets
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ws_client import WebSocketClient

async def echo(websocket, _path):
    async for message in websocket:
        await websocket.send(message)

@pytest.mark.asyncio
async def test_basic_send(tmp_path):
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
