import streamlit as st
from auth import verify_login
from rag_engine import SecureRAG

st.set_page_config(
    page_title="Acme Corp | Knowledge Portal",
    page_icon="🔐",
    layout="centered",
)

CUSTOM_CSS = """
<style>
#MainMenu, footer, header {visibility: hidden;}

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 24px;
    background: #0f172a;
    border-radius: 10px;
    margin-bottom: 24px;
}

.top-bar-brand {
    color: white;
    font-weight: 700;
    font-size: 16px;
}

.user-badge {
    color: #cbd5e1;
    font-size: 13px;
}

.role-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    margin-left: 8px;
}

.role-team { background: #dbeafe; color: #1e40af; }
.role-admin { background: #fee2e2; color: #991b1b; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

LOGIN_CSS = """
<style>
div.block-container {
    max-width: 380px;
    margin: 70px auto 0 auto;
    background: #ffffff;
    border-radius: 14px;
    padding: 40px 30px 26px 30px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.35);
}

.login-logo-circle {
    width: 60px;
    height: 60px;
    border-radius: 16px;
    background: linear-gradient(135deg, #2563eb, #1e40af);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    font-weight: 800;
    font-size: 26px;
    margin: -72px auto 14px auto;
    box-shadow: 0 8px 20px rgba(37,99,235,0.45);
}

.login-title {
    font-size: 19px;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
    text-align: center;
}

.login-subtitle {
    color: #475569;
    font-size: 12.5px;
    text-align: center;
    margin-top: 3px;
    margin-bottom: 18px;
}

div.block-container input {
    color: #0f172a !important;
    background-color: #f8fafc !important;
}

div.block-container label p {
    color: #1e293b !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}

.demo-creds {
    margin-top: 14px;
    padding: 10px 12px;
    background: #f1f5f9;
    border-radius: 8px;
    font-size: 11px;
    color: #334155;
    line-height: 1.5;
}
</style>
"""


@st.cache_resource
def load_engine():
    return SecureRAG("docs")


def render_login():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="login-logo-circle">A</div>
        <p class="login-title">Acme Corp</p>
        <p class="login-subtitle">Sign in to the Internal Knowledge Portal</p>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        email = st.text_input("Work email", placeholder="you@acmecorp.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        user = verify_login(email, password)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid email or password.")

    st.markdown(
        """
        <div class="demo-creds">
        <b>Demo accounts</b><br>
        Team member — alice@acmecorp.com / team123<br>
        Admin — bob@acmecorp.com / admin123
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard():
    user = st.session_state.user
    role_class = "role-admin" if user["role"] == "admin" else "role-team"

    top_col1, top_col2 = st.columns([4, 1])
    with top_col1:
        st.markdown(
            f"""
            <div class="top-bar">
                <span class="top-bar-brand">🔐 Acme Corp Knowledge Portal</span>
                <span class="user-badge">
                    {user['name']} · {user['title']}
                    <span class="role-pill {role_class}">{user['role']}</span>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_col2:
        if st.button("Log out", use_container_width=True):
            del st.session_state.user
            st.rerun()

    engine = load_engine()

    query = st.text_input(
        "Ask a question about company policy, benefits, or operations",
        placeholder="e.g. What is the policy on remote work?",
    )

    if query.strip():
        results = engine.query(query, user["role"])

        if not results:
            st.warning(
                "No results. Either nothing matched, or the relevant "
                "documents aren't within your access level."
            )
        else:
            st.caption(f"{len(results)} result(s) — scoped to your access level")
            for score, doc in results:
                with st.expander(f"📄 {doc.title}  ·  relevance {score:.2f}"):
                    st.write(doc.content)
                    st.caption(f"source: {doc.source_file}  ·  access tag: {doc.access_role}")

    st.divider()
    st.caption(
        "Retrieval is filtered by your role BEFORE ranking — documents outside "
        "your access level are never scored or surfaced. Log out and sign in as "
        "the other demo account to see the same question return different results."
    )


if "user" not in st.session_state:
    render_login()
else:
    render_dashboard()