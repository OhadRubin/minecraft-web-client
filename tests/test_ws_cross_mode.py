import asyncio
import json
import websockets
import pytest

async def relay_handler(conn, clients):
    clients.add(conn)
    try:
        async for message in conn:
            for client in list(clients):
                if client is not conn:
                    await client.send(message)
    finally:
        clients.remove(conn)

async def capture(port, mode, actions):
    uri = f"ws://localhost:{port}"
    async with websockets.connect(uri) as bot, websockets.connect(uri) as sender:
        await bot.send(json.dumps({"init": "bot"}))
        await sender.send(json.dumps({"init": mode}))
        await bot.recv()
        for act in actions:
            await sender.send(json.dumps(act))
        received = []
        for _ in actions:
            received.append(json.loads(await bot.recv()))
        return received

@pytest.mark.asyncio
async def test_ws_cross_mode_consistency():
    actions = [{"type": "leftDown"}, {"type": "leftUp"}]
    clients = set()
    server = await websockets.serve(lambda c: relay_handler(c, clients), "localhost", 8770)
    try:
        pygame_msgs = await capture(8770, "pygame", actions)
        mcp_msgs = await capture(8770, "mcp", actions)
    finally:
        server.close()
        await server.wait_closed()
    assert pygame_msgs == mcp_msgs

@pytest.mark.asyncio
async def test_ws_cross_mode_sequence():
    actions = [
        {"type": "leftDown"},
        {"type": "rightDown"},
        {"type": "rightUp"},
        {"type": "leftUp"},
        {"type": "control", "control": "sneak", "state": True},
        {"type": "control", "control": "sneak", "state": False},
    ]
    clients = set()
    server = await websockets.serve(lambda c: relay_handler(c, clients), "localhost", 8775)
    try:
        py_msgs = await capture(8775, "pygame", actions)
        mcp_msgs = await capture(8775, "mcp", actions)
    finally:
        server.close()
        await server.wait_closed()
    assert py_msgs == mcp_msgs
