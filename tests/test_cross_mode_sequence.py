import asyncio
import sys
import types
import pytest
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Stub pygame to avoid heavy dependency during import
dummy_pygame = types.ModuleType("pygame")
dummy_pygame.init = lambda: None
dummy_pygame.USEREVENT = 24
dummy_font = types.SimpleNamespace(init=lambda: None)
dummy_pygame.font = dummy_font
dummy_event = types.SimpleNamespace(Event=object)
dummy_pygame.event = dummy_event
dummy_locals = types.ModuleType("pygame.locals")
dummy_pygame.locals = dummy_locals
sys.modules.setdefault("pygame", dummy_pygame)
sys.modules.setdefault("pygame.locals", dummy_locals)

# Provide dummy mcp_client and mcp modules so mode_strategy imports succeed
dummy_mcp_client = types.ModuleType("mcp_client")
dummy_mcp = types.ModuleType("mcp")
dummy_chain = types.ModuleType("chain")
class DummyServer:
    def __init__(self, *args, **kwargs):
        pass

dummy_mcp_client.Server = DummyServer
class DummyClientSession:
    pass
class DummyStdioServerParameters:
    def __init__(self, *args, **kwargs):
        pass

dummy_mcp.ClientSession = DummyClientSession
dummy_mcp.StdioServerParameters = DummyStdioServerParameters
sys.modules.setdefault("mcp_client", dummy_mcp_client)
sys.modules.setdefault("mcp", dummy_mcp)
sys.modules.setdefault("mcp.client", types.ModuleType("mcp.client"))
sys.modules.setdefault("chain", dummy_chain)
dummy_chain.PygameMCPAsyncMessageChain = type("PygameMCPAsyncMessageChain", (), {})

# Provide lightweight mc_pygame_controller package with minimal submodules
dummy_pkg = types.ModuleType("mc_pygame_controller")
dummy_mode_strategy = types.ModuleType("mc_pygame_controller.mode_strategy")
dummy_constants = types.ModuleType("mc_pygame_controller.constants")
dummy_constants.CUSTOM_MCP_TASK_EVENT = 25
dummy_constants.CUSTOM_MCP_RESULT_EVENT = 26

class PygameModeStrategy:
    def __init__(self, controller):
        self.controller = controller

    def handle_movement(self, x: float, z: float):
        self.controller.send_command_sync({"type": "move", "x": x, "z": z})


class MCPModeStrategy:
    def __init__(self, controller):
        self.controller = controller

    def handle_movement(self, x: float, z: float):
        self.controller.handle_other_commands("walk", duration=1000)

dummy_mode_strategy.PygameModeStrategy = PygameModeStrategy
dummy_mode_strategy.MCPModeStrategy = MCPModeStrategy
dummy_pkg.mode_strategy = dummy_mode_strategy
dummy_pkg.constants = dummy_constants
sys.modules.setdefault("mc_pygame_controller", dummy_pkg)
sys.modules.setdefault("mc_pygame_controller.mode_strategy", dummy_mode_strategy)
sys.modules["mc_pygame_controller.constants"] = dummy_constants

import importlib.util, os
base_dir = os.path.dirname(os.path.dirname(__file__))
conv_path = os.path.join(base_dir, "mc_pygame_controller", "action_converter.py")
spec = importlib.util.spec_from_file_location("mc_pygame_controller.action_converter", conv_path)
action_converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(action_converter)
dummy_pkg.action_converter = action_converter
sys.modules["mc_pygame_controller.action_converter"] = action_converter

from simulate_cross_mode_ws import run_cross_mode_sequence
from mc_pygame_controller.mode_strategy import PygameModeStrategy, MCPModeStrategy

class DummyController:
    def __init__(self):
        self.sent_commands = []
        self.last_moved_in_mcp_mode = 0
        self.enable_logging = False
    def send_command_sync(self, cmd):
        self.sent_commands.append(cmd)
    def handle_other_commands(self, action_name, **params):
        self.sent_commands.append({"tool": action_name, "parameters": params})

class SimpleEnv:
    def __init__(self):
        self.x = 0.0
        self.z = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
    async def walk(self, duration_ms):
        # Without direction info we can't move; simulate no-op
        await asyncio.sleep(duration_ms / 1000)
    async def look_angle(self, x_angle, y_angle, delay_ms=0):
        await asyncio.sleep(delay_ms / 1000)
        self.yaw += x_angle
        self.pitch += y_angle
    def apply_ws_move(self, x, z):
        self.x += x
        self.z += z
    def apply_ws_look(self, dx, dy):
        self.yaw += dx / 5.0
        self.pitch += -dy / 5.0


def test_cross_mode_environment_difference():
    env_ws = SimpleEnv()
    env_mcp = SimpleEnv()

    ctrl_ws = DummyController()
    strat_ws = PygameModeStrategy(ctrl_ws)
    strat_ws.handle_movement(1.0, 0.0)
    strat_ws.controller.send_command_sync({"type": "look", "movementX": 40, "movementY": 0})

    for cmd in ctrl_ws.sent_commands:
        if cmd["type"] == "move":
            env_ws.apply_ws_move(cmd["x"], cmd["z"])
        elif cmd["type"] == "look":
            env_ws.apply_ws_look(cmd["movementX"], cmd["movementY"])

    ctrl_mcp = DummyController()
    strat_mcp = MCPModeStrategy(ctrl_mcp)
    strat_mcp.handle_movement(1.0, 0.0)
    strat_mcp.controller.send_command_sync({"tool": "lookAngle", "parameters": {"xAngle": 8.0, "yAngle": 0.0, "speed": "normal"}})

    loop = asyncio.get_event_loop()
    for cmd in ctrl_mcp.sent_commands:
        if cmd["tool"] == "walk":
            loop.run_until_complete(env_mcp.walk(cmd["parameters"]["duration"]))
        elif cmd["tool"] == "lookAngle":
            loop.run_until_complete(env_mcp.look_angle(cmd["parameters"]["xAngle"], cmd["parameters"]["yAngle"]))

    assert (env_ws.x, env_ws.z) == (1.0, 0.0)
    assert (env_mcp.x, env_mcp.z) == (0.0, 0.0)
    assert env_ws.yaw == env_mcp.yaw


def test_cross_mode_multiple_directions():
    directions = [
        (1, 0),
        (0, 1),
        (-1, 0),
        (0, -1),
        (1, 1),
        (-1, 1),
        (-1, -1),
        (1, -1),
    ]

    for x, z in directions:
        env_ws = SimpleEnv()
        env_mcp = SimpleEnv()

        ctrl_ws = DummyController()
        strat_ws = PygameModeStrategy(ctrl_ws)
        strat_ws.handle_movement(x, z)

        for cmd in ctrl_ws.sent_commands:
            if cmd["type"] == "move":
                env_ws.apply_ws_move(cmd["x"], cmd["z"])

        ctrl_mcp = DummyController()
        strat_mcp = MCPModeStrategy(ctrl_mcp)
        strat_mcp.handle_movement(x, z)

        loop = asyncio.get_event_loop()
        for cmd in ctrl_mcp.sent_commands:
            if cmd["tool"] == "walk":
                loop.run_until_complete(env_mcp.walk(cmd["parameters"]["duration"]))

        assert (env_ws.x, env_ws.z) == (x, z)
        assert (env_mcp.x, env_mcp.z) == (0.0, 0.0)


def test_cross_mode_camera_consistency():
    env_ws = SimpleEnv()
    env_mcp = SimpleEnv()

    ctrl_ws = DummyController()
    PygameModeStrategy(ctrl_ws)
    ctrl_ws.send_command_sync({"type": "look", "movementX": 50, "movementY": -25})

    for cmd in ctrl_ws.sent_commands:
        if cmd["type"] == "look":
            env_ws.apply_ws_look(cmd["movementX"], cmd["movementY"])

    ctrl_mcp = DummyController()
    MCPModeStrategy(ctrl_mcp)
    ctrl_mcp.handle_other_commands(
        "lookAngle",
        xAngle=10.0,
        yAngle=5.0,
        speed="normal",
    )

    loop = asyncio.get_event_loop()
    for cmd in ctrl_mcp.sent_commands:
        if cmd["tool"] == "lookAngle":
            loop.run_until_complete(
                env_mcp.look_angle(
                    cmd["parameters"]["xAngle"],
                    cmd["parameters"]["yAngle"],
                )
            )

    assert env_ws.yaw == env_mcp.yaw == 10.0
    assert env_ws.pitch == env_mcp.pitch == 5.0

