import os
import sys
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

import importlib.util

def _load_module(module_path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

action_handler_mod = _load_module('mc_pygame_controller/action_handler.py', 'action_handler')
controller_state_mod = _load_module('mc_pygame_controller/controller_state.py', 'controller_state')

ActionHandler = action_handler_mod.ActionHandler
ControllerState = controller_state_mod.ControllerState

class DummyStrategy:
    def __init__(self):
        self.handle_timed_action = MagicMock()

# Helper controller stub
class DummyController:
    def __init__(self, state):
        self.state = state
        self.ui_manager = SimpleNamespace()  # not used
        self.sent_commands = []

    def send_command_sync(self, cmd):
        self.sent_commands.append(cmd)

@pytest.fixture
def setup_action_handler(monkeypatch):
    state = ControllerState(enable_logging=False)
    strategy = DummyStrategy()
    controller = DummyController(state)
    handler = ActionHandler(state, strategy, controller)
    return handler, strategy, controller

def test_jump_action_triggers_once(monkeypatch, setup_action_handler):
    handler, strategy, controller = setup_action_handler

    # Mock time.time to control duration calculation
    times = [1.0]
    monkeypatch.setattr(time, "time", lambda: times[0])

    # Press jump
    handler._handle_jump_action(True)
    # No call yet because still pressed
    assert strategy.handle_timed_action.call_count == 0

    # Advance time and release
    times[0] = 1.2
    handler._handle_jump_action(False)

    # Ensure handle_timed_action called once with action name "jump"
    strategy.handle_timed_action.assert_called_once()
    action_name, duration = strategy.handle_timed_action.call_args[0][:2]
    assert action_name == "jump"
    # Duration should be "short" for 200ms hold
    assert duration == "short"

