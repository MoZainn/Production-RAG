# Production RAG

A multi-agent Retrieval-Augmented Generation system, built from scratch to explore what "production-ready" actually requires beyond chunking, embeddings, and a vector store.

Most RAG tutorials stop at retrieve → stuff context → generate. This repo starts where that stops: routing, memory, access control, reranking, and evaluation — the layer that decides whether a RAG system is a demo or something a real team could depend on.

---

## Why this exists

RAG isn't chunking. RAG isn't embeddings. RAG isn't a vector database. It's the discipline of stitching all of these into a system that gives accurate, stable, explainable answers — under real constraints, with real failure modes.

This repo is being built and documented in public, one layer at a time.

---

## What's built so far

### 1. Multi-agent retrieval core
- Two-stage router (keyword + LLM) directing queries to specialized agents instead of one generic retriever handling everything
- Multiple domain agents (specs, use-case, hardware, workflow)
- Layered memory — session and persistent — so context holds across a conversation
- Local embeddings + FAISS vector store
- A "final answer" marker heuristic to fix silent response truncation

### 2. Access control at the retrieval layer
- Authentication (who you are) and authorization (what you're allowed to see), enforced before retrieval — not filtered after
- Role-based document tagging (Team Member / Admin)
- Retriever only searches documents inside the caller's allowed set; everything outside it is invisible to ranking, not just to the user
- Mirrors metadata-filtered search patterns used in Pinecone / Qdrant / Weaviate / Chroma

### 3. Reranking and evaluation
- Cross-encoder reranker (BGE/MiniLM-style) inserted between retrieval and generation
- Retriever widened to pull more candidates at lower precision; reranker scores query–document pairs jointly and reorders before generation
- Retrieval quality measured with Precision@k and Recall@k, not eyeballed
- Finding: the reranker didn't strictly outperform the base retriever's ranking — reordering isn't a free upgrade, it needs the same evaluation discipline as everything else in the pipeline

---

## What's coming next

- **Evaluation framework for the full pipeline** — not just retrieval in isolation, but end-to-end answer quality
- **Pre-processing** — smarter chunking and document preparation strategies
- **Hybrid retrieval** — combining lexical (BM25) and dense retrieval
- Continued hardening of the "deep layer": failure modes, latency/accuracy tradeoffs, and packaging this into something open-source and usable outside one machine

---

## Design principles this repo follows

- Retrieval fails silently before it fails loudly — design for that
- Routing and agent design are first-class problems, not an afterthought
- Memory and state matter as much as retrieval quality
- Debugging generation usually means debugging retrieval first
- Nothing ships on "it feels better" — every change is checked against a metric

---

## Status

Actively under construction and documented as it's built. Expect breaking changes as pieces get rebuilt in the open.

---

## License

Personal Portfolio Work - MIT LISENCED
