import asyncio
import time
import sys
import types
import pytest

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

look_path_path = os.path.join(base_dir, "mc_pygame_controller", "look_path.py")
spec2 = importlib.util.spec_from_file_location("mc_pygame_controller.look_path", look_path_path)
look_path = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(look_path)
dummy_pkg.look_path = look_path
sys.modules["mc_pygame_controller.look_path"] = look_path

from mc_pygame_controller.mode_strategy import PygameModeStrategy, MCPModeStrategy
from mc_pygame_controller.action_converter import ActionConverter
from mc_pygame_controller.look_path import LookPathTracker


class DummyController:
    def __init__(self):
        self.sent_commands = []
        self.last_moved_in_mcp_mode = 0
        self.enable_logging = False

    def send_command_sync(self, command):
        self.sent_commands.append(command)

    def handle_other_commands(self, action_name, **params):
        self.sent_commands.append({"tool": action_name, "parameters": params})


class DummyEnvironment:
    def __init__(self):
        self.x = 0
        self.yaw = 0.0
        self.pitch = 0.0

    async def walk(self, duration_ms):
        await asyncio.sleep(duration_ms / 1000)
        self.x += 1

    async def look_angle(self, x_angle, y_angle, delay_ms=0):
        await asyncio.sleep(delay_ms / 1000)
        self.yaw += x_angle
        self.pitch += y_angle

    async def get_status(self):
        return {"yaw": self.yaw, "pitch": self.pitch, "x": self.x}


def test_movement_direction_loss():
    dirs = [
        (1, 0),
        (0, 1),
        (-1, 0),
        (0, -1),
        (1, 1),
        (-1, 1),
        (-1, -1),
        (1, -1),
    ]

    for x, z in dirs:
        controller = DummyController()
        strat = PygameModeStrategy(controller)
        strat.handle_movement(x, z)
        assert controller.sent_commands[-1] == {"type": "move", "x": x, "z": z}

        controller = DummyController()
        strat = MCPModeStrategy(controller)
        strat.handle_movement(x, z)
        assert controller.sent_commands[-1] == {
            "tool": "walk",
            "parameters": {"duration": 1000},
        }


def test_camera_sensitivity_conversion():
    for delta in [10, 25, 50, 100]:
        scaled = delta * 2
        action = {"type": "look", "movementX": scaled, "movementY": 0}
        converted = ActionConverter.convert_pygame_action(action)
        expected = {
            "tool": "lookAngle",
            "parameters": {"xAngle": round(scaled / 5.0, 1), "yAngle": 0.0, "speed": "normal"},
        }
        assert converted == expected


def test_look_path_tracker_matches_environment():
    env = DummyEnvironment()
    tracker = LookPathTracker(sensitivity=5.0, enable_logging=False, mode="mcp")
    tracker.set_execution_callback(lambda cmd: asyncio.get_event_loop().create_task(env.look_angle(cmd["parameters"]["xAngle"], cmd["parameters"]["yAngle"])))

    tracker.start_mouse_tracking()
    for dx, dy in [(10, 0), (10, 0), (0, -5), (15, 0)]:
        tracker.add_movement(dx, dy)
    tracker.stop_mouse_tracking()

    # Ensure the command executed
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))

    stats = tracker.get_current_stats()
    assert stats is None
    status = asyncio.get_event_loop().run_until_complete(env.get_status())
    assert round(status["yaw"], 1) == 7.0
    assert round(status["pitch"], 1) == 1.0


def test_async_action_timing():
    env = DummyEnvironment()

    async def run():
        start = time.time()
        await env.walk(200)
        assert time.time() - start >= 0.2
        await env.look_angle(5.0, 0.0, delay_ms=100)
        status = await env.get_status()
        assert status["x"] == 1
        assert status["yaw"] == 5.0
        assert status["pitch"] == 0.0
        assert time.time() - start >= 0.3

    asyncio.get_event_loop().run_until_complete(run())

def test_camera_sensitivity_signed():
    for dx, dy in [(10, 0), (-10, 0), (0, 10), (0, -10)]:
        scaled_x = dx * 2
        scaled_y = dy * 2
        action = {"type": "look", "movementX": scaled_x, "movementY": scaled_y}
        converted = ActionConverter.convert_pygame_action(action)
        expected = {
            "tool": "lookAngle",
            "parameters": {
                "xAngle": round(scaled_x / 5.0, 1),
                "yAngle": round(-scaled_y / 5.0, 1),
                "speed": "normal",
            },
        }
        assert converted == expected


def test_look_path_tracker_multiple_drags():
    env = DummyEnvironment()
    tracker = LookPathTracker(sensitivity=5.0, enable_logging=False, mode="mcp")
    tracker.set_execution_callback(lambda cmd: asyncio.get_event_loop().create_task(env.look_angle(cmd["parameters"]["xAngle"], cmd["parameters"]["yAngle"])))

    tracker.start_mouse_tracking()
    tracker.add_movement(10, 0)
    tracker.stop_mouse_tracking()
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))

    tracker.start_mouse_tracking()
    tracker.add_movement(-5, 5)
    tracker.stop_mouse_tracking()
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))

    status = asyncio.get_event_loop().run_until_complete(env.get_status())
    assert round(status["yaw"], 1) == 1.0
    assert round(status["pitch"], 1) == -1.0

