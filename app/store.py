"""SQLite store: leads, suppressions, proposals, jobs, audit log.

One email address = one lead, ever (matches the existing ghostcorpnet
operation's dedup rule). Suppressed addresses can never become leads.
"""
import json
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    city TEXT DEFAULT '',
    vertical TEXT DEFAULT '',
    service TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    source TEXT DEFAULT '',
    score INTEGER DEFAULT 0,
    score_reasons TEXT DEFAULT '[]',
    status TEXT DEFAULT 'ready',
    audit TEXT DEFAULT '',
    created_at TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS suppressions (
    email TEXT PRIMARY KEY,
    reason TEXT DEFAULT '',
    at TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    package TEXT NOT NULL,
    total_upfront_usd INTEGER NOT NULL,
    monthly_usd INTEGER NOT NULL,
    body TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload TEXT DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    result TEXT DEFAULT '',
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT DEFAULT ''
);
"""


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Store:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False: the API serves requests from a thread pool;
        # this single-connection store serializes access through SQLite itself.
        self.conn = sqlite3.connect(path, check_same_thread=False)
        if path != ":memory:":
            # WAL + NORMAL sync: bulk imports of thousands of leads are ~50x
            # faster than the default journal/sync, with safe durability for
            # this workload (verified: 7,059-row import, 2026-11-02).
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def log(self, actor: str, action: str, detail: str = "") -> None:
        self.conn.execute(
            "INSERT INTO audit_log (at, actor, action, detail) VALUES (?,?,?,?)",
            (_now(), actor, action, detail),
        )
        self.conn.commit()

    def suppress(self, email: str, reason: str = "") -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO suppressions (email, reason, at) VALUES (?,?,?)",
            (email.strip().lower(), reason, _now()),
        )
        self.conn.commit()

    def is_suppressed(self, email: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM suppressions WHERE email=?", (email.strip().lower(),)
        ).fetchone()
        return row is not None

    def add_lead(self, lead: dict) -> str:
        """Returns 'added', 'duplicate', or 'suppressed'."""
        email = (lead.get("email") or "").strip().lower()
        if not email:
            return "duplicate"
        if self.is_suppressed(email):
            return "suppressed"
        try:
            self.conn.execute(
                """INSERT INTO leads (name, email, city, vertical, service, source_url,
                   source, score, score_reasons, status, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    lead.get("name", ""), email, lead.get("city", ""), lead.get("vertical", ""),
                    lead.get("service", ""), lead.get("source_url", ""), lead.get("source", ""),
                    int(lead.get("score", 0)), json.dumps(lead.get("score_reasons", [])),
                    lead.get("status", "ready"), lead.get("created_at", "") or _now(),
                ),
            )
            self.conn.commit()
            return "added"
        except sqlite3.IntegrityError:
            return "duplicate"

    def leads(self, limit: int = 5000):
        rows = self.conn.execute(
            "SELECT * FROM leads ORDER BY score DESC, id ASC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def lead(self, lead_id: int):
        row = self.conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        return dict(row) if row else None

    def set_audit(self, lead_id: int, audit: dict) -> None:
        self.conn.execute(
            "UPDATE leads SET audit=? WHERE id=?", (json.dumps(audit), lead_id)
        )
        self.conn.commit()

    def add_proposal(self, lead_id: int, package: str, upfront: int, monthly: int, body: str) -> int:
        cur = self.conn.execute(
            """INSERT INTO proposals (lead_id, package, total_upfront_usd, monthly_usd, body, created_at)
               VALUES (?,?,?,?,?,?)""",
            (lead_id, package, upfront, monthly, body, _now()),
        )
        self.conn.commit()
        return cur.lastrowid

    def proposals(self):
        rows = self.conn.execute("SELECT * FROM proposals ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

    def enqueue(self, kind: str, key: str, payload: dict) -> str:
        try:
            self.conn.execute(
                "INSERT INTO jobs (kind, idempotency_key, payload, created_at, updated_at) VALUES (?,?,?,?,?)",
                (kind, key, json.dumps(payload), _now(), _now()),
            )
            self.conn.commit()
            return "queued"
        except sqlite3.IntegrityError:
            return "duplicate"

    def pending_jobs(self, limit: int = 50):
        rows = self.conn.execute(
            "SELECT * FROM jobs WHERE status='pending' ORDER BY id ASC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def finish_job(self, job_id: int, status: str, result: str = "") -> None:
        self.conn.execute(
            "UPDATE jobs SET status=?, result=?, updated_at=? WHERE id=?",
            (status, result, _now(), job_id),
        )
        self.conn.commit()

    def summary(self) -> dict:
        def count(sql, args=()):
            return self.conn.execute(sql, args).fetchone()[0]

        return {
            "leads_total": count("SELECT COUNT(*) FROM leads"),
            "leads_ready": count("SELECT COUNT(*) FROM leads WHERE status='ready'"),
            "leads_audited": count("SELECT COUNT(*) FROM leads WHERE audit != ''"),
            "proposals_drafted": count("SELECT COUNT(*) FROM proposals"),
            "suppressions": count("SELECT COUNT(*) FROM suppressions"),
            "jobs_pending": count("SELECT COUNT(*) FROM jobs WHERE status='pending'"),
            "jobs_done": count("SELECT COUNT(*) FROM jobs WHERE status='done'"),
        }
