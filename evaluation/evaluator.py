import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv
from agent.agent import CodingAgent
from evaluation.tasks import TASKS


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / ".env")
PROJECTS = ROOT / "projects"
RESULTS_FILE = ROOT / "results.json"


def run_tests(workspace: Path):
    start = time.perf_counter()
    try:
        process = subprocess.run(
            ["python", "-m", "pytest", "-q"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "passed": process.returncode == 0,
            "return_code": process.returncode,
            "output": (process.stdout + "\n" + process.stderr).strip(),
            "time_seconds": round(time.perf_counter() - start, 2),
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "return_code": -1,
            "output": "pytest timed out after 60 seconds",
            "time_seconds": 60.0,
        }


def evaluate_task(task):
    template = PROJECTS / task["project"]

    with tempfile.TemporaryDirectory(prefix=f"agent_eval_{task['id']}_") as tmp:
        workspace = Path(tmp) / task["project"]
        shutil.copytree(template, workspace)

        before = run_tests(workspace)

        start = time.perf_counter()
        agent_error = None
        agent_result = None

        try:
            agent = CodingAgent(str(workspace))
            agent_result = agent.run(task["prompt"])
        except Exception as exc:
            agent_error = f"{type(exc).__name__}: {exc}"

        after = run_tests(workspace)

        result = {
            "task_id": task["id"],
            "project": task["project"],
            "success": after["passed"],
            "initial_tests_passed": before["passed"],
            "final_tests_passed": after["passed"],
            "initial_return_code": before["return_code"],
            "final_return_code": after["return_code"],
            "agent_time_seconds": round(time.perf_counter() - start, 2),
            "test_time_seconds": after["time_seconds"],
            "agent_error": agent_error,
            "agent_result": str(agent_result)[:4000] if agent_result is not None else None,
            "final_test_output": after["output"][:8000],
        }
        return result


def main():
    print("=" * 60)
    print(" AUTONOMOUS AGENT EVALUATION")
    print("=" * 60)

    results = []

    for index, task in enumerate(TASKS, start=1):
        print(f"\n[{index}/{len(TASKS)}] {task['id']}")

        result = evaluate_task(task)
        results.append(result)

        status = "PASS" if result["success"] else "FAIL"
        print(f"  {status}")
        print(f"  Time: {result['agent_time_seconds']}s")

        if result["agent_error"]:
            print(f"  Agent error: {result['agent_error']}")

    success_count = sum(r["success"] for r in results)
    success_rate = (success_count / len(results) * 100) if results else 0
    avg_time = (
        sum(r["agent_time_seconds"] for r in results) / len(results)
        if results else 0
    )

    summary = {
        "total_tasks": len(results),
        "successful_tasks": success_count,
        "failed_tasks": len(results) - success_count,
        "success_rate_percent": round(success_rate, 2),
        "average_agent_time_seconds": round(avg_time, 2),
        "tasks": results,
    }

    RESULTS_FILE.write_text(json.dumps(summary, indent=2))

    print("\n" + "-" * 60)
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Average Time: {avg_time:.2f}s")
    print(f"Results saved to: {RESULTS_FILE}")
    print("-" * 60)


if __name__ == "__main__":
    main()
