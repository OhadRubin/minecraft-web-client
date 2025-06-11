import time
import types
import importlib.util
from pathlib import Path
import pytest

module_dir = Path(__file__).resolve().parents[1] / "mc_pygame_controller"

spec_ah = importlib.util.spec_from_file_location("action_handler", module_dir / "action_handler.py")
ah = importlib.util.module_from_spec(spec_ah)
spec_ah.loader.exec_module(ah)
ActionHandler = ah.ActionHandler

spec_cs = importlib.util.spec_from_file_location("controller_state", module_dir / "controller_state.py")
cs = importlib.util.module_from_spec(spec_cs)
spec_cs.loader.exec_module(cs)
ControllerState = cs.ControllerState

class DummyStrategy:
    def __init__(self):
        self.timed_actions = []
        self.toggle_actions = []
        self.simple_actions = []
        self.movements = []

    def handle_timed_action(self, action_name, duration, pygame_down_cmd=None, pygame_up_cmd=None, **kwargs):
        self.timed_actions.append((action_name, duration, pygame_down_cmd, pygame_up_cmd, kwargs))

    def handle_toggle_action(self, action_name, state, pygame_control=None):
        self.toggle_actions.append((action_name, state))

    def handle_simple_action(self, action_name, pygame_cmd=None, **params):
        self.simple_actions.append((action_name, params))

    def handle_movement(self, x, z):
        self.movements.append((x, z))


class DummyLookPathTracker:
    def __init__(self):
        self.movements = []
        self.mouse_tracking_active = True

    def add_movement(self, x, y):
        if self.mouse_tracking_active:
            self.movements.append((x, y))

    def clear_history(self):
        self.movements = []


class DummyController:
    def __init__(self):
        self.commands = []
        self.ui_manager = types.SimpleNamespace()
        self.look_path_tracker = DummyLookPathTracker()

    def send_command_sync(self, command):
        self.commands.append(command)

    def _handle_camera_drag_state(self, *args, **kwargs):
        pass


def create_handler():
    state = ControllerState(enable_logging=False)
    strategy = DummyStrategy()
    controller = DummyController()
    handler = ActionHandler(state, strategy, controller)
    return handler, state, strategy, controller


def test_calculate_duration_ranges():
    handler, state, strategy, controller = create_handler()
    now = time.time()
    assert handler._calculate_duration(None) == "medium"
    assert handler._calculate_duration(now - 0.05) == "very_short"
    assert handler._calculate_duration(now - 0.3) == "short"
    assert handler._calculate_duration(now - 1.0) == "medium"
    assert handler._calculate_duration(now - 2.0) == "long"
    assert handler._calculate_duration(now - 5.0) == "very_long"
    assert handler._calculate_duration(now - 11.0) == "very_very_long"


def test_left_click_action_short_duration():
    handler, state, strategy, controller = create_handler()
    handler.handle_left_click(True)
    # simulate a 0.2s hold
    state.action_states["left_click"]["start_time"] -= 0.2
    handler.handle_left_click(False)
    assert not state.action_states["left_click"]["active"]
    assert strategy.timed_actions[0][0] == "leftClick"
    assert strategy.timed_actions[0][1] == "short"


def test_toggle_actions():
    handler, state, strategy, controller = create_handler()
    handler.handle_sneak(True)
    handler.handle_sneak(True)  # no change
    handler.handle_sneak(False)
    assert strategy.toggle_actions == [("sneak", True), ("sneak", False)]

    handler.handle_sprint(True)
    handler.handle_sprint(False)
    assert strategy.toggle_actions[-2:] == [("sprint", True), ("sprint", False)]


def test_simple_actions():
    handler, state, strategy, controller = create_handler()
    handler.handle_inventory()
    handler.handle_hotbar_slot(2)
    handler.handle_drop_item()
    handler.handle_swap_hands()
    actions = [a[0] for a in strategy.simple_actions]
    assert actions == [
        "toggleInventory",
        "setHotbarSlot",
        "dropItem",
        "swapHands",
    ]


def test_jump_action_duration():
    handler, state, strategy, controller = create_handler()
    handler.handle_jump(True)
    # simulate 0.6s hold
    state.action_states["jump"]["start_time"] -= 0.6
    handler.handle_jump(False)
    assert strategy.timed_actions[-1][0] == "jump"
    assert strategy.timed_actions[-1][1] == "short"


def test_detect_key_edge():
    handler, state, _, _ = create_handler()
    just_pressed, just_released = handler._detect_key_edge("space", True)
    assert just_pressed and not just_released
    just_pressed, just_released = handler._detect_key_edge("space", True)
    assert not just_pressed and not just_released
    just_pressed, just_released = handler._detect_key_edge("space", False)
    assert not just_pressed and just_released


def test_process_edge_detections_inventory_hotbar():
    handler, state, strategy, controller = create_handler()
    from collections import defaultdict
    import pygame

    keys = defaultdict(lambda: False)
    keys[pygame.K_2] = True
    keys[pygame.K_q] = True
    keys[pygame.K_f] = True
    keys[pygame.K_e] = True

    handler.process_edge_detections(keys)

    actions = [a[0] for a in strategy.simple_actions]
    assert actions == ["setHotbarSlot", "dropItem", "swapHands", "toggleInventory"]
    assert state.current_hotbar_slot == 1
    assert state.inventory_open


def test_handle_camera_look_modes():
    handler, state, strategy, controller = create_handler()
    state.mode = "pygame"
    handler.handle_camera_look(1, -2)
    assert controller.look_path_tracker.movements[-1] == (2, -4)
    assert controller.commands[-1] == {"type": "look", "movementX": 2, "movementY": -4}

    controller.commands.clear()
    state.mode = "mcp"
    handler.handle_camera_look(1, -2)
    assert controller.look_path_tracker.movements[-1] == (2, -4)
    assert controller.commands == []


def test_handle_clear_path():
    handler, state, strategy, controller = create_handler()
    controller.look_path_tracker.movements = [(1, 1), (2, 2)]
    handler.handle_clear_path()
    assert controller.look_path_tracker.movements == []


def test_process_actions_dispatch():
    handler, state, strategy, controller = create_handler()
    actions = [
        ("movement", (0.4, -0.2)),
        ("camera_look", (1, -1)),
        ("left_click", True),
        ("left_click", False),
        ("clear_path_pressed", None),
    ]
    controller.look_path_tracker.movements = [(5, 5)]
    handler.process_actions(actions)
    assert strategy.movements[0] == (0.4, -0.2)
    assert controller.look_path_tracker.movements == []
    assert strategy.timed_actions[-1][0] == "leftClick"


class DummyBtn:
    def __init__(self):
        self.is_pressed = False


def test_left_click_keyboard_or_button():
    handler, state, strategy, controller = create_handler()
    controller.ui_manager.left_click_btn = DummyBtn()

    # Trigger via keyboard
    handler._handle_left_click_keyboard(True)
    state.action_states["left_click"]["start_time"] -= 0.3
    handler._handle_left_click_keyboard(False)

    # Trigger via button
    controller.ui_manager.left_click_btn.is_pressed = True
    handler._handle_left_click_keyboard(False)
    state.action_states["left_click"]["start_time"] -= 0.2
    controller.ui_manager.left_click_btn.is_pressed = False
    handler._handle_left_click_keyboard(False)

    assert len(strategy.timed_actions) == 2
    assert strategy.timed_actions[0][1] == "short"
    assert strategy.timed_actions[1][1] == "short"


def test_right_click_keyboard_or_button():
    handler, state, strategy, controller = create_handler()
    controller.ui_manager.right_click_btn = DummyBtn()

    # Trigger via keyboard
    handler._handle_right_click_keyboard(True)
    state.action_states["right_click"]["start_time"] -= 0.25
    handler._handle_right_click_keyboard(False)

    # Trigger via button
    controller.ui_manager.right_click_btn.is_pressed = True
    handler._handle_right_click_keyboard(False)
    state.action_states["right_click"]["start_time"] -= 0.18
    controller.ui_manager.right_click_btn.is_pressed = False
    handler._handle_right_click_keyboard(False)

    assert len(strategy.timed_actions) == 2
    assert all(a[0] == "rightClick" for a in strategy.timed_actions)


def test_inventory_toggle_context():
    handler, state, strategy, _ = create_handler()
    handler.handle_inventory()
    assert state.inventory_open and state.current_context == "inventory"
    handler.handle_inventory()
    assert not state.inventory_open and state.current_context == "world"
    actions = [a[0] for a in strategy.simple_actions]
    assert actions == ["toggleInventory", "toggleInventory"]


def test_rapid_sneak_toggle_sequence():
    handler, state, strategy, _ = create_handler()
    handler.handle_sneak(True)
    handler.handle_sneak(False)
    handler.handle_sneak(True)
    handler.handle_sneak(False)
    assert strategy.toggle_actions == [
        ("sneak", True),
        ("sneak", False),
        ("sneak", True),
        ("sneak", False),
    ]


def test_process_actions_unknown_action():
    handler, state, strategy, _ = create_handler()
    handler.process_actions([("unknown_action", True)])
    assert not strategy.timed_actions
    assert not strategy.toggle_actions
    assert not strategy.simple_actions


def test_jump_action_long_duration():
    handler, state, strategy, _ = create_handler()
    handler.handle_jump(True)
    state.action_states["jump"]["start_time"] -= 3.2
    handler.handle_jump(False)
    assert strategy.timed_actions[-1][0] == "jump"
    assert strategy.timed_actions[-1][1] == "long"


def test_handle_movement_threshold():
    handler, state, strategy, _ = create_handler()
    handler.handle_movement(0.05, 0.05)
    handler.handle_movement(0.2, 0.0)
    handler.handle_movement(0.21, 0.02)
    handler.handle_movement(0.35, 0.15)
    assert strategy.movements == [(0.2, 0.0), (0.35, 0.15)]


def test_camera_drag_tracking_respects_active():
    handler, state, strategy, controller = create_handler()
    controller.look_path_tracker.mouse_tracking_active = False
    handler.handle_camera_look(2, 2)
    assert controller.look_path_tracker.movements == []
    controller.look_path_tracker.mouse_tracking_active = True
    handler.handle_camera_look(1, -1)
    assert controller.look_path_tracker.movements[-1] == (2, -2)
