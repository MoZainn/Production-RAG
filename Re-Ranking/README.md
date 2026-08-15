# RAG Reranking — Two-Stage Retrieval Demo

A working demonstration of why production RAG systems use **two
retrieval stages** instead of one, and what breaks if you skip the
second stage.

## The problem this solves

Most beginner RAG tutorials do single-stage retrieval: embed the
query, embed every document, rank by similarity, return the top
matches. This uses a **bi-encoder** — query and document are each
embedded *separately*, with no interaction between them.

The failure mode: a bi-encoder has to compress everything about a
document into one fixed-size vector before it ever sees your actual
question. Two documents can end up looking similar in vector space
just because they share vocabulary — even when only one of them is
actually relevant.

This repo includes a deliberately tricky document set to make that
failure visible: a genuinely helpful "fix email sync on your phone"
guide, sitting alongside an internal ops log that repeats the words
"email," "sync," and "server" a dozen times in a completely
different context. Pure vector similarity can be fooled into ranking
the irrelevant log highly, just from keyword density.

## The fix: a second stage

- **Stage 1 (`retriever.py`)** — Chroma vector search casts a wide
  net fast: pull the top 6 candidates from the whole knowledge base
  by cosine similarity. Optimized for recall (don't miss the right
  doc), not precision.
- **Stage 2 (`reranker.py`)** — A **cross-encoder** re-scores just
  those 6 candidates. Unlike a bi-encoder, a cross-encoder takes the
  query and a candidate document *together*, as one combined input,
  and directly scores how relevant they are to each other. It can
  actually reason about the relationship between the two, not just
  compare two vectors that were each computed in isolation.

The tradeoff: cross-encoders are far more accurate but much slower,
and can't be precomputed ahead of time the way document embeddings
can. That's exactly why this only runs on Stage 1's short list of 6,
not the entire knowledge base — running a cross-encoder on thousands
of documents from scratch would be too slow for real-time use.

## Structure

```
rag-reranking/
├── app.py            # Streamlit UI — before/after comparison
├── retriever.py        # Stage 1: Chroma vector search (bi-encoder)
├── reranker.py          # Stage 2: cross-encoder reranking
├── requirements.txt
└── docs/                 # IT support knowledge base, including one
                            # deliberately keyword-stuffed trap doc
```

## Run it

```bash
uv run streamlit run app.py
```

First run downloads two small models (Chroma's embedding model, and
the reranking cross-encoder `cross-encoder/ms-marco-MiniLM-L-6-v2`)
— a few hundred MB combined, cached locally after that. No API keys
needed, everything runs on your machine.

## What to look for

Try the default query: *"My email isn't syncing on my phone, what
should I do?"*

- **Left column (vector search only)** — watch where "Email Server
  Sync Job — Weekly Operations Report" lands. It's not actually
  helpful for this question, but its heavy repetition of "email" and
  "sync" can pull it toward the top of pure vector similarity.
- **Right column (after reranking)** — "How to Fix Email Sync Issues
  on Your Phone" should move up to the top, and the ops log should
  drop, because the cross-encoder can tell the difference between a
  document that *mentions* sync and one that actually *answers* a
  sync question.

If the effect isn't dramatic on the first try, experiment with the
query wording — reranking's impact is strongest exactly in these
keyword-overlap-but-wrong-context situations, so try phrasing that
leans into the ambiguity between the trap doc and the real answer.

## Extending this

- Swap in a larger cross-encoder (e.g.
  `cross-encoder/ms-marco-MiniLM-L-12-v2`) for higher accuracy at
  the cost of latency.
- Increase `n_candidates` in `retriever.py` to widen Stage 1's net
  before reranking narrows it back down.
- Combine with the access-control pattern from the
  `rag-access-control` project — role-based filtering in Stage 1,
  reranking in Stage 2, same pipeline.
