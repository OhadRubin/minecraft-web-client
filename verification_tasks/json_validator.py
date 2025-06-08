import json
import sys
from pathlib import Path


def validate_json_file(filepath: str) -> bool:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"\u2705 {filepath}: Valid JSON")
        return True
    except json.JSONDecodeError as e:
        print(f"\u274C {filepath}: JSON Error - {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python json_validator.py <file1> [file2 ...]")
        sys.exit(1)

    for file in sys.argv[1:]:
        validate_json_file(file)
