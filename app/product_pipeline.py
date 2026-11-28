"""Owner-reviewed digital product draft and validation pipeline.

This registry prepares product briefs and records evidence. It never publishes
to Gumroad, changes checkout, charges customers, or promises a product exists.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path


FORMATS = {"pdf", "template", "software", "course", "game", "other"}
STATUSES = {"DRAFT", "VALIDATION_RECORDED", "APPROVED_FOR_LISTING", "REJECTED"}


class ProductPipelineError(ValueError):
    pass


class ProductPipeline:
    def __init__(self, db_path: str):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS product_drafts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_submission_id INTEGER NOT NULL DEFAULT 0,
          title TEXT NOT NULL,
          problem TEXT NOT NULL,
          audience TEXT NOT NULL,
          solution TEXT NOT NULL,
          description TEXT NOT NULL,
          format TEXT NOT NULL,
          proposed_price_cents INTEGER NOT NULL DEFAULT 0,
          currency TEXT NOT NULL DEFAULT 'USD',
          status TEXT NOT NULL DEFAULT 'DRAFT',
          validation TEXT NOT NULL DEFAULT '{}',
          created_at INTEGER NOT NULL,
          updated_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_product_drafts_status
          ON product_drafts(status, id DESC);
        """)
        self.conn.commit()

    def create(self, payload: dict) -> dict:
        required = ("title", "problem", "audience", "solution", "description", "format")
        values = {key: str(payload.get(key, "")).strip() for key in required}
        limits = {"title": (4, 120), "problem": (20, 2000), "audience": (5, 300),
                  "solution": (20, 2000), "description": (40, 5000)}
        for key, (minimum, maximum) in limits.items():
            if not minimum <= len(values[key]) <= maximum:
                raise ProductPipelineError(f"{key} must be {minimum}-{maximum} characters")
        if values["format"] not in FORMATS:
            raise ProductPipelineError("unsupported product format")
        price = int(payload.get("proposed_price_cents", 0))
        if not 0 <= price <= 1_000_000:
            raise ProductPipelineError("proposed price must be between 0 and 10000 USD")
        source_id = int(payload.get("source_submission_id", 0))
        if source_id < 0:
            raise ProductPipelineError("invalid source submission")
        now = int(time.time())
        cur = self.conn.execute(
            """INSERT INTO product_drafts
               (source_submission_id,title,problem,audience,solution,description,format,
                proposed_price_cents,status,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (source_id, values["title"], values["problem"], values["audience"],
             values["solution"], values["description"], values["format"],
             price, "DRAFT", now, now),
        )
        self.conn.commit()
        return self.get(cur.lastrowid)

    def get(self, product_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM product_drafts WHERE id=?",
                                (int(product_id),)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["validation"] = json.loads(result["validation"])
        return result

    def list(self, status: str = "ALL", limit: int = 100) -> list[dict]:
        if status != "ALL" and status not in STATUSES:
            raise ProductPipelineError("invalid product status")
        limit = max(1, min(int(limit), 300))
        query = "SELECT id FROM product_drafts"
        args: tuple = ()
        if status != "ALL":
            query += " WHERE status=?"
            args = (status,)
        query += " ORDER BY id DESC LIMIT ?"
        rows = self.conn.execute(query, args + (limit,)).fetchall()
        return [self.get(row["id"]) for row in rows]

    def record_validation(self, product_id: int, checks: list[dict],
                           evidence_summary: str) -> dict:
        product = self.get(product_id)
        if not product:
            raise LookupError("product draft not found")
        if product["status"] not in {"DRAFT", "VALIDATION_RECORDED"}:
            raise ProductPipelineError("product is not open for validation")
        if not isinstance(checks, list) or not 3 <= len(checks) <= 20:
            raise ProductPipelineError("provide 3-20 validation checks")
        normalized = []
        for check in checks:
            if not isinstance(check, dict):
                raise ProductPipelineError("each check must be an object")
            name = str(check.get("name", "")).strip()[:100]
            passed = check.get("passed")
            evidence = str(check.get("evidence", "")).strip()[:500]
            if not name or not isinstance(passed, bool) or not evidence:
                raise ProductPipelineError("each check needs a name, boolean result and evidence")
            normalized.append({"name": name, "passed": passed, "evidence": evidence})
        summary = str(evidence_summary).strip()
        if not 20 <= len(summary) <= 1500:
            raise ProductPipelineError("evidence summary must be 20-1,500 characters")
        validation = {"checks": normalized, "all_passed": all(c["passed"] for c in normalized),
                      "evidence_summary": summary, "recorded_by": "owner"}
        now = int(time.time())
        self.conn.execute(
            "UPDATE product_drafts SET validation=?,status='VALIDATION_RECORDED',updated_at=? WHERE id=?",
            (json.dumps(validation, separators=(",", ":")), now, int(product_id)),
        )
        self.conn.commit()
        return self.get(product_id)

    def decide(self, product_id: int, decision: str) -> dict:
        product = self.get(product_id)
        if not product:
            raise LookupError("product draft not found")
        if decision not in {"APPROVED_FOR_LISTING", "REJECTED"}:
            raise ProductPipelineError("decision must be APPROVED_FOR_LISTING or REJECTED")
        if product["status"] != "VALIDATION_RECORDED":
            raise ProductPipelineError("record validation evidence before owner decision")
        if decision == "APPROVED_FOR_LISTING" and not product["validation"].get("all_passed"):
            raise ProductPipelineError("failed validation checks cannot be approved")
        self.conn.execute(
            "UPDATE product_drafts SET status=?,updated_at=? WHERE id=?",
            (decision, int(time.time()), int(product_id)),
        )
        self.conn.commit()
        return self.get(product_id)
