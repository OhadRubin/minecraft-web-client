"""
You're right to question this! Let me look more carefully at which methods and attributes of `ConversationPanel` are actually being used.
Ran tool

You're actually quite perceptive! Let me analyze exactly what methods and attributes are being used:

## Actually Used Methods/Attributes:

From the grep results, here's what's **actually** being used:

### Methods:
1. **`capture_mcp_action(mcp_command)`** - Called in `interface.py`
2. **`convert_actions_to_mock_response()`** - Called in `interface.py` 
3. **`_render_messages(**api_params)`** - Called in `chain.py`

### Attributes:
1. **`human_demo_mode`** - Set to `True` in `interface.py`
2. **`captured_actions`** - Checked for existence in `interface.py`
3. **`messages`** - Set from `chain.py`

## What These Methods Actually Do:

Looking at the `ConversationPanel` class:

- **`capture_mcp_action()`** - Just appends to `self.captured_actions` list and prints
- **`convert_actions_to_mock_response()`** - Converts actions to mock tool calls and clears the list
- **`_render_messages()`** - Returns a mock response without making any real API calls

## Your Assessment is Largely Correct!

The `ConversationPanel` is essentially:
1. **A simple list wrapper** for `captured_actions` 
2. **A formatter** that converts actions to mock OpenAI-style responses
3. **A mock response generator** that avoids real API calls

The class could easily be simplified to just a few utility functions:
- `capture_action(action, actions_list)` 
- `actions_to_mock_response(actions_list)`
- `create_mock_response(content, tool_calls)`

You're right that it seems over-engineered for what it actually does. The main "value" is that it provides a consistent interface that mimics OpenAI's response format, but most of the class structure isn't really necessary for the functionality being used.

It's essentially a glorified action collector with a formatter method!
"""


from dataclasses import dataclass
from typing import List, Dict, Union, Any, Optional
import json
import time

@dataclass(frozen=True)
class Message:
    role: str
    content: Optional[Union[str, List[Dict[str, str]]]] = None
    tool_calls: Optional[List[Any]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    should_cache: bool = False

class ConversationPanel:
    """Manage conversation messages for display and human demonstrations."""

    def __init__(self):
        self.messages = []
        self.captured_actions = []
        self.human_demo_mode = True

    def capture_mcp_action(self, mcp_command):
        self.captured_actions.append(mcp_command)
        print(
            f"📝 Captured action: {mcp_command['tool']}({mcp_command['parameters']})"
        )

    def convert_actions_to_mock_response(self):
        if not self.captured_actions:
            return {
                "content": "I'll explore and take some actions in Minecraft.",
                "tool_calls": None,
            }

        action_descriptions = []
        tool_calls = []
        for i, action in enumerate(self.captured_actions):
            tool_name = action["tool"]
            params = action["parameters"]
            tool_call_id = f"call_{i}_{tool_name}"
            tool_calls.append(
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {"name": tool_name, "arguments": json.dumps(params)},
                }
            )
            if tool_name == "lookAngle":
                x_angle = params.get("xAngle", 0)
                y_angle = params.get("yAngle", 0)
                action_descriptions.append(
                    f"look around (x: {x_angle}°, y: {y_angle}°)"
                )
            elif tool_name == "walk":
                duration = params.get("duration", 1000)
                action_descriptions.append(f"move forward for {duration}ms")
            elif tool_name == "leftClick":
                action_descriptions.append("break/attack with left click")
            elif tool_name == "rightClick":
                action_descriptions.append("place/use with right click")
            elif tool_name == "setHotbarSlot":
                slot = params.get("slot", 0)
                action_descriptions.append(f"select hotbar slot {slot + 1}")
            else:
                action_descriptions.append(f"use {tool_name}")

        if len(action_descriptions) == 1:
            content = f"I'll {action_descriptions[0]} to explore the area."
        else:
            content = (
                f"I'll {', '.join(action_descriptions[:-1])} and {action_descriptions[-1]} to navigate and explore."
            )

        self.captured_actions.clear()
        return {"content": content, "tool_calls": tool_calls if tool_calls else None}

    async def _render_messages(self, **api_params):
        if self.messages:
            print(f"📄 Conversation has {len(self.messages)} messages")

        class MockResponse:
            def __init__(self, message_data):
                self.choices = [MockChoice(message_data)]
                self.usage = MockUsage()

        class MockChoice:
            def __init__(self, message_data):
                self.message = MockMessage(message_data)

        class MockMessage:
            def __init__(self, message_data):
                self.content = message_data["content"]
                self.tool_calls = message_data["tool_calls"]
                if self.tool_calls:
                    mock_tool_calls = []
                    for tc in self.tool_calls:
                        mock_tc = type(
                            "MockToolCall",
                            (),
                            {
                                "id": tc["id"],
                                "type": tc["type"],
                                "function": type(
                                    "MockFunction",
                                    (),
                                    {
                                        "name": tc["function"]["name"],
                                        "arguments": tc["function"]["arguments"],
                                    },
                                )(),
                            },
                        )()
                        mock_tool_calls.append(mock_tc)
                    self.tool_calls = mock_tool_calls

        class MockUsage:
            def __init__(self):
                self.prompt_tokens = 0
                self.completion_tokens = 0
                self.total_tokens = 0

        if self.human_demo_mode:
            message_data = self.convert_actions_to_mock_response()
        else:
            message_data = {
                "content": "MCP/Pygame mode - no OpenAI call made",
                "tool_calls": None,
            }

        return MockResponse(message_data)

def create_user_message(captured_actions):
    action_descriptions = []
    for action in captured_actions:
        tool_name = action["tool"]
        params = action["parameters"]
        if tool_name == "lookAngle":
            x_angle = params.get("xAngle", 0)
            y_angle = params.get("yAngle", 0)
            action_descriptions.append(
                f"look {x_angle:.1f}° horizontally, {y_angle:.1f}° vertically"
            )
        else:
            action_descriptions.append(f"use {tool_name}")

    user_message = f"I performed these actions: {', '.join(action_descriptions)}"
    return user_message
