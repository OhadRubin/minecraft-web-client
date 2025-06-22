import json
import glob
from pathlib import Path
from typing import List

from structure_validator import check_tool_call_format


REQUIRED_TOP_LEVEL = ["session_id", "start_time", "end_time", "conversations"]
REQUIRED_CONV_FIELDS = [
    "conversation_id",
    "task_description",
    "start_time",
    "end_time",
    "duration",
    "messages",
]


def validate_session_file(filepath: str) -> List[str]:
    errors: List[str] = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"JSON decode error: {e}"]

    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    conversations = data.get("conversations", [])
    for idx, conv in enumerate(conversations):
        for field in REQUIRED_CONV_FIELDS:
            if field not in conv:
                errors.append(f"Conversation {idx} missing field: {field}")
        for midx, msg in enumerate(conv.get("messages", [])):
            if "role" not in msg:
                errors.append(f"Conversation {idx} message {midx} missing role")
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tidx, tc in enumerate(msg["tool_calls"]):
                    result = check_tool_call_format(tc)
                    if result != "Valid":
                        errors.append(
                            f"Conv {idx} msg {midx} tool {tidx}: {result}"
                        )
            if msg.get("role") == "tool" and "tool_call_id" not in msg:
                errors.append(f"Conversation {idx} message {midx} missing tool_call_id")
    return errors


def main():
    session_files = glob.glob("collected_trajectories/session_*.json")
    if not session_files:
        print("No session files found")
        return

    for file in session_files:
        errors = validate_session_file(file)
        if errors:
            print(f"{file}:")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"{file}: Valid")


if __name__ == "__main__":
    main()
