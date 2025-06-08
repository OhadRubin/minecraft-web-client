import pytest

from mc_pygame_controller.action_handler import ActionHandler
from mc_pygame_controller.controller_state import ControllerState

class DummyStrategy:
    def __init__(self):
        self.calls = []
    def handle_toggle_action(self, action_name, state, pygame_control=None):
        self.calls.append((action_name, state))

class DummyController:
    def __init__(self, state):
        self.state = state
        self.ui_manager = None


def test_sneak_toggle():
    state = ControllerState()
    strategy = DummyStrategy()
    controller = DummyController(state)
    handler = ActionHandler(state, strategy, controller)

    handler.handle_sneak(True)
    assert strategy.calls == [("sneak", True)]
    handler.handle_sneak(True)
    assert strategy.calls == [("sneak", True)]  # no duplicate when same state
    handler.handle_sneak(False)
    assert strategy.calls == [("sneak", True), ("sneak", False)]


def test_sprint_toggle():
    state = ControllerState()
    strategy = DummyStrategy()
    controller = DummyController(state)
    handler = ActionHandler(state, strategy, controller)

    handler.handle_sprint(True)
    handler.handle_sprint(False)
    assert strategy.calls == [("sprint", True), ("sprint", False)]
