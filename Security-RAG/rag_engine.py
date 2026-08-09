"""
Secure RAG Engine
------------------
A minimal retrieval engine that demonstrates access-controlled RAG:
the SAME query, issued by users with different roles, returns
DIFFERENT retrieved documents based on what each role is authorized
to see. Filtering happens at the retrieval layer, not after the fact.

Docs under docs/team/  -> accessible to all roles
Docs under docs/admin/ -> accessible to "admin" role only
"""

from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Document:
    def __init__(self, doc_id, title, content, access_role, source_file):
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.access_role = access_role  # "team" or "admin"
        self.source_file = source_file


class SecureRAG:
    """
    Role-aware retrieval engine.

    Access model:
      - "team"  role can only retrieve documents tagged access_role="team"
      - "admin" role can retrieve documents tagged "team" AND "admin"

    This mirrors how a real production system would attach a metadata
    filter (e.g. {"access_role": {"$in": allowed_roles}}) to a vector DB
    query (Pinecone, Qdrant, Chroma, Weaviate, etc.) before ranking —
    unauthorized chunks are never scored or returned, not just hidden
    in the UI after the fact.
    """

    ROLE_HIERARCHY = {
        "team": {"team"},
        "admin": {"team", "admin"},
    }

    def __init__(self, docs_dir="docs"):
        self.docs_dir = Path(docs_dir)
        self.documents = []
        self._load_documents()

        if not self.documents:
            raise RuntimeError(f"No documents found under {self.docs_dir}")

        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.doc_vectors = self.vectorizer.fit_transform(
            [d.content for d in self.documents]
        )

    def _load_documents(self):
        doc_id = 0
        for role_folder in ("team", "admin"):
            folder = self.docs_dir / role_folder
            if not folder.exists():
                continue
            for file in sorted(folder.glob("*.txt")):
                content = file.read_text(encoding="utf-8").strip()
                first_line = content.splitlines()[0] if content else file.stem
                title = first_line.lstrip("#").strip()
                self.documents.append(
                    Document(doc_id, title, content, role_folder, file.name)
                )
                doc_id += 1

    def query(self, question: str, user_role: str, top_k: int = 3):
        """
        Returns up to top_k (score, Document) tuples, restricted to
        documents the given role is authorized to access.
        """
        allowed_roles = self.ROLE_HIERARCHY.get(user_role, {"team"})

        query_vec = self.vectorizer.transform([question])
        sims = cosine_similarity(query_vec, self.doc_vectors)[0]

        results = [
            (score, doc)
            for idx, (score, doc) in enumerate(zip(sims, self.documents))
            if doc.access_role in allowed_roles and score > 0
        ]
        results.sort(key=lambda pair: pair[0], reverse=True)
        return results[:top_k]
