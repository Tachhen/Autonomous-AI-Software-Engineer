import json
from pathlib import Path


def summarize(results_file="evaluation/results.json"):
    data = json.loads(Path(results_file).read_text())

    print(f"Tasks: {data['total_tasks']}")
    print(f"Successful: {data['successful_tasks']}")
    print(f"Failed: {data['failed_tasks']}")
    print(f"Success rate: {data['success_rate_percent']}%")
    print(f"Average agent time: {data['average_agent_time_seconds']}s")
