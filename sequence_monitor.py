"""Utility script to monitor console output for sequence tracking events."""
import re
import sys
import time


CREATION_RE = re.compile(r"Started tracking sequence (\S+)")
COMPLETION_RE = re.compile(r"Sequence (\S+) complete")


def monitor_console_output(stream=sys.stdin):
    sequences = {}
    for line in stream:
        line = line.rstrip()
        print(line)
        match = CREATION_RE.search(line)
        if match:
            sequences[match.group(1)] = time.time()
            continue
        match = COMPLETION_RE.search(line)
        if match:
            seq_id = match.group(1)
            start = sequences.pop(seq_id, None)
            if start:
                duration = time.time() - start
                print(f"[monitor] {seq_id} completed in {duration:.2f}s")
            continue
        # check for hanging sequences every iteration
        now = time.time()
        for seq_id, start in list(sequences.items()):
            if now - start > 5:
                print(f"[monitor] warning: {seq_id} incomplete after {now-start:.1f}s")
                sequences.pop(seq_id)


if __name__ == "__main__":
    monitor_console_output()
