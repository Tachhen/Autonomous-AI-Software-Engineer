import chromadb


class CodeRetriever:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path="./.chroma"
        )

        self.collection = self.client.get_or_create_collection(
            name="codebase"
        )

    def search(self, query, top_k=5):

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        output = []

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        for document, metadata in zip(
            documents,
            metadatas
        ):

            output.append({
                "file": metadata["file"],
                "start_line": metadata["start_line"],
                "end_line": metadata["end_line"],
                "content": document
            })

        return output