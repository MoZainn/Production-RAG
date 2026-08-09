# Secure RAG Demo — Login-Gated, Access-Controlled Retrieval

A working example of authentication + role-based access control (RBAC)
applied at the **retrieval layer** of a RAG system.

You log in as a specific employee. What you can retrieve — not just what
you're shown, but what's ever scored or considered — is scoped to your
role from that point forward. Log out, log back in as someone else, ask
the exact same question, get a different (or empty) answer.

This is meant to demonstrate a specific point: a raw LLM chat interface
has no concept of "who's asking." A production RAG system does — and
that's one of the engineering problems that separates a tutorial RAG
pipeline from a production one.

## Structure

```
secure-rag-demo/
├── app.py              # Streamlit UI — login portal + scoped dashboard
├── auth.py              # Mock authentication (hashed passwords, user->role)
├── rag_engine.py         # Retrieval engine with role-based filtering
├── requirements.txt
├── docs/
│   ├── team/               # Accessible to ALL authenticated users
│   │   ├── onboarding_guide.txt
│   │   ├── remote_work_policy.txt
│   │   └── it_support_faq.txt
│   └── admin/               # Accessible to ADMIN role only
│       ├── salary_bands.txt
│       ├── board_meeting_minutes.txt
│       └── infra_access_policy.txt
```

## How the authentication works (auth.py)

- A small in-memory user table maps email -> {password_hash, role, name}.
- Passwords are hashed with sha256 before comparison — the app never
  compares or stores plaintext passwords, even in this demo.
- `verify_login(email, password)` hashes the submitted password and
  checks it against the stored hash. Returns the user record on match,
  `None` otherwise.
- On success, `app.py` stores the user record in `st.session_state`,
  which is Streamlit's per-browser-session memory — this is what keeps
  you "logged in" as you interact with the app, and is cleared entirely
  when you click Log out.

**This is illustrative, not production-grade auth.** A real system would:
- Use an identity provider (Okta, Auth0, Azure AD, AWS Cognito) or a
  proper auth framework — never hand-roll a password table like this.
- Use bcrypt/argon2 with per-user salts, not a single sha256 pass.
- Issue short-lived session tokens (JWT / server-side sessions) instead
  of relying on in-memory app state.
- Rate-limit login attempts and log authentication events for audit.

The point of building it this way for the demo: authentication is real
enough that it's actually checking credentials and setting a role — not
a fake screen that leads to the same view regardless of who "logs in."

## How the access control works (rag_engine.py)

- Documents are tagged by folder (`team` / `admin`) when loaded, and
  stored as Chroma metadata alongside a real embedding of each
  document (Chroma's bundled `all-MiniLM-L6-v2` model — downloaded
  once on first run, then cached locally; no API key needed).
- `SecureRAG.query(question, user_role)` maps the logged-in user's
  role to the set of tags they're allowed to see, and passes that as
  a `where` filter directly to Chroma's `collection.query(...)` call:

  ```python
  collection.query(
      query_texts=[question],
      where={"access_role": {"$in": allowed_roles}},
  )
  ```

  Chroma applies that filter as part of the vector search itself —
  documents outside the allowed set are never compared against the
  query embedding, let alone returned. This is the exact same pattern
  used by Pinecone, Qdrant, and Weaviate in real production systems —
  this project now runs on that pattern for real, not just in theory.

## Run it (using uv)

```bash
cd secure-rag-demo
uv venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
uv pip install -r requirements.txt
uv run streamlit run app.py
```

Or skip manual activation entirely:

```bash
cd secure-rag-demo
uv run streamlit run app.py
```

It opens at `http://localhost:8501` with a login screen.

## Demo accounts

| Email                  | Password   | Role  |
|-------------------------|------------|-------|
| alice@acmecorp.com      | team123    | team  |
| bob@acmecorp.com        | admin123   | admin |

## Try this for the video

1. Log in as **alice@acmecorp.com** → ask "What are the salary bands?"
   → **zero results.**
2. Log out, log in as **bob@acmecorp.com** → ask the exact same question
   → full salary breakdown returned.
3. Also try "What is the policy on remote work?" — Alice gets one
   general policy doc; Bob additionally gets the confidential board
   minutes discussing extended remote access for leadership.

Since this is now login-gated, you'll record two separate short clips
(logged in as each user) and cut them together side by side in editing —
which actually reads as more realistic than a split-screen live demo
would, since real users don't see each other's sessions simultaneously.

## Extending this

- Swap Chroma for a hosted vector DB (Pinecone, Qdrant Cloud, Weaviate)
  if you need multi-machine or multi-user concurrent access — Chroma
  here runs fully local, which is perfect for a demo but not a shared
  deployment.
- Replace `auth.py` with real OAuth2/OIDC via an identity provider.
- Add row-level or document-level ACLs instead of folder-level tags for
  finer-grained control.
- Add audit logging — who queried what, and what was returned — for
  compliance and traceability on top of the access control that's
  already enforced.
