import streamlit as st
from retriever import Retriever
from reranker import rerank

st.set_page_config(page_title="RAG Reranking Demo", page_icon="🔀", layout="wide")

CUSTOM_CSS = """
<style>
#MainMenu, footer, header {visibility: hidden;}

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

div.block-container {
    max-width: 1000px;
    margin: 40px auto 0 auto;
    background: #ffffff;
    border-radius: 14px;
    padding: 32px 36px 30px 36px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.35);
}

div.block-container input {
    color: #0f172a !important;
    background-color: #f8fafc !important;
}

div.block-container label p {
    color: #1e293b !important;
    font-weight: 600 !important;
}

.stage-title {
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 2px;
}

.stage-subtitle {
    font-size: 12px;
    color: #64748b;
    margin-bottom: 14px;
}

.result-card {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
}

.result-rank {
    display: inline-block;
    width: 22px;
    height: 22px;
    border-radius: 6px;
    background: #1e293b;
    color: white;
    font-size: 12px;
    font-weight: 700;
    text-align: center;
    line-height: 22px;
    margin-right: 8px;
}

.result-title {
    font-size: 13.5px;
    font-weight: 600;
    color: #0f172a;
}

.result-score {
    font-size: 11px;
    color: #64748b;
    margin-top: 3px;
}

.moved-up {
    color: #16a34a;
    font-weight: 700;
}

.moved-down {
    color: #dc2626;
    font-weight: 700;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <p style="font-size:20px; font-weight:700; color:#0f172a; margin-bottom:0;">
    🔀 Reranking Demo — Vector Search vs. Cross-Encoder Reranking
    </p>
    <p style="font-size:13px; color:#475569; margin-top:4px;">
    Same query, same candidate set. Left: raw vector similarity order.
    Right: reordered by a cross-encoder that reads the query and each
    document together instead of comparing precomputed vectors.
    </p>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_retriever():
    return Retriever("docs")


retriever = load_retriever()

query = st.text_input(
    "Ask a question",
    value="My email isn't syncing on my phone, what should I do?",
)

if query.strip():
    with st.spinner("Retrieving candidates, then reranking..."):
        candidates = retriever.retrieve(query, n_candidates=6)
        # Keep a copy of the original vector-search order before reranking
        # mutates/reorders the list, so the "before" column stays accurate.
        original_order = list(candidates)
        reranked = rerank(query, candidates)

    original_titles = [doc.title for doc in original_order]
    reranked_titles = [doc.title for doc in reranked]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            '<p class="stage-title">Stage 1 — Vector Search Only</p>'
            '<p class="stage-subtitle">Bi-encoder similarity, unmodified order</p>',
            unsafe_allow_html=True,
        )
        for i, doc in enumerate(original_order):
            new_pos = reranked_titles.index(doc.title)
            movement = ""
            if new_pos < i:
                movement = f'<span class="moved-up">↑ moved up {i - new_pos}</span>'
            elif new_pos > i:
                movement = f'<span class="moved-down">↓ moved down {new_pos - i}</span>'
            st.markdown(
                f"""
                <div class="result-card">
                    <span class="result-rank">{i + 1}</span>
                    <span class="result-title">{doc.title}</span>
                    <div class="result-score">vector score: {doc.vector_score:.3f} {movement}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown(
            '<p class="stage-title">Stage 2 — After Cross-Encoder Reranking</p>'
            '<p class="stage-subtitle">Query + document scored together</p>',
            unsafe_allow_html=True,
        )
        for i, doc in enumerate(reranked):
            old_pos = original_titles.index(doc.title)
            movement = ""
            if i < old_pos:
                movement = f'<span class="moved-up">↑ up from #{old_pos + 1}</span>'
            elif i > old_pos:
                movement = f'<span class="moved-down">↓ down from #{old_pos + 1}</span>'
            st.markdown(
                f"""
                <div class="result-card">
                    <span class="result-rank">{i + 1}</span>
                    <span class="result-title">{doc.title}</span>
                    <div class="result-score">rerank score: {doc.rerank_score:.3f} {movement}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    st.caption(
        "Stage 1 casts a wide net fast — 6 candidates pulled from the whole "
        "knowledge base by vector similarity. Stage 2 only re-scores those "
        "6, accurately, by reading the query and each document together. "
        "That combination is what production RAG systems use to get both "
        "speed and precision."
    )
