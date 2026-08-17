import json


class Planner:
    def __init__(self, client):
        self.client = client

    def create_plan(self, task: str, repository_context: str = ""):
        prompt = f"""
You are a senior software engineer.

Create a step-by-step implementation plan for this task.

TASK:
{task}

REPOSITORY CONTEXT:
{repository_context}

Rules:
- Return ONLY valid JSON.
- Return an object containing a "steps" array.
- Each step must be a concrete action.
- Only include actions that can be performed using the available agent tools.
- Available tools are:
  - list_files
  - search_code
  - read_file
  - edit_file
  - run_tests
- Do not include Git commits, pushes, deployments, or other actions that require unavailable tools.
- Do not write code.
- Keep the plan between 3 and 8 steps.

Example:
{{
    "steps": [
        "Inspect the relevant files",
        "Identify the root cause",
        "Implement the required change",
        "Run the existing tests",
        "Fix any remaining failures"
    ]
}}
"""

        response = self.client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior autonomous software engineer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        try:
            plan = json.loads(content)
            return plan["steps"]

        except (json.JSONDecodeError, KeyError, TypeError):
            return [
                "Inspect the relevant files",
                "Understand the existing implementation",
                "Implement the required change",
                "Run the existing tests",
                "Fix any remaining failures"
            ]