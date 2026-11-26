"""Sanitized public build journal.

Only explicitly approved, non-sensitive engineering events can be published.
Never store prompts, secrets, customer data, personal identity, internal URLs,
stack traces, or raw model conversations here.
"""
import json
import re
import sqlite3
import time
from pathlib import Path

ALLOWED_CATEGORIES = {"milestone", "release", "test", "incident_resolved", "research"}
ALLOWED_STATES = {"implemented", "tested", "deployed", "live_verified", "blocked"}


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class BuildJournal:
    def __init__(self, db_path):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
          CREATE TABLE IF NOT EXISTS public_build_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_key TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            state TEXT NOT NULL,
            commit_ref TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
          )
        """)
        self.conn.commit()

    @staticmethod
    def validate(event):
        if event["category"] not in ALLOWED_CATEGORIES:
            raise ValueError("unsupported journal category")
        if event["state"] not in ALLOWED_STATES:
            raise ValueError("unsupported journal state")
        if not re.fullmatch(r"[A-Za-z0-9._:-]{3,120}", event["event_key"]):
            raise ValueError("invalid event key")
        for key, limit in (("title", 120), ("summary", 600), ("commit_ref", 40)):
            value = event.get(key, "")
            if not isinstance(value, str) or len(value) > limit:
                raise ValueError(f"invalid {key}")
        if not event["title"].strip() or not event["summary"].strip():
            raise ValueError("title and summary are required")

    def publish(self, event):
        self.validate(event)
        try:
            self.conn.execute(
              """INSERT INTO public_build_journal(event_key,category,title,summary,
                 state,commit_ref,created_at) VALUES(?,?,?,?,?,?,?)""",
              (event["event_key"], event["category"], event["title"].strip(),
               event["summary"].strip(), event["state"], event.get("commit_ref", ""),
               _now())
            )
            self.conn.commit()
            return "published"
        except sqlite3.IntegrityError:
            return "duplicate"

    def list_public(self, limit=50):
        rows = self.conn.execute(
          """SELECT category,title,summary,state,commit_ref,created_at
             FROM public_build_journal ORDER BY id DESC LIMIT ?""",
          (max(1, min(int(limit), 100)),)
        ).fetchall()
        return {"entries": [dict(row) for row in rows]}
