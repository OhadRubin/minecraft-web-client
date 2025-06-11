import asyncio
import json
import websockets
import types
from mc_pygame_controller import mode_strategy
from mc_pygame_controller.action_converter import convert_to_mcp_format

class DummyController:
    def __init__(self, queue):
        self.queue = queue
        self.last_moved_in_mcp_mode = 0
        self.enable_logging = False
        self.action_handler = types.SimpleNamespace(_log_mcp_command=lambda *a, **k: None)

    async def send_command_sync(self, cmd):
        await self.queue.put(cmd)

    async def handle_other_commands(self, command_type, **params):
        mcp_cmd = convert_to_mcp_format(command_type, params)
        if mcp_cmd:
            await self.queue.put(mcp_cmd)

async def relay(websocket, path, queue):
    async for msg in websocket:
        await queue.put(json.loads(msg))

async def run_strategy(strategy, uri):
    async with websockets.connect(uri) as ws:
        # patch controller methods to send via websocket
        async def send_cmd(cmd):
            await ws.send(json.dumps(cmd))
        async def handle_other(action, **params):
            await ws.send(json.dumps(convert_to_mcp_format(action, params)))
        strategy.controller.send_command_sync = send_cmd
        strategy.controller.handle_other_commands = handle_other
        # perform sample actions
        strategy.handle_timed_action(
            "leftClick",
            "short",
            {"type": "leftDown"},
            {"type": "leftUp"},
        )
        strategy.handle_toggle_action("sneak", True, "sneak")
        strategy.handle_simple_action("toggleInventory", {"type": "inventory"})
        await asyncio.sleep(0.1)

async def main():
    queue_py = asyncio.Queue()
    queue_mcp = asyncio.Queue()
    server = await websockets.serve(lambda w,p: relay(w,p,queue_py if not queue_py.qsize() else queue_mcp), "localhost", 8780)
    try:
        py_ctrl = DummyController(queue_py)
        mcp_ctrl = DummyController(queue_mcp)
        py_strategy = mode_strategy.PygameModeStrategy(py_ctrl)
        mcp_strategy = mode_strategy.MCPModeStrategy(mcp_ctrl)
        await asyncio.gather(
            run_strategy(py_strategy, "ws://localhost:8780"),
            run_strategy(mcp_strategy, "ws://localhost:8780"),
        )
        await asyncio.sleep(0.1)
        py_msgs = []
        while not queue_py.empty():
            py_msgs.append(await queue_py.get())
        mcp_msgs = []
        while not queue_mcp.empty():
            mcp_msgs.append(await queue_mcp.get())
        print("Pygame messages:", py_msgs)
        print("MCP messages:", mcp_msgs)
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
