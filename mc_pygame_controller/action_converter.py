"""
Action Conversion Engine - Eliminates Critical Code Duplication

This module provides a centralized converter for pygame actions to MCP format,
eliminating the identical business logic duplicated in:
- mode_strategy.py:342-433 (_convert_actions_to_mcp_format)
- action_sequence_tracker.py:177-253 (_convert_pygame_to_tool_calls)

Key Features:
- Single source of truth for all conversion calculations
- Multiple output format support (simple + OpenAI format)
- Consistent mathematical formulas and thresholds
"""

import json
from typing import Dict, List, Optional, Any


class ActionConverter:
    """Centralized converter for pygame actions to MCP format."""

    # Shared constants - single source of truth
    MOVEMENT_THRESHOLD = 0.1
    LOOK_THRESHOLD = 0.2
    SENSITIVITY = 5.0
    MAGNITUDE_DURATION_SCALE = 2000

    @staticmethod
    def convert_pygame_action(action: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert single pygame action to normalized MCP data.

        Args:
            action: Pygame action dict (e.g., {"type": "move", "x": 0.5, "z": 0.3})

        Returns:
            {"tool": str, "parameters": dict} or None if no conversion needed
        """
        if not isinstance(action, dict):
            return None

        action_type = action.get("type")

        if action_type == "move":
            return ActionConverter._convert_move_action(action)
        elif action_type == "look":
            return ActionConverter._convert_look_action(action)
        elif action_type == "documentMouseEvent" and action.get("button") == 0:
            # Only convert mouse down events, skip mouse up events to avoid duplicates
            if action.get("action") == "down":
                return ActionConverter._convert_left_click_action(action)
            return None
        elif action_type == "rightDown":
            return ActionConverter._convert_right_click_action(action)

        return None

    @staticmethod
    def _convert_move_action(action: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert move action with consistent magnitude/duration calculation."""
        x, z = action.get("x", 0), action.get("z", 0)

        if (
            abs(x) > ActionConverter.MOVEMENT_THRESHOLD
            or abs(z) > ActionConverter.MOVEMENT_THRESHOLD
        ):
            # Single source of truth for magnitude calculation
            magnitude = (x**2 + z**2) ** 0.5
            duration = int(magnitude * ActionConverter.MAGNITUDE_DURATION_SCALE)

            return {"tool": "walk", "parameters": {"duration": duration}}
        return None

    @staticmethod
    def _convert_look_action(action: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert look action with consistent sensitivity/angle calculation."""
        movement_x = action.get("movementX", 0)
        movement_y = action.get("movementY", 0)

        # Single source of truth for angle conversion
        x_angle = movement_x / ActionConverter.SENSITIVITY
        y_angle = -(movement_y / ActionConverter.SENSITIVITY)  # Invert Y axis

        if (
            abs(x_angle) > ActionConverter.LOOK_THRESHOLD
            or abs(y_angle) > ActionConverter.LOOK_THRESHOLD
        ):
            return {
                "tool": "lookAngle",
                "parameters": {
                    "xAngle": round(x_angle, 1),
                    "yAngle": round(y_angle, 1),
                    "speed": "normal",
                },
            }
        return None

    @staticmethod
    def _convert_left_click_action(action: Dict[str, Any]) -> Dict[str, Any]:
        """Convert left click action."""
        return {"tool": "leftClick", "parameters": {"duration": "short"}}

    @staticmethod
    def _convert_right_click_action(action: Dict[str, Any]) -> Dict[str, Any]:
        """Convert right click action."""
        return {"tool": "rightClick", "parameters": {"duration": "short"}}

    @staticmethod
    def convert_pygame_actions_bulk(actions: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert multiple pygame actions to MCP format.

        Args:
            actions: List of pygame actions (dict or string format)

        Returns:
            List of converted MCP actions (excluding None results)
        """
        mcp_actions = []

        for action in actions:
            # Handle dict-based commands (primary format)
            if isinstance(action, dict):
                converted = ActionConverter.convert_pygame_action(action)
                if converted:
                    mcp_actions.append(converted)

            # Handle legacy string-based commands
            elif isinstance(action, str):
                converted = ActionConverter._convert_string_action(action)
                if converted:
                    mcp_actions.append(converted)

        return mcp_actions

    @staticmethod
    def _convert_string_action(action_str: str) -> Optional[Dict[str, Any]]:
        """Convert legacy string-based actions with proper parsing."""
        try:
            if '"move":' in action_str:
                # Default duration for legacy move commands
                return {"tool": "walk", "parameters": {"duration": 1000}}

            elif '"look":' in action_str:
                # Parse JSON to extract actual look parameters
                action_data = json.loads(action_str)
                if "look" in action_data:
                    look_data = action_data["look"]
                    # Create a dict format and reuse the main conversion logic
                    dict_action = {
                        "type": "look",
                        "movementX": look_data.get("movementX", 0),
                        "movementY": look_data.get("movementY", 0),
                    }
                    return ActionConverter.convert_pygame_action(dict_action)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Could not parse legacy action: {action_str} - {e}")

        return None

    # Format Adapters - Different output requirements solved here

    @staticmethod
    def to_simple_format(conversions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format converter for mode_strategy.py usage.

        Returns: [{"tool": "walk", "parameters": {...}}, ...]
        """
        return conversions  # Already in the correct format

    @staticmethod
    def to_openai_format(
        conversions: List[Dict[str, Any]], sequence_id: str
    ) -> List[Dict[str, Any]]:
        """
        Format converter for action_sequence_tracker.py usage.

        Returns: OpenAI tool call format with IDs
        """
        tool_calls = []

        for i, conversion in enumerate(conversions):
            if conversion:
                tool_calls.append(
                    {
                        "id": f"call_{sequence_id}_{conversion['tool']}_{i}",
                        "type": "function",
                        "function": {
                            "name": conversion["tool"],
                            "arguments": json.dumps(conversion["parameters"]),
                        },
                    }
                )

        return tool_calls

    # Convenience methods for common usage patterns

    @staticmethod
    def pygame_to_mcp_simple(actions: List[Any]) -> List[Dict[str, Any]]:
        """Convenience method for mode_strategy.py."""
        conversions = ActionConverter.convert_pygame_actions_bulk(actions)
        return ActionConverter.to_simple_format(conversions)

    @staticmethod
    def pygame_to_openai_tools(
        actions: List[Any], sequence_id: str
    ) -> List[Dict[str, Any]]:
        """Convenience method for action_sequence_tracker.py."""
        conversions = ActionConverter.convert_pygame_actions_bulk(actions)
        return ActionConverter.to_openai_format(conversions, sequence_id)


# Validation helper for testing
def validate_conversion_consistency():
    """
    Validate that both output formats produce equivalent core data.
    This helps ensure refactoring doesn't break compatibility.
    """
    test_actions = [
        {"type": "move", "x": 0.5, "z": 0.3},
        {"type": "look", "movementX": 10, "movementY": -5},
        {"type": "documentMouseEvent", "button": 0},
        {"type": "rightDown"},
    ]

    # Test both formats
    simple_format = ActionConverter.pygame_to_mcp_simple(test_actions)
    openai_format = ActionConverter.pygame_to_openai_tools(test_actions, "test_seq")

    print(f"✅ Simple format: {len(simple_format)} actions")
    print(f"✅ OpenAI format: {len(openai_format)} tool calls")

    # Validate core data consistency
    for i, (simple, openai) in enumerate(zip(simple_format, openai_format)):
        simple_tool = simple["tool"]
        openai_tool = openai["function"]["name"]
        assert (
            simple_tool == openai_tool
        ), f"Tool mismatch at {i}: {simple_tool} != {openai_tool}"

        simple_params = simple["parameters"]
        openai_params = json.loads(openai["function"]["arguments"])
        assert simple_params == openai_params, f"Parameters mismatch at {i}"

    print("✅ Conversion consistency validated!")


def convert_to_mcp_format(command_type, params):
    """Convert pygame commands to MCP format"""
    # Simple mapping for clicks, movement, etc.
    if command_type == "left_click" or command_type == "leftClick":
        return {
            "tool": "leftClick",
            "parameters": {"duration": params.get("duration", "medium")},
        }
    elif command_type == "right_click" or command_type == "rightClick":
        return {
            "tool": "rightClick",
            "parameters": {"duration": params.get("duration", "medium")},
        }
    elif command_type == "walk":
        return {
            "tool": "walk",
            "parameters": {"duration": params.get("duration", 1000)},
        }
    elif command_type == "setHotbarSlot":
        return {
            "tool": "setHotbarSlot",
            "parameters": {"slot": params.get("slot", 0)},
        }
    elif command_type == "jump":
        return {
            "tool": "jump",
            "parameters": {"duration": params.get("duration", "short")},
        }
    elif command_type == "sneak":
        return {
            "tool": "sneak",
            "parameters": {"state": params.get("state", True)},
        }
    elif command_type == "sprint":
        return {
            "tool": "sprint",
            "parameters": {"state": params.get("state", True)},
        }
    elif command_type == "toggleInventory":
        return {
            "tool": "toggleInventory",
            "parameters": {},
        }
    elif command_type == "dropItem":
        return {
            "tool": "dropItem",
            "parameters": {"amount": params.get("amount", 1)},
        }
    elif command_type == "swapHands":
        return {
            "tool": "swapHands",
            "parameters": {},
        }
    # Add more mappings as needed
    return None


if __name__ == "__main__":
    validate_conversion_consistency()
