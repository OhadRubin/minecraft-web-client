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

from ws_cross_mode_sim import CrossModeServer

@pytest.mark.asyncio
async def test_cross_mode_message_flow():
    server = CrossModeServer(port=8768)
    await server.start()

    bot_received = []
    mcp_received = []

    async def bot():
        async with websockets.connect("ws://localhost:8768") as ws:
            await ws.send(json.dumps({"init": "bot"}))
            # Expect command from mcp then pygame
            for _ in range(2):
                msg = json.loads(await ws.recv())
                bot_received.append(msg)
                await ws.send(json.dumps({"ack": msg.get("cmd")}))

    async def mcp():
        async with websockets.connect("ws://localhost:8768") as ws:
            await ws.send(json.dumps({"init": "mcp"}))
            await ws.send(json.dumps({"cmd": "from_mcp"}))
            mcp_received.append(json.loads(await ws.recv()))
            mcp_received.append(json.loads(await ws.recv()))

    async def pygame():
        async with websockets.connect("ws://localhost:8768") as ws:
            await ws.send(json.dumps({"init": "pygame"}))
            await ws.send(json.dumps({"cmd": "from_pygame"}))
            await asyncio.sleep(0.1)

    await asyncio.gather(bot(), mcp(), pygame())
    await server.stop()

    assert bot_received == [{"cmd": "from_mcp"}, {"cmd": "from_pygame"}]
    assert mcp_received == [{"ack": "from_mcp"}, {"ack": "from_pygame"}]


@pytest.mark.asyncio
async def test_cross_mode_multiple_bots():
    server = CrossModeServer(port=8769)
    await server.start()

    async def bot(name):
        async with websockets.connect("ws://localhost:8769") as ws:
            await ws.send(json.dumps({"init": "bot"}))
            msg = json.loads(await ws.recv())
            await ws.send(json.dumps({"ack": f"{name}:{msg.get('cmd')}"}))

    async def mcp():
        async with websockets.connect("ws://localhost:8769") as ws:
            await ws.send(json.dumps({"init": "mcp"}))
            await ws.send(json.dumps({"cmd": "test"}))
            acks = [json.loads(await ws.recv()), json.loads(await ws.recv())]
            return acks

    results = await asyncio.gather(bot("b1"), bot("b2"), mcp())
    await server.stop()

    acks = results[-1]
    assert {ack["ack"] for ack in acks} == {"b1:test", "b2:test"}

@pytest.mark.asyncio
async def test_cross_mode_reconnect_client():
    server = CrossModeServer(port=8770)
    await server.start()
    results = []

    async def bot():
        async with websockets.connect("ws://localhost:8770") as ws:
            await ws.send(json.dumps({"init": "bot"}))
            for _ in range(2):
                msg = json.loads(await ws.recv())
                await ws.send(json.dumps({"ack": msg["cmd"]}))

    async def mcp():
        async with websockets.connect("ws://localhost:8770") as ws:
            await ws.send(json.dumps({"init": "mcp"}))
            await ws.send(json.dumps({"cmd": "one"}))
            await ws.recv()
        await asyncio.sleep(0.05)
        async with websockets.connect("ws://localhost:8770") as ws2:
            await ws2.send(json.dumps({"init": "mcp"}))
            await ws2.send(json.dumps({"cmd": "two"}))
            results.append(json.loads(await ws2.recv()))

    await asyncio.gather(bot(), mcp())
    await server.stop()
    assert results == [{"ack": "two"}]


@pytest.mark.asyncio
async def test_cross_mode_multiple_mcp_clients():
    server = CrossModeServer(port=8771)
    await server.start()
    results = []

    async def bot():
        async with websockets.connect("ws://localhost:8771") as ws:
            await ws.send(json.dumps({"init": "bot"}))
            for _ in range(2):
                msg = json.loads(await ws.recv())
                await ws.send(json.dumps({"ack": msg["cmd"]}))

    async def mcp(name):
        async with websockets.connect("ws://localhost:8771") as ws:
            await ws.send(json.dumps({"init": "mcp"}))
            await ws.send(json.dumps({"cmd": name}))
            a1 = json.loads(await ws.recv())
            a2 = json.loads(await ws.recv())
            results.append({"name": name, "acks": {a1["ack"], a2["ack"]}})

    await asyncio.gather(bot(), mcp("a"), mcp("b"))
    await server.stop()

    assert {"a", "b"} == results[0]["acks"]
    assert {"a", "b"} == results[1]["acks"]

@pytest.mark.asyncio
async def test_cross_mode_reconnect_bot():
    server = CrossModeServer(port=8772)
    await server.start()
    results = []
    first_done = asyncio.Event()

    async def bot_first():
        async with websockets.connect("ws://localhost:8772") as ws:
            await ws.send(json.dumps({"init": "bot"}))
            msg = json.loads(await ws.recv())
            await ws.send(json.dumps({"ack": f"first:{msg['cmd']}"}))
        first_done.set()

    async def bot_second():
        async with websockets.connect("ws://localhost:8772") as ws:
            await ws.send(json.dumps({"init": "bot"}))
            msg = json.loads(await ws.recv())
            await ws.send(json.dumps({"ack": f"second:{msg['cmd']}"}))

    async def mcp():
        async with websockets.connect("ws://localhost:8772") as ws:
            await ws.send(json.dumps({"init": "mcp"}))
            await ws.send(json.dumps({"cmd": "one"}))
            results.append(json.loads(await ws.recv()))
            await first_done.wait()
            await ws.send(json.dumps({"cmd": "two"}))
            results.append(json.loads(await ws.recv()))

    await asyncio.gather(bot_first(), mcp(), bot_second())
    await server.stop()
    assert results == [{"ack": "first:one"}, {"ack": "second:two"}]


