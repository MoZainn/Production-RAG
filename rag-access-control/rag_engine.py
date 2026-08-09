"""
Secure RAG Engine — Chroma-backed version
-------------------------------------------
Real embeddings + a real local vector database (Chroma), with
role-based access control enforced as a metadata filter that runs
BEFORE similarity search — not as a post-filter on the results.

Docs under docs/team/  -> access_role="team"  (visible to everyone)
Docs under docs/admin/ -> access_role="admin" (visible to admins only)

Chroma runs fully local and persists to ./chroma_db — no API keys,
no external service. It uses its bundled default embedding model
(all-MiniLM-L6-v2, downloaded once on first run, then cached locally)
to turn text into real semantic embeddings, instead of the earlier
keyword-based TF-IDF version (kept in rag_engine_tfidf_backup.py for
reference).
"""

from pathlib import Path
import chromadb

COLLECTION_NAME = "company_docs"


class DocumentResult:
    """Lightweight wrapper so app.py's doc.title / doc.content / etc.
    keep working unchanged regardless of which retriever is behind it."""

    def __init__(self, content: str, metadata: dict):
        self.content = content
        self.title = metadata.get("title", "Untitled")
        self.access_role = metadata.get("access_role", "team")
        self.source_file = metadata.get("source_file", "")


class SecureRAG:
    """
    Role-aware retrieval engine backed by a real vector database.

    Access model:
      - "team"  role can only retrieve documents tagged access_role="team"
      - "admin" role can retrieve documents tagged "team" AND "admin"

    The role -> allowed-tags mapping is passed to Chroma as a `where`
    filter on every query, e.g.:

        collection.query(
            query_texts=[question],
            where={"access_role": {"$in": allowed_roles}},
        )

    Chroma applies that filter as part of the search itself — documents
    outside the allowed set are never compared against the query vector,
    let alone returned. This is the same pattern used by Pinecone,
    Qdrant, and Weaviate in real production deployments.
    """

    ROLE_HIERARCHY = {
        "team": {"team"},
        "admin": {"team", "admin"},
    }

    def __init__(self, docs_dir="docs", persist_dir="chroma_db"):
        self.docs_dir = Path(docs_dir)
        self.client = chromadb.PersistentClient(path=persist_dir)

        # Reset on every startup so edits to docs/ are always reflected —
        # fine for a demo-sized document set; a real system would ingest
        # incrementally instead of rebuilding the whole collection.
        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        self.collection = self.client.create_collection(name=COLLECTION_NAME)
        self._ingest()

    def _ingest(self):
        ids, documents, metadatas = [], [], []
        doc_id = 0

        for role_folder in ("team", "admin"):
            folder = self.docs_dir / role_folder
            if not folder.exists():
                continue
            for file in sorted(folder.glob("*.txt")):
                content = file.read_text(encoding="utf-8").strip()
                if not content:
                    continue
                first_line = content.splitlines()[0]
                title = first_line.lstrip("#").strip()

                ids.append(f"doc_{doc_id}")
                documents.append(content)
                metadatas.append(
                    {
                        "title": title,
                        "access_role": role_folder,
                        "source_file": file.name,
                    }
                )
                doc_id += 1

        if documents:
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, question: str, user_role: str, top_k: int = 3):
        """
        Returns up to top_k (score, DocumentResult) tuples, restricted
        to documents the given role is authorized to access. The
        `where` filter below is what enforces that restriction — it's
        applied by Chroma during the vector search itself.
        """
        allowed_roles = list(self.ROLE_HIERARCHY.get(user_role, {"team"}))

        results = self.collection.query(
            query_texts=[question],
            n_results=top_k,
            where={"access_role": {"$in": allowed_roles}},
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        output = []
        for content, meta, distance in zip(documents, metadatas, distances):
            # Chroma returns a distance (lower = more similar); convert
            # to a similarity-style score so app.py's display stays the
            # same as it was with the TF-IDF version.
            score = max(0.0, 1 - distance)
            output.append((score, DocumentResult(content, meta)))

        return output
