import json
import os
from datetime import datetime


class AgentMemory:

    def __init__(self, path=".agent_memory.json"):

        self.path = os.path.abspath(path)

        self.data = {
            "task": None,
            "started_at": None,
            "actions": [],
            "files_read": [],
            "files_modified": [],
            "test_runs": [],
            "completed": False
        }

        self.load()

    def load(self):

        if not os.path.exists(self.path):
            return

        try:

            with open(
                self.path,
                "r",
                encoding="utf-8"
            ) as f:

                self.data = json.load(f)

        except (json.JSONDecodeError, OSError):

            # If memory is corrupted, start fresh.
            self.data = {
                "task": None,
                "started_at": None,
                "actions": [],
                "files_read": [],
                "files_modified": [],
                "test_runs": [],
                "completed": False
            }

    def save(self):

        with open(
            self.path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.data,
                f,
                indent=2
            )

    def start_task(self, task):

        self.data["task"] = task
        self.data["started_at"] = (
            datetime.now().isoformat()
        )

        self.data["completed"] = False

        self.save()

    def record_action(
        self,
        tool,
        arguments,
        result
    ):

        self.data["actions"].append({

            "timestamp":
                datetime.now().isoformat(),

            "tool": tool,

            "arguments": arguments,

            "result": str(result)
        })

        self.save()

    def record_file_read(self, path):

        if path not in self.data["files_read"]:

            self.data["files_read"].append(path)

        self.save()

    def record_file_modified(self, path):

        if path not in self.data["files_modified"]:

            self.data["files_modified"].append(path)

        self.save()

    def record_test_run(self, result):

        self.data["test_runs"].append({

            "timestamp":
                datetime.now().isoformat(),

            "result": result
        })

        self.save()

    def complete_task(self):

        self.data["completed"] = True

        self.save()

    def summary(self):

        return {

            "task":
                self.data["task"],

            "files_read":
                self.data["files_read"],

            "files_modified":
                self.data["files_modified"],

            "test_runs":
                len(self.data["test_runs"]),

            "completed":
                self.data["completed"]
        }

    def context(self):

        return json.dumps(
            self.data,
            indent=2
        )