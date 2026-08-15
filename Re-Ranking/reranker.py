"""
Stage 2: Reranker
-------------------
Precise, expensive re-scoring of the small shortlist Stage 1 already
found. Uses a CROSS-encoder, not a bi-encoder — the key architectural
difference from retriever.py.

Bi-encoder (Stage 1 / Chroma):
    embed(query)  -> vector A     (computed once, independently)
    embed(doc)    -> vector B     (precomputed for every doc, ahead of time)
    score = similarity(A, B)      (cheap — just a dot product)

Cross-encoder (Stage 2 / this file):
    score = model(query, doc)     (query and doc go IN TOGETHER)

Because the cross-encoder sees the query and the document at the same
time, it can reason about how they relate to each other directly —
it's not limited to comparing two vectors that were each computed in
isolation. This makes it significantly more accurate, but also much
slower: it can't be precomputed, because the score depends on the
specific (query, doc) pair. That's exactly why it only runs on
Stage 1's small shortlist (6 docs) instead of the whole knowledge
base — running it on everything would be too slow.

Model used: cross-encoder/ms-marco-MiniLM-L-6-v2, a small, widely
used reranking model trained specifically for this task. Downloaded
once on first run via sentence-transformers, then cached locally.
"""

from sentence_transformers import CrossEncoder

_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_model = None


def _get_model():
    global _model
    if _model is None:
        _model = CrossEncoder(_MODEL_NAME)
    return _model


def rerank(query: str, candidates: list):
    """
    Takes the candidate list from Stage 1 (retriever.retrieve) and
    returns it re-sorted by cross-encoder relevance score. Mutates
    each candidate's .rerank_score in place and returns a NEW list
    sorted by that score, descending.
    """
    if not candidates:
        return candidates

    model = _get_model()

    pairs = [(query, doc.content) for doc in candidates]
    scores = model.predict(pairs)

    for doc, score in zip(candidates, scores):
        doc.rerank_score = float(score)

    return sorted(candidates, key=lambda d: d.rerank_score, reverse=True)
