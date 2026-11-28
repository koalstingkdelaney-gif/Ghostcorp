"""Customer-approved website audit and service handoff workflow.

Public intake is consent-based. Audits use the existing SSRF-hardened,
robots-aware crawler. Proposals are based only on the existing rate card.
Customers must explicitly approve a proposal before an owner can mark delivery
in progress. The workflow never sends email, charges, refunds or deploys code.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlparse


class ServiceWorkflowError(ValueError):
    pass


class WebsiteServiceWorkflow:
    def __init__(self, db_path: str):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS website_service_requests (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          business_name TEXT NOT NULL,
          website_url TEXT NOT NULL,
          contact_email TEXT NOT NULL,
          package TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'RECEIVED',
          audit_json TEXT NOT NULL DEFAULT '{}',
          proposal_json TEXT NOT NULL DEFAULT '{}',
          approval_token_hash TEXT NOT NULL DEFAULT '',
          token_expires_at INTEGER NOT NULL DEFAULT 0,
          accepted_at INTEGER NOT NULL DEFAULT 0,
          delivery_notes TEXT NOT NULL DEFAULT '',
          deliverable_url TEXT NOT NULL DEFAULT '',
          payment_sale_id TEXT NOT NULL DEFAULT '',
          created_at INTEGER NOT NULL,
          updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS website_service_limits (
          fingerprint TEXT PRIMARY KEY,
          window_start INTEGER NOT NULL,
          request_count INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_website_service_status
          ON website_service_requests(status,id DESC);
        """)
        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(website_service_requests)")}
        if "payment_sale_id" not in columns:
            self.conn.execute("ALTER TABLE website_service_requests ADD COLUMN payment_sale_id TEXT NOT NULL DEFAULT ''")
        self.conn.commit()

    @staticmethod
    def fingerprint(client_ip: str, secret: str) -> str:
        if not secret or len(secret) < 32:
            raise ServiceWorkflowError("service intake rate-limit secret is not configured")
        return hmac.new(secret.encode(), client_ip.encode(), hashlib.sha256).hexdigest()

    def _consume_limit(self, fingerprint: str, now: int):
        self.conn.execute("BEGIN IMMEDIATE")
        row = self.conn.execute(
            "SELECT window_start,request_count FROM website_service_limits WHERE fingerprint=?",
            (fingerprint,),
        ).fetchone()
        if row and now - row["window_start"] < 3600 and row["request_count"] >= 3:
            self.conn.rollback()
            raise ServiceWorkflowError("request limit reached; try again later")
        if not row or now - row["window_start"] >= 3600:
            self.conn.execute(
                """INSERT INTO website_service_limits(fingerprint,window_start,request_count)
                   VALUES(?,?,1) ON CONFLICT(fingerprint) DO UPDATE SET
                   window_start=excluded.window_start,request_count=1""",
                (fingerprint, now),
            )
        else:
            self.conn.execute(
                "UPDATE website_service_limits SET request_count=request_count+1 WHERE fingerprint=?",
                (fingerprint,),
            )

    def create_request(self, business_name: str, website_url: str, email: str,
                       package: str, fingerprint: str, allowed_packages: set[str]) -> dict:
        business_name = business_name.strip()
        website_url = website_url.strip()
        email = email.strip().lower()
        package = package.strip()
        parsed = urlparse(website_url)
        if not 2 <= len(business_name) <= 100:
            raise ServiceWorkflowError("business name must be 2-100 characters")
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ServiceWorkflowError("enter a public HTTPS website URL")
        if len(website_url) > 2048 or len(email) > 254:
            raise ServiceWorkflowError("website or email is too long")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ServiceWorkflowError("enter a valid contact email")
        if package not in allowed_packages:
            raise ServiceWorkflowError("select an available service package")
        now = int(time.time())
        self._consume_limit(fingerprint, now)
        try:
            cur = self.conn.execute(
                """INSERT INTO website_service_requests
                   (business_name,website_url,contact_email,package,status,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (business_name, website_url, email, package, "RECEIVED", now, now),
            )
            self.conn.commit()
            return self.get(cur.lastrowid)
        except Exception:
            if self.conn.in_transaction:
                self.conn.rollback()
            raise

    def get(self, request_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM website_service_requests WHERE id=?",
                                (int(request_id),)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["audit"] = json.loads(result.pop("audit_json"))
        result["proposal"] = json.loads(result.pop("proposal_json"))
        return result

    def list(self, limit: int = 100) -> list[dict]:
        limit = max(1, min(int(limit), 300))
        rows = self.conn.execute(
            "SELECT id FROM website_service_requests ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self.get(row["id"]) for row in rows]

    def record_audit(self, request_id: int, audit: dict) -> dict:
        item = self.get(request_id)
        if not item:
            raise LookupError("service request not found")
        if item["status"] != "RECEIVED":
            raise ServiceWorkflowError("audit can only be recorded for a new request")
        self.conn.execute(
            "UPDATE website_service_requests SET audit_json=?,status='AUDITED',updated_at=? WHERE id=?",
            (json.dumps(audit, separators=(",", ":")), int(time.time()), int(request_id)),
        )
        self.conn.commit()
        return self.get(request_id)

    def record_proposal(self, request_id: int, proposal: dict) -> dict:
        item = self.get(request_id)
        if not item:
            raise LookupError("service request not found")
        if item["status"] != "AUDITED":
            raise ServiceWorkflowError("complete the website audit before drafting a proposal")
        self.conn.execute(
            "UPDATE website_service_requests SET proposal_json=?,status='PROPOSAL_READY',updated_at=? WHERE id=?",
            (json.dumps(proposal, separators=(",", ":")), int(time.time()), int(request_id)),
        )
        self.conn.commit()
        return self.get(request_id)

    def issue_customer_approval(self, request_id: int) -> tuple[dict, str]:
        item = self.get(request_id)
        if not item:
            raise LookupError("service request not found")
        if item["status"] != "PROPOSAL_READY":
            raise ServiceWorkflowError("proposal must be ready before requesting customer approval")
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expiry = int(time.time()) + 7 * 24 * 60 * 60
        self.conn.execute(
            """UPDATE website_service_requests SET status='AWAITING_CUSTOMER_APPROVAL',
               approval_token_hash=?,token_expires_at=?,updated_at=? WHERE id=?""",
            (token_hash, expiry, int(time.time()), int(request_id)),
        )
        self.conn.commit()
        return self.get(request_id), token

    def get_public_approval(self, token: str) -> dict:
        if not token or len(token) > 200:
            raise LookupError("approval link is invalid or expired")
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        row = self.conn.execute(
            "SELECT * FROM website_service_requests WHERE approval_token_hash=?",
            (token_hash,),
        ).fetchone()
        if not row or row["status"] != "AWAITING_CUSTOMER_APPROVAL" or row["token_expires_at"] < int(time.time()):
            raise LookupError("approval link is invalid or expired")
        return {"business_name": row["business_name"], "website_url": row["website_url"],
                "package": row["package"], "proposal": json.loads(row["proposal_json"]),
                "expires_at": row["token_expires_at"]}

    def customer_decide(self, token: str, decision: str) -> dict:
        if decision not in {"ACCEPTED", "DECLINED"}:
            raise ServiceWorkflowError("decision must be ACCEPTED or DECLINED")
        public = self.get_public_approval(token)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        status = "CUSTOMER_APPROVED" if decision == "ACCEPTED" else "CUSTOMER_DECLINED"
        cur = self.conn.execute(
            """UPDATE website_service_requests SET status=?,accepted_at=?,updated_at=?,
               approval_token_hash='' WHERE approval_token_hash=? AND status='AWAITING_CUSTOMER_APPROVAL'""",
            (status, int(time.time()) if decision == "ACCEPTED" else 0,
             int(time.time()), token_hash),
        )
        self.conn.commit()
        if cur.rowcount != 1:
            raise LookupError("approval link was already used")
        return {"status": status, "business_name": public["business_name"]}

    def update_delivery(self, request_id: int, status: str,
                        notes: str = "", deliverable_url: str = "",
                        payment_sale_id: str = "") -> dict:
        if status not in {"IN_PROGRESS", "DELIVERED"}:
            raise ServiceWorkflowError("delivery status must be IN_PROGRESS or DELIVERED")
        item = self.get(request_id)
        if not item:
            raise LookupError("service request not found")
        if item["status"] not in {"CUSTOMER_APPROVED", "IN_PROGRESS"}:
            raise ServiceWorkflowError("customer approval is required before delivery")
        if not payment_sale_id or len(payment_sale_id) > 180:
            raise ServiceWorkflowError("a verified Gumroad payment reference is required")
        if status == "DELIVERED":
            parsed = urlparse(deliverable_url)
            if parsed.scheme != "https" or not parsed.hostname:
                raise ServiceWorkflowError("a public HTTPS deliverable URL is required")
            if len(notes.strip()) < 20:
                raise ServiceWorkflowError("delivery notes must describe the completed work")
        self.conn.execute(
            """UPDATE website_service_requests SET status=?,delivery_notes=?,
               deliverable_url=?,payment_sale_id=?,updated_at=? WHERE id=?""",
            (status, notes.strip()[:2000], deliverable_url.strip()[:2048],
             payment_sale_id, int(time.time()), int(request_id)),
        )
        self.conn.commit()
        return self.get(request_id)
