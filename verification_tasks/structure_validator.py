import json


def check_tool_call_format(tool_call: dict) -> str:
    required = ["id", "type", "function"]
    function_required = ["name", "arguments"]

    for field in required:
        if field not in tool_call:
            return f"Missing tool_call field: {field}"

    function = tool_call.get("function", {})
    for field in function_required:
        if field not in function:
            return f"Missing function field: {field}"

    try:
        json.loads(function.get("arguments", ""))
    except Exception:
        return "Invalid arguments JSON string"

    return "Valid"


if __name__ == "__main__":
    import sys

    for file in sys.argv[1:]:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for conv in data.get("conversations", []):
            for msg in conv.get("messages", []):
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        result = check_tool_call_format(tc)
                        print(f"{file} {tc.get('id','?')}: {result}")
