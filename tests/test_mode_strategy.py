import importlib.util
import sys
import types
from pathlib import Path

# Provide dummy modules to satisfy imports expected by mode_strategy
mcp_client_mod = types.ModuleType("mcp_client")
mcp_client_mod.Server = object
sys.modules.setdefault("mcp_client", mcp_client_mod)
chain_mod = types.ModuleType("chain")
chain_mod.PygameMCPAsyncMessageChain = object
sys.modules.setdefault("chain", chain_mod)

module_dir = Path(__file__).resolve().parents[1] / "mc_pygame_controller"

spec_ms = importlib.util.spec_from_file_location("mode_strategy", module_dir / "mode_strategy.py")
ms = importlib.util.module_from_spec(spec_ms)
spec_ms.loader.exec_module(ms)
PygameModeStrategy = ms.PygameModeStrategy
MCPModeStrategy = ms.MCPModeStrategy

spec_ac = importlib.util.spec_from_file_location("action_converter", module_dir / "action_converter.py")
ac = importlib.util.module_from_spec(spec_ac)
spec_ac.loader.exec_module(ac)
convert_to_mcp_format = ac.convert_to_mcp_format

class DummyController:
    def __init__(self):
        self.commands = []
        self.other_commands = []
        self.logged = []
        self.last_moved_in_mcp_mode = 0
        self.enable_logging = False
        self.action_handler = types.SimpleNamespace(
            _log_mcp_command=lambda tool, params: self.logged.append({"tool": tool, "parameters": params})
        )

    def send_command_sync(self, command):
        self.commands.append(command)

    def handle_other_commands(self, command_type, **params):
        mcp_cmd = convert_to_mcp_format(command_type, params)
        if mcp_cmd:
            self.other_commands.append(mcp_cmd)


def test_timed_action_equivalence():
    py_ctrl = DummyController()
    mcp_ctrl = DummyController()
    py_strategy = PygameModeStrategy(py_ctrl)
    mcp_strategy = MCPModeStrategy(mcp_ctrl)

    py_strategy.handle_timed_action(
        "leftClick",
        "short",
        {"type": "leftDown"},
        {"type": "leftUp"},
    )
    mcp_strategy.handle_timed_action("leftClick", "short")

    assert py_ctrl.logged[0] == mcp_ctrl.other_commands[0]
    assert py_ctrl.commands == [{"type": "leftDown"}, {"type": "leftUp"}]


def test_toggle_action_equivalence():
    py_ctrl = DummyController()
    mcp_ctrl = DummyController()
    py_strategy = PygameModeStrategy(py_ctrl)
    mcp_strategy = MCPModeStrategy(mcp_ctrl)

    py_strategy.handle_toggle_action("sneak", True, "sneak")
    mcp_strategy.handle_toggle_action("sneak", True)

    assert py_ctrl.logged[0] == mcp_ctrl.other_commands[0]
    assert py_ctrl.commands[0] == {"type": "control", "control": "sneak", "state": True}

def test_simple_action_equivalence():
    py_ctrl = DummyController()
    mcp_ctrl = DummyController()
    py_strategy = PygameModeStrategy(py_ctrl)
    mcp_strategy = MCPModeStrategy(mcp_ctrl)

    py_strategy.handle_simple_action("toggleInventory", {"type": "inventory"})
    mcp_strategy.handle_simple_action("toggleInventory")

    py_strategy.handle_simple_action(
        "setHotbarSlot", {"type": "hotbar", "slot": 3}, slot=3
    )
    mcp_strategy.handle_simple_action("setHotbarSlot", slot=3)

    assert py_ctrl.logged[0] == mcp_ctrl.other_commands[0]
    assert py_ctrl.logged[1] == mcp_ctrl.other_commands[1]
    assert py_ctrl.commands == [
        {"type": "inventory"},
        {"type": "hotbar", "slot": 3},
    ]
