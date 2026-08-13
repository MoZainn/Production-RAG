import streamlit as st
from auth import verify_login
from rag_engine import SecureRAG
from audit_log import log_query, get_recent_logs

st.set_page_config(
    page_title="Acme Corp | Knowledge Portal",
    page_icon="🔐",
    layout="centered",
)

BASE_CSS = """
<style>
#MainMenu, footer, header {visibility: hidden;}

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
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

st.markdown(BASE_CSS, unsafe_allow_html=True)

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

DASHBOARD_CSS = """
<style>
div.block-container {
    max-width: 760px;
    margin: 50px auto 0 auto;
    background: #ffffff;
    border-radius: 14px;
    padding: 32px 34px 30px 34px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.35);
}

.dash-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 18px;
    margin-bottom: 22px;
    border-bottom: 1px solid #e2e8f0;
}

.dash-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}

.dash-logo-mark {
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: linear-gradient(135deg, #2563eb, #1e40af);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    font-weight: 800;
    font-size: 15px;
}

.dash-brand-text {
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
}

.dash-user {
    text-align: right;
    font-size: 12.5px;
    color: #475569;
}

.dash-user b {
    color: #0f172a;
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

div.block-container [data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
}

div.block-container [data-testid="stMarkdownContainer"] p {
    color: #1e293b !important;
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
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

    user = st.session_state.user
    role_class = "role-admin" if user["role"] == "admin" else "role-team"

    header_col, logout_col = st.columns([5, 1])
    with header_col:
        st.markdown(
            f"""
            <div class="dash-header">
                <div class="dash-brand">
                    <div class="dash-logo-mark">A</div>
                    <span class="dash-brand-text">Acme Corp Knowledge Portal</span>
                </div>
                <div class="dash-user">
                    <b>{user['name']}</b><br>
                    {user['title']}
                    <span class="role-pill {role_class}">{user['role']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with logout_col:
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
        result_titles = [doc.title for _, doc in results]
        log_query(user["email"], user["role"], query, result_titles)

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

    if user["role"] == "admin":
        st.divider()
        with st.expander("🔍 Audit Log (admin only)"):
            logs = get_recent_logs(20)
            if not logs:
                st.caption("No queries logged yet.")
            else:
                for ts, email, role, q, count, titles in logs:
                    st.markdown(f"**{ts}** — `{email}` ({role}) asked: \"{q}\" → {count} result(s)")
                    if titles:
                        st.caption(f"Returned: {titles}")


if "user" not in st.session_state:
    render_login()
else:
    render_dashboard()