import sys
import os
import time
import pytest

# Allow importing modules without triggering package-level imports that require
# optional dependencies.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mc_pygame_controller"))

from action_handler import ActionHandler
from controller_state import ControllerState


class MockStrategy:
    def __init__(self):
        self.timed_calls = []

    # Only the methods used by ActionHandler are implemented
    def handle_timed_action(self, action_name, duration, pygame_down_cmd=None, pygame_up_cmd=None, **kwargs):
        self.timed_calls.append((action_name, duration))

    def handle_movement(self, x, z):
        pass

    def handle_toggle_action(self, action_name, state, pygame_control=None):
        pass

    def handle_simple_action(self, action_name, pygame_cmd=None, **params):
        pass


class MockController:
    def __init__(self):
        self.state = ControllerState()
        self.enable_logging = False


@pytest.fixture
def jump_handler():
    controller = MockController()
    strategy = MockStrategy()
    handler = ActionHandler(controller.state, strategy, controller)
    return handler, strategy


def test_single_spacebar_jump(jump_handler):
    handler, strategy = jump_handler
    handler.handle_jump(True)
    time.sleep(0.05)
    handler.handle_jump(False)
    assert len(strategy.timed_calls) == 1
    assert strategy.timed_calls[0][0] == "jump"


def test_held_spacebar_single_action(jump_handler):
    handler, strategy = jump_handler
    handler.handle_jump(True)
    time.sleep(0.2)
    handler.handle_jump(False)
    assert len(strategy.timed_calls) == 1
    assert strategy.timed_calls[0][0] == "jump"


def test_rapid_spacebar_taps(jump_handler):
    handler, strategy = jump_handler
    for _ in range(3):
        handler.handle_jump(True)
        time.sleep(0.05)
        handler.handle_jump(False)
    assert len(strategy.timed_calls) == 3
    for call in strategy.timed_calls:
        assert call[0] == "jump"
