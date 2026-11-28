"""Privacy-minimal customer problem submissions for product discovery.

Only voluntarily supplied problem descriptions are stored. Contact details are
optional and require a separate explicit permission checkbox. Request IPs are
never stored; a keyed fingerprint is retained briefly for abuse throttling.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import sqlite3
import time
from pathlib import Path


class FeedbackError(ValueError):
    pass


class CustomerFeedback:
    def __init__(self, db_path: str):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS customer_problem_submissions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          problem TEXT NOT NULL,
          context TEXT NOT NULL DEFAULT '',
          email TEXT NOT NULL DEFAULT '',
          contact_permission INTEGER NOT NULL DEFAULT 0,
          status TEXT NOT NULL DEFAULT 'NEW',
          created_at INTEGER NOT NULL,
          reviewed_at INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS customer_feedback_limits (
          fingerprint TEXT PRIMARY KEY,
          window_start INTEGER NOT NULL,
          request_count INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_customer_feedback_status
          ON customer_problem_submissions(status, id DESC);
        """)
        self.conn.commit()

    @staticmethod
    def fingerprint(client_ip: str, secret: str) -> str:
        if not secret or len(secret) < 32:
            raise FeedbackError("public feedback rate-limit secret is not configured")
        return hmac.new(secret.encode(), client_ip.encode(), hashlib.sha256).hexdigest()

    def submit(self, problem: str, context: str, email: str,
               contact_permission: bool, fingerprint: str) -> dict:
        problem = problem.strip()
        context = context.strip()
        email = email.strip().lower()
        if not 20 <= len(problem) <= 2000:
            raise FeedbackError("describe the problem in 20 to 2,000 characters")
        if len(context) > 1500:
            raise FeedbackError("additional context must be 1,500 characters or fewer")
        if len(email) > 254 or (email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)):
            raise FeedbackError("enter a valid email address or leave it blank")
        if contact_permission and not email:
            raise FeedbackError("an email is required when requesting a reply")
        if email and not contact_permission:
            email = ""  # Do not retain contact details without permission.
        now = int(time.time())
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.conn.execute(
                "SELECT window_start,request_count FROM customer_feedback_limits WHERE fingerprint=?",
                (fingerprint,),
            ).fetchone()
            if row and now - row["window_start"] < 3600 and row["request_count"] >= 3:
                self.conn.rollback()
                raise FeedbackError("submission limit reached; please try again later")
            if not row or now - row["window_start"] >= 3600:
                self.conn.execute(
                    """INSERT INTO customer_feedback_limits(fingerprint,window_start,request_count)
                       VALUES(?,?,1) ON CONFLICT(fingerprint) DO UPDATE SET
                       window_start=excluded.window_start,request_count=1""",
                    (fingerprint, now),
                )
            else:
                self.conn.execute(
                    "UPDATE customer_feedback_limits SET request_count=request_count+1 WHERE fingerprint=?",
                    (fingerprint,),
                )
            cur = self.conn.execute(
                """INSERT INTO customer_problem_submissions
                   (problem,context,email,contact_permission,created_at)
                   VALUES(?,?,?,?,?)""",
                (problem, context, email, int(contact_permission), now),
            )
            self.conn.commit()
            return {"id": cur.lastrowid, "status": "RECEIVED"}
        except Exception:
            if self.conn.in_transaction:
                self.conn.rollback()
            raise

    def get(self, submission_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM customer_problem_submissions WHERE id=?",
            (int(submission_id),),
        ).fetchone()
        return dict(row) if row else None

    def list(self, status: str = "NEW", limit: int = 100) -> list[dict]:
        if status not in {"NEW", "REVIEWED", "ROADMAP", "CLOSED", "ALL"}:
            raise FeedbackError("invalid submission status")
        limit = max(1, min(int(limit), 300))
        if status == "ALL":
            rows = self.conn.execute(
                "SELECT * FROM customer_problem_submissions ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM customer_problem_submissions WHERE status=? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_status(self, submission_id: int, status: str) -> dict:
        if status not in {"REVIEWED", "ROADMAP", "CLOSED"}:
            raise FeedbackError("status must be REVIEWED, ROADMAP, or CLOSED")
        cur = self.conn.execute(
            """UPDATE customer_problem_submissions SET status=?,reviewed_at=?
               WHERE id=? AND status!='CLOSED'""",
            (status, int(time.time()), int(submission_id)),
        )
        self.conn.commit()
        if cur.rowcount != 1:
            raise LookupError("submission not found or already closed")
        row = self.conn.execute(
            "SELECT id,status,reviewed_at FROM customer_problem_submissions WHERE id=?",
            (int(submission_id),),
        ).fetchone()
        return dict(row)
