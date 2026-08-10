import json
import os

from openai import OpenAI

from agent.tools import RepositoryTools


class CodingAgent:

    def __init__(self, workspace):
        self.workspace = os.path.abspath(workspace)

        self.tools = RepositoryTools(self.workspace)

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            timeout=60.0
        )

    def tool_definitions(self):

        return [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List all files in the repository. This must be called before inspecting or editing files.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read an existing file. You must read a file before editing it.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Exact relative path returned by list_files."
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Replace the complete contents of an existing SOURCE CODE file. Never use this tool to modify tests unless explicitly requested.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Exact relative path of the source file."
                            },
                            "content": {
                                "type": "string",
                                "description": "Complete new contents of the source file."
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_tests",
                    "description": "Run the repository test suite and return the results.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    def execute_tool(self, name, arguments):

        print(f"\n[TOOL] {name}")
        print(f"[ARGS] {arguments}")

        if name == "list_files":
            return self.tools.list_files()

        if name == "read_file":
            return self.tools.read_file(arguments["path"])

        if name == "edit_file":

            path = arguments["path"]

            # Safety rule:
            # Never allow the agent to modify tests.
            if (
                path.startswith("tests/")
                or path.startswith("test_")
                or "/tests/" in path
            ):
                return (
                    "ERROR: Tests cannot be modified by the agent. "
                    "Modify the source code instead."
                )

            return self.tools.edit_file(
                path,
                arguments["content"]
            )

        if name == "run_tests":

            result = self.tools.run_tests()

            return json.dumps(result)

        return f"Unknown tool: {name}"

    def run(self, task):

        messages = [
            {
                "role": "system",
                "content": """
You are an autonomous AI software engineer.

You work directly on a software repository.

Your job is to solve the user's software engineering task.

AVAILABLE TOOLS:

1. list_files
   Discover the repository.

2. read_file
   Read an existing file.

3. edit_file
   Modify SOURCE CODE.

4. run_tests
   Run the test suite.

STRICT RULES:

1. ALWAYS call list_files FIRST.

2. ALWAYS use the EXACT paths returned by list_files.

3. NEVER guess file paths.

4. ALWAYS read a file before editing it.

5. NEVER modify tests unless the user explicitly asks you to modify tests.

6. When a test fails, identify the SOURCE CODE responsible for the failure.

7. Make the SMALLEST possible source-code change.

8. Do not add unnecessary classes, functions, main methods,
   unittest code, or features.

9. After editing source code, ALWAYS run the tests.

10. If tests fail, inspect the failure and make another source-code fix.

11. STOP once the existing tests pass.

Example:

calculator.py:

def add(a, b):
    return a - b

tests/test_calculator.py:

from calculator import add

def test_add():
    assert add(2, 3) == 5

The correct solution is:

calculator.py:

def add(a, b):
    return a + b

The test must NOT be changed.
""".strip()
            },
            {
                "role": "user",
                "content": task
            }
        ]

        tools = self.tool_definitions()

        for iteration in range(8):

            print(f"\n[AGENT ITERATION {iteration + 1}]")

            response = self.client.chat.completions.create(
                model="openrouter/free",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )

            message = response.choices[0].message

            if message.content:
                print("\n[AI]")
                print(message.content)

            if not message.tool_calls:
                return message.content or "Agent finished."

            messages.append(message)

            for tool_call in message.tool_calls:

                name = tool_call.function.name

                try:
                    arguments = json.loads(
                        tool_call.function.arguments
                    )
                except json.JSONDecodeError:
                    arguments = {}

                result = self.execute_tool(
                    name,
                    arguments
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    }
                )

        return (
            "Agent stopped after reaching the maximum "
            "number of iterations."
        )