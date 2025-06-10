import importlib.util
import sys
from pathlib import Path

# Load the module directly from file to avoid running package __init__
module_path = Path(__file__).resolve().parent.parent / 'mc_pygame_controller' / 'action_converter.py'
spec = importlib.util.spec_from_file_location('action_converter', module_path)
action_converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(action_converter)
ActionConverter = action_converter.ActionConverter


def test_left_click_deduplication():
    actions = [
        {"type": "documentMouseEvent", "button": 0, "action": "down"},
        {"type": "documentMouseEvent", "button": 0, "action": "up"},
    ]
    mcp_actions = ActionConverter.convert_pygame_actions_bulk(actions)
    assert mcp_actions == [{"tool": "leftClick", "parameters": {"duration": "short"}}]


def test_right_click_conversion():
    actions = [
        {"type": "rightDown"},
        {"type": "rightUp"},
    ]
    mcp_actions = ActionConverter.convert_pygame_actions_bulk(actions)
    assert mcp_actions == [{"tool": "rightClick", "parameters": {"duration": "short"}}]
