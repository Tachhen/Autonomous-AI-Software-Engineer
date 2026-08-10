import os
import subprocess


class RepositoryTools:

    def __init__(self, workspace):
        self.workspace = os.path.abspath(workspace)

    def list_files(self):
        files = []

        for root, dirs, filenames in os.walk(self.workspace):

            dirs[:] = [
                d for d in dirs
                if d not in {
                    ".git",
                    "__pycache__",
                    ".pytest_cache",
                    ".venv",
                    "venv"
                }
            ]

            for filename in filenames:
                path = os.path.relpath(
                    os.path.join(root, filename),
                    self.workspace
                )

                files.append(path)

        return "\n".join(files)

    def read_file(self, path):
        full_path = os.path.abspath(
            os.path.join(self.workspace, path)
        )

        if not full_path.startswith(self.workspace):
            return "Error: access outside workspace is not allowed."

        if not os.path.exists(full_path):
            return f"Error: file does not exist: {path}"

        if not os.path.isfile(full_path):
            return f"Error: not a file: {path}"

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()

        except UnicodeDecodeError:
            return f"Error: {path} is not a text file."

    def edit_file(self, path, content):
        full_path = os.path.abspath(
            os.path.join(self.workspace, path)
        )

        if not full_path.startswith(self.workspace):
            return "Error: access outside workspace is not allowed."

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"Successfully updated {path}"

        except Exception as e:
            return f"Error writing file: {e}"

    def run_tests(self):
        env = os.environ.copy()

        env["PYTHONPATH"] = self.workspace

        try:
            result = subprocess.run(
                ["pytest", "-q"],
                cwd=self.workspace,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Tests timed out after 60 seconds."
            }

        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Error running tests: {e}"
            }