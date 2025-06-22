import sys
import pytest

# Import modules without executing mc_pygame_controller.__init__
sys.path.insert(0, 'mc_pygame_controller')
from action_handler import ActionHandler
from controller_state import ControllerState


class DummyStrategy:
    def __init__(self):
        self.calls = []

    def handle_simple_action(self, action_name, pygame_cmd=None, **params):
        self.calls.append((action_name, pygame_cmd, params))


class DummyController:
    def __init__(self):
        self.ui_manager = None
        self.look_path_tracker = None


def test_handle_hotbar_slot_basic():
    state = ControllerState()
    strategy = DummyStrategy()
    controller = DummyController()
    handler = ActionHandler(state, strategy, controller)

    handler.handle_hotbar_slot(0)
    assert strategy.calls == [(
        "setHotbarSlot",
        {"type": "setHotbarSlot", "slot": 0},
        {"slot": 0},
    )]
    assert state.current_hotbar_slot == 0
    assert state.last_hotbar_slot == 0


def test_handle_hotbar_slot_duplicate():
    state = ControllerState()
    strategy = DummyStrategy()
    controller = DummyController()
    handler = ActionHandler(state, strategy, controller)

    handler.handle_hotbar_slot(2)
    handler.handle_hotbar_slot(2)

    assert len(strategy.calls) == 1
    assert state.current_hotbar_slot == 2
    assert state.last_hotbar_slot == 2


def test_handle_hotbar_slot_change():
    state = ControllerState()
    strategy = DummyStrategy()
    controller = DummyController()
    handler = ActionHandler(state, strategy, controller)

    handler.handle_hotbar_slot(1)
    handler.handle_hotbar_slot(5)

    assert len(strategy.calls) == 2
    assert strategy.calls[1][2]["slot"] == 5
    assert state.current_hotbar_slot == 5
    assert state.last_hotbar_slot == 5
