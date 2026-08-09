"""
Authentication layer for the Secure RAG demo.

This is deliberately minimal — a hardcoded user store with hashed
passwords — so the ACCESS CONTROL logic stays the focus of the demo.

IMPORTANT (read this before showing this to anyone technical):
This is illustrative, not production-grade auth. A real system would:
  - Never store its own password table like this — use an identity
    provider (Okta, Auth0, Azure AD, Cognito) or at minimum a proper
    auth library (e.g. Django's auth, or OAuth2/OIDC).
  - Use bcrypt/argon2 (with per-user salt) instead of plain sha256.
  - Issue short-lived session tokens (JWT or server-side sessions),
    not just an in-memory Streamlit session state flag.
  - Rate-limit login attempts and log auth events for audit.

For a demo whose whole point is "authorization scopes retrieval,"
this layer is enough to be real (it genuinely checks credentials and
sets a role), without turning the project into an auth library build.
"""

import hashlib

# email -> {password_hash, name, role}
# Demo credentials (shown here + in README so anyone testing this can log in):
#   salma@acmecorp.com / team      -> role: team
#   raza@acmecorp.com   / admin    -> role: admin
_USERS = {
    "salma@acmecorp.com": {
        "password_hash": hashlib.sha256("team".encode()).hexdigest(),
        "name": "Salma Hayaat",
        "role": "team",
        "title": "Software Engineer",
    },
    "raza@acmecorp.com": {
        "password_hash": hashlib.sha256("admin".encode()).hexdigest(),
        "name": "Raza Khan",
        "role": "admin",
        "title": "Platform Administrator",
    },
}


def verify_login(email: str, password: str):
    """
    Returns the user record dict on success, or None on failure.
    """
    email = email.strip().lower()
    user = _USERS.get(email)
    if not user:
        return None

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user["password_hash"]:
        return None

    return {"email": email, **user}
