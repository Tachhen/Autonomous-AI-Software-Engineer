import json
import os
from openai import OpenAI
from agent.tools import RepositoryTools
from rag.retriever import CodeRetriever
from memory.memory import AgentMemory
from agent.planner import Planner

class CodingAgent:

    def __init__(self, workspace):

        self.workspace = os.path.abspath(workspace)
        self.tools = RepositoryTools(self.workspace)
        self.retriever = CodeRetriever()
        self.memory = AgentMemory()
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            timeout=60.0
        )
        self.planner=Planner(self.client)

    #Tools
    def tool_definitions(self):
        return [
            #LIST FILES
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": (
                        "Gets a list of all files in the repository. "
                        "Use this before inspecting or editing files."
                        "or editing files."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            #READ FILE
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": (
                        "Read an existing file. "
                        "You must read a file before editing it."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": (
                                    "Exact relative path returned "
                                    "by list_files."
                                )
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            #SEARCH CODE
            {
                "type": "function",
                "function": {
                    "name": "search_code",
                    "description": (
                        "Semantically search the repository for "
                        "code relevant to the current task. "
                        "Use this when you need to locate relevant "
                        "code, functions, classes, or logic."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": (
                                    "Natural language description "
                                    "of the code or functionality "
                                    "you are looking for."
                                )
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            #EDIT FILE
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": (
                        "Replace the complete contents of an "
                        "existing SOURCE CODE file. "
                        "Never use this tool to modify tests "
                        "unless explicitly requested."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": (
                                    "Exact relative path of the "
                                    "source file."
                                )
                            },
                            "content": {
                                "type": "string",
                                "description": (
                                    "Complete new contents of "
                                    "the source file."
                                )
                            }
                        },
                        "required": [
                            "path",
                            "content"
                        ]
                    }
                }
            },
            #RUN TEST
            {
                "type": "function",
                "function": {
                    "name": "run_tests",
                    "description": (
                        "Run the repository test suite and "
                        "return the results."
                    ),
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
            result = self.tools.list_files()
        elif name == "read_file":

            path = arguments["path"]

            result = self.tools.read_file(path)

            self.memory.record_file_read(path)
        #SEARCH CODE USING RAG
        elif name == "search_code":

            query = arguments["query"]

            results = self.retriever.search(
                query,
                top_k=5
            )

            if not results:

                result = "No relevant code was found."

            else:

                formatted_results = []

                for item in results:

                    formatted_results.append(
                        f"""
FILE: {item['file']}
LINES: {item['start_line']}-{item['end_line']}

{item['content']}
""".strip()
                    )

                result = "\n\n---\n\n".join(
                    formatted_results
                )
        #EDIT
        elif name == "edit_file":

            path = arguments["path"]
            if (
                path.startswith("tests/")
                or path.startswith("test_")
                or "/tests/" in path
            ):
            #SAFETY 
                result = (
                    "ERROR: Tests cannot be modified by "
                    "the agent. Modify the source code instead."
                )
            else:
                result = self.tools.edit_file(
                    path,
                    arguments["content"]
                )

                self.memory.record_file_modified(path)

        elif name == "run_tests":

            test_result = self.tools.run_tests()

            self.memory.record_test_run(
                test_result
            )

            result = json.dumps(
                test_result,
                indent=2
            )

        else:

            result = f"Unknown tool: {name}"
        #ADD TO MEMORY
        self.memory.record_action(
            name,
            arguments,
            result
        )
        return result


    def run(self, task):
        self.memory.start_task(task)
        repository_context = self.tools.list_files()
        plan = self.planner.create_plan(
            task,
            repository_context
        )
        print("\n" + "=" *50)
        print("IMPLEMENTATION PLAN")
        print("="*50)
        for i,step in enumerate(plan,1):
            print(f"{i}.{step}")
        print("=" * 50 + "\n")
        previous_memory = self.memory.context()
        plan_text = "\n".join(
            f"{i}.{step}"
            for i, step in enumerate(plan, 1)
        )
        messages = [
            {
                "role": "system",
                "content": """
        You are an autonomous AI software engineer.

        You work directly on a software repository.

        Your job is to solve the user's software engineering task.

        ==================================================
        AVAILABLE TOOLS
        ==================================================

        1. list_files

        Discover the repository structure.

        2. search_code

        Semantically search the repository using RAG.

        3. read_file

        Read an existing file.

        4. edit_file

        Modify SOURCE CODE.

        5. run_tests

        Run the test suite.

        ==================================================
        STRICT RULES
        ==================================================

        1. ALWAYS call list_files FIRST.

        2. ALWAYS use the EXACT file paths returned by
        list_files.

        3. NEVER guess file paths.

        4. You may use search_code to locate relevant
        code after discovering the repository.

        5. ALWAYS read a file before editing it.

        6. NEVER modify tests unless the user explicitly
        asks you to modify tests.

        7. When a test fails, identify the SOURCE CODE
        responsible for the failure.

        8. Make the SMALLEST possible source-code change.

        9. Do not add unnecessary classes, functions,
        main methods, unittest code, or features.

        10. After editing source code, ALWAYS run the tests.

        11. If tests fail, inspect the failure and make
            another source-code fix.

        12. STOP once the existing tests pass.

        13. Do not claim that tests pass unless you actually
            ran run_tests and received a successful result.

        ==================================================
        RAG RULES
        ==================================================

        search_code uses a vector database containing
        semantic representations of repository code.

        Use search_code when:

        - The repository is unfamiliar.
        - You need to locate functionality.
        - You need to find a relevant class or function.
        - The repository contains many files.

        After finding a potentially relevant file with
        search_code, use read_file to inspect the actual
        file before making changes.

        Do NOT blindly trust search results.

        ==================================================
        MEMORY RULES
        ==================================================

        You have persistent memory containing information
        about previous actions performed by the agent.

        Use memory to avoid unnecessary repeated work.

        Memory may contain:

        - Files already read
        - Files already modified
        - Previous test results
        - Previous actions
        - Previous failures
        - Previous approaches

        Do not repeat an unsuccessful approach without
        a reason.

        However, ALWAYS verify the current repository
        state using the available tools.

        ==================================================
        EXAMPLE
        ==================================================

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

        ==================================================
        OBJECTIVE
        ==================================================

        Solve the user's task with the smallest safe
        change possible.

        Use the available tools to inspect, understand,
        modify, and validate the repository.

        """.strip()
            },

            {
                "role": "system",
                "content": (
                    "==================================================\n"
                    "IMPLEMENTATION PLAN\n"
                    "==================================================\n\n"
                    "Follow the implementation plan below.\n\n"
                    + plan_text
                    + "\n\n"
                    "Use the plan as guidance, but verify everything "
                    "against the actual repository.\n\n"
                    "Do not blindly follow the plan if repository "
                    "inspection shows that a different approach "
                    "is required."
                )
            },

            {
                "role": "system",
                "content": (
                    "PERSISTENT AGENT MEMORY:\n\n"
                    + previous_memory
                    + """

        Use this memory to avoid repeating unnecessary
        actions.

        Before taking an action, consider:

        - What files have already been inspected?
        - What files have already been modified?
        - What tests have already been run?
        - What failures have already been observed?
        - What approaches have already been attempted?

        Do not blindly trust memory.

        The actual repository is always the source
        of truth.
        """
                )
            },
            {
                "role": "user",
                "content": task
            }
        ]
        tools = self.tool_definitions()

        for iteration in range(10):

            print(
                f"\n[AGENT ITERATION {iteration + 1}]"
            )

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

                self.memory.complete_task()

                return (
                    message.content
                    or "Agent finished."
                )

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
            "Agent stopped after reaching "
            "the maximum number of iterations."
        )