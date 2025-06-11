import json
import importlib.util
from pathlib import Path

module_dir = Path(__file__).resolve().parents[1] / "mc_pygame_controller"

spec = importlib.util.spec_from_file_location("action_converter", module_dir / "action_converter.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)
ActionConverter = ac.ActionConverter



def test_convert_left_right_click():
    left = {"type": "documentMouseEvent", "button": 0, "action": "down"}
    right = {"type": "rightDown"}
    actions = [left, right]
    converted = ActionConverter.convert_pygame_actions_bulk(actions)
    assert converted == [
        {"tool": "leftClick", "parameters": {"duration": "short"}},
        {"tool": "rightClick", "parameters": {"duration": "short"}},
    ]


def test_ignore_mouse_up_event():
    actions = [
        {"type": "documentMouseEvent", "button": 0, "action": "down"},
        {"type": "documentMouseEvent", "button": 0, "action": "up"},
    ]
    result = ActionConverter.convert_pygame_actions_bulk(actions)
    assert result == [{"tool": "leftClick", "parameters": {"duration": "short"}}]


def test_convert_legacy_string_action():
    legacy_move = '{"move":{"x":0,"z":-1}}'
    result = ActionConverter.convert_pygame_actions_bulk([legacy_move])
    assert result == [{"tool": "walk", "parameters": {"duration": 1000}}]

    legacy_look = '{"look":{"movementX":10,"movementY":5}}'
    result = ActionConverter.convert_pygame_actions_bulk([legacy_look])
    assert result[0]["tool"] == "lookAngle"


def test_convert_move_and_look():
    actions = [
        {"type": "move", "x": 0.5, "z": 0.0},
        {"type": "look", "movementX": 10, "movementY": -5},
    ]
    result = ActionConverter.convert_pygame_actions_bulk(actions)
    assert result[0] == {"tool": "walk", "parameters": {"duration": 1000}}
    assert result[1] == {
        "tool": "lookAngle",
        "parameters": {"xAngle": 2.0, "yAngle": 1.0, "speed": "normal"},
    }


def test_convert_to_mcp_format_all():
    mapping = [
        ("jump", {"duration": "short"}, {"tool": "jump", "parameters": {"duration": "short"}}),
        ("sneak", {"state": True}, {"tool": "sneak", "parameters": {"state": True}}),
        ("sprint", {"state": False}, {"tool": "sprint", "parameters": {"state": False}}),
        (
            "toggleInventory",
            {},
            {"tool": "toggleInventory", "parameters": {}},
        ),
        ("dropItem", {"amount": 1}, {"tool": "dropItem", "parameters": {"amount": 1}}),
        (
            "swapHands",
            {},
            {"tool": "swapHands", "parameters": {}},
        ),
        (
            "setHotbarSlot",
            {"slot": 2},
            {"tool": "setHotbarSlot", "parameters": {"slot": 2}},
        ),
        ("walk", {"duration": 500}, {"tool": "walk", "parameters": {"duration": 500}}),
    ]
    for cmd, params, expected in mapping:
        assert ac.convert_to_mcp_format(cmd, params) == expected


def test_openai_format_consistency():
    actions = [
        {"type": "move", "x": 0.3, "z": 0.4},
        {"type": "look", "movementX": 5, "movementY": -5},
        {"type": "documentMouseEvent", "button": 0, "action": "down"},
    ]
    simple = ActionConverter.pygame_to_mcp_simple(actions)
    tools = ActionConverter.pygame_to_openai_tools(actions, "seq")
    assert len(simple) == len(tools)
    for s, t in zip(simple, tools):
        assert s["tool"] == t["function"]["name"]
        assert json.loads(t["function"]["arguments"]) == s["parameters"]


def test_convert_to_mcp_defaults():
    assert ac.convert_to_mcp_format("dropItem", {}) == {
        "tool": "dropItem",
        "parameters": {"amount": 1},
    }
    assert ac.convert_to_mcp_format("setHotbarSlot", {}) == {
        "tool": "setHotbarSlot",
        "parameters": {"slot": 0},
    }


def test_ignore_unknown_pygame_action():
    actions = [
        {"type": "foo", "x": 1},
        {"bar": "baz"},
    ]
    result = ActionConverter.convert_pygame_actions_bulk(actions)
    assert result == []
