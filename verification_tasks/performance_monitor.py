import argparse
import json
import time
from pathlib import Path

import psutil


def monitor_performance(output: Path, interval: float = 1.0) -> None:
    """Continuously record CPU and memory usage to ``output``."""
    data = {
        "memory_usage": [],
        "cpu_usage": [],
        "timestamps": [],
    }

    def save():
        output.write_text(json.dumps(data, indent=2))

    try:
        while True:
            data["memory_usage"].append(psutil.virtual_memory().percent)
            data["cpu_usage"].append(psutil.cpu_percent())
            data["timestamps"].append(time.time())
            time.sleep(interval)
            if len(data["timestamps"]) % 60 == 0:
                save()
    except KeyboardInterrupt:
        pass
    finally:
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor system performance during mc_pygame_controller tests")
    parser.add_argument("-o", "--output", default="performance_data.json", help="JSON file for collected stats")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Sampling interval in seconds")
    args = parser.parse_args()

    monitor_performance(Path(args.output), args.interval)
