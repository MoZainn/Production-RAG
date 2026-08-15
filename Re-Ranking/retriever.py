"""
Stage 1: Retriever
-------------------
Fast, approximate candidate selection using vector similarity search
(Chroma + its bundled embedding model). This casts a wide net —
pulling back more candidates than we'll actually show the user —
because this stage's job is recall (don't miss the right answer),
not precision (don't worry about getting the order exactly right).

Precision is Stage 2's job (reranker.py).
"""

from pathlib import Path
import chromadb

COLLECTION_NAME = "it_support_docs"


class RetrievedDoc:
    def __init__(self, content: str, metadata: dict, vector_score: float):
        self.content = content
        self.title = metadata.get("title", "Untitled")
        self.source_file = metadata.get("source_file", "")
        self.vector_score = vector_score  # similarity score from Stage 1
        self.rerank_score = None          # filled in by Stage 2, if run


class Retriever:
    def __init__(self, docs_dir="docs", persist_dir="chroma_db"):
        self.docs_dir = Path(docs_dir)
        self.client = chromadb.PersistentClient(path=persist_dir)

        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        self.collection = self.client.create_collection(name=COLLECTION_NAME)
        self._ingest()

    def _ingest(self):
        ids, documents, metadatas = [], [], []
        doc_id = 0

        for file in sorted(self.docs_dir.glob("*.txt")):
            content = file.read_text(encoding="utf-8").strip()
            if not content:
                continue
            first_line = content.splitlines()[0]
            title = first_line.lstrip("#").strip()

            ids.append(f"doc_{doc_id}")
            documents.append(content)
            metadatas.append({"title": title, "source_file": file.name})
            doc_id += 1

        if documents:
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def retrieve(self, query: str, n_candidates: int = 6):
        """
        Returns the top n_candidates by raw vector similarity — this
        is the UNRERANKED result set, exactly what a single-stage RAG
        pipeline would show the user.
        """
        results = self.collection.query(query_texts=[query], n_results=n_candidates)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        candidates = []
        for content, meta, distance in zip(documents, metadatas, distances):
            score = max(0.0, 1 - distance)
            candidates.append(RetrievedDoc(content, meta, score))

        return candidates
