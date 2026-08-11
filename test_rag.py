from rag.indexer import CodeIndexer
from rag.retriever import CodeRetriever


workspace = "./workspace/demo-project"

indexer = CodeIndexer(workspace)

indexer.index()

retriever = CodeRetriever()

results = retriever.search(
    "How does the calculator add numbers?"
)

for result in results:

    print("\nFILE:", result["file"])
    print(
        "LINES:",
        result["start_line"],
        "-",
        result["end_line"]
    )

    print(result["content"])