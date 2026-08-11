import os
import chromadb


class CodeIndexer:

    def __init__(self, workspace):

        self.workspace = os.path.abspath(workspace)

        self.client = chromadb.PersistentClient(
            path="./.chroma"
        )

        self.collection = self.client.get_or_create_collection(
            name="codebase"
        )

    def get_files(self):

        files = []

        ignored_dirs = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".chroma"
        }

        for root, dirs, filenames in os.walk(self.workspace):

            dirs[:] = [
                d for d in dirs
                if d not in ignored_dirs
            ]

            for filename in filenames:

                if filename.endswith((
                    ".py", ".java", ".js", ".jsx",
                    ".ts", ".tsx", ".cpp", ".c",
                    ".h", ".go", ".rs", ".md",
                    ".json", ".yaml", ".yml"
                )):

                    files.append(
                        os.path.join(root, filename)
                    )

        return files

    def chunk_file(self, path, chunk_size=100):

        with open(
            path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            lines = f.readlines()

        chunks = []

        for i in range(0, len(lines), chunk_size):

            chunks.append(
                {
                    "content": "".join(
                        lines[i:i + chunk_size]
                    ),
                    "start_line": i + 1,
                    "end_line": min(
                        i + chunk_size,
                        len(lines)
                    )
                }
            )

        return chunks

    def index(self):

        files = self.get_files()

        documents = []
        ids = []
        metadatas = []

        counter = 0

        for path in files:

            relative_path = os.path.relpath(
                path,
                self.workspace
            )

            for chunk in self.chunk_file(path):

                documents.append(
                    chunk["content"]
                )

                ids.append(
                    f"chunk-{counter}"
                )

                metadatas.append(
                    {
                        "file": relative_path,
                        "start_line": chunk["start_line"],
                        "end_line": chunk["end_line"]
                    }
                )

                counter += 1

        if not documents:
            print("No source files found.")
            return

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(
            f"Indexed {len(documents)} chunks "
            f"from {len(files)} files."
        )