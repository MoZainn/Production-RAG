# Audit Logging — Drop-in Module

This is the third piece of the AAA security pattern (Authentication,
Authorization, Auditing) for the rag-access-control project.

- **Authentication** — who are you? (already in `auth.py`)
- **Authorization** — what are you allowed to see? (already in `rag_engine.py`)
- **Auditing** — what actually happened? (this module)

`audit_log.py` records every query — who asked, what they asked, and
what came back — to a local SQLite database (`audit_log.db`). SQLite
is built into Python, so there's no new dependency to install.

## How to wire it in

1. Drop `audit_log.py` into your `rag-access-control` project folder,
   alongside `app.py`, `auth.py`, and `rag_engine.py`.

2. In `app.py`, add this import near the top:

   ```python
   from audit_log import log_query, get_recent_logs
   ```

3. Inside `render_dashboard()`, find the block that runs the query
   and displays results. Right after `results = engine.query(...)`,
   add:

   ```python
   result_titles = [doc.title for _, doc in results]
   log_query(user["email"], user["role"], query, result_titles)
   ```

   This logs every query — including ones with zero results, since a
   pattern of zero-result queries for restricted content is itself
   useful audit signal.

4. Still inside `render_dashboard()`, add an admin-only viewer near
   the bottom (before or after the closing caption):

   ```python
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
   ```

   Only admins can see the log itself — same role-check pattern as
   the rest of the app, and realistic: normal employees don't get to
   see everyone's query history in a real company either.

5. Add one line to `.gitignore`:

   ```
   audit_log.db
   ```

   Same reasoning as `chroma_db/` — it's local runtime data generated
   by using the app, not something that belongs in source control.

## Verifying it works

Log in as a team member, ask a couple of questions (including one
that should return zero results, like "what are the salary bands?").
Log out, log in as admin — the "Audit Log" expander at the bottom of
the dashboard should show both users' query history, including the
zero-result one.

## What's inside audit_log.py

- `log_query(user_email, user_role, query_text, result_titles)` —
  writes one row per query to `audit_log.db`.
- `get_recent_logs(limit=20)` — returns the most recent entries,
  newest first, as tuples of
  `(timestamp, user_email, user_role, query_text, result_count, result_titles)`.

The table is created automatically on first use — no separate setup
step needed.
