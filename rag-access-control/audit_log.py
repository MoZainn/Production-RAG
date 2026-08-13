"""
Audit Logging
-------------
Every query is logged: who asked, what they asked, and what came
back. This is the third piece of the AAA pattern — Authentication,
Authorization, Auditing — that most enterprise security frameworks
are built around:

  Authentication -> who are you? (auth.py)
  Authorization  -> what are you allowed to see? (rag_engine.py's
                    role-based filtering)
  Auditing       -> what actually happened? (this file)

Authentication and authorization control what CAN happen. Auditing
is the permanent record of what DID happen — needed for compliance,
incident investigation, and simply being able to prove what a system
did, after the fact.

Uses SQLite (Python's built-in sqlite3 — no extra dependency) so the
log persists across app restarts, unlike the Chroma vector store,
which is intentionally rebuilt fresh every time the app starts.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("audit_log.db")


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_email TEXT NOT NULL,
            user_role TEXT NOT NULL,
            query_text TEXT NOT NULL,
            result_count INTEGER NOT NULL,
            result_titles TEXT
        )
        """
    )
    return conn


def log_query(user_email: str, user_role: str, query_text: str, result_titles: list):
    conn = _get_connection()
    conn.execute(
        "INSERT INTO audit_log "
        "(timestamp, user_email, user_role, query_text, result_count, result_titles) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            user_email,
            user_role,
            query_text,
            len(result_titles),
            "; ".join(result_titles) if result_titles else "",
        ),
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 20):
    conn = _get_connection()
    cursor = conn.execute(
        "SELECT timestamp, user_email, user_role, query_text, result_count, result_titles "
        "FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
