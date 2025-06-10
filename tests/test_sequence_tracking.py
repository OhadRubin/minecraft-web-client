import importlib.util
import pathlib
import sys
import types

base = pathlib.Path(__file__).resolve().parent.parent / "mc_pygame_controller"

# Minimal stub for PygameMCPAsyncMessageChain
class StubChain:
    def __init__(self):
        self.messages = []

    def user(self, content):
        self.messages.append(("user", content))
        return self

    def bot(self, content="", tool_calls=None):
        self.messages.append(("assistant", tool_calls))
        return self

    def tool(self, content="", tool_call_id="", name=""):
        self.messages.append(("tool", name))
        return self

    def to_dict(self):
        return {"messages": self.messages}

sys.modules["chain"] = types.SimpleNamespace(PygameMCPAsyncMessageChain=StubChain)

# Load action_converter so relative import works
spec_conv = importlib.util.spec_from_file_location("action_converter", base / "action_converter.py")
conv_module = importlib.util.module_from_spec(spec_conv)
spec_conv.loader.exec_module(conv_module)
sys.modules["action_converter"] = conv_module

spec_tracker = importlib.util.spec_from_file_location("action_sequence_tracker", base / "action_sequence_tracker.py")
tracker_module = importlib.util.module_from_spec(spec_tracker)
spec_tracker.loader.exec_module(tracker_module)
ActionSequenceTracker = tracker_module.ActionSequenceTracker


def test_sequence_complete_single_action():
    tracker = ActionSequenceTracker()
    seq_id = tracker.start_sequence([{"type": "move", "x": 1, "z": 0}], "test")
    assert tracker.active_sequences[seq_id].expected_responses == 2

    tracker.add_mcp_response(seq_id, {"tool": "walk", "content": "ok"})
    assert not tracker.is_sequence_complete(seq_id)
    tracker.add_mcp_response(seq_id, {"tool": "getBotStatus", "content": "status"})
    assert tracker.is_sequence_complete(seq_id)

    seq = tracker.complete_sequence(seq_id)
    chain = tracker.build_conversation_chain(seq)
    assert len(chain.messages) == 3
