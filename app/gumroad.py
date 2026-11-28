"""Read-only Gumroad sale verification and idempotent revenue event ledger.

Gumroad remains the checkout and digital-delivery provider. This adapter
verifies each Ping's sale ID against Gumroad's authenticated sales API before
recording it. It never refunds, edits payouts, changes products or stores buyer
email/card data.
"""
from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from urllib.parse import quote

import httpx


class GumroadError(ValueError):
    pass


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


class GumroadSales:
    def __init__(self, db_path: str, transport=None):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS gumroad_verified_sales (
          sale_id TEXT PRIMARY KEY,
          product_permalink TEXT NOT NULL,
          status TEXT NOT NULL,
          amount_raw TEXT NOT NULL DEFAULT '',
          currency TEXT NOT NULL DEFAULT '',
          provider_created_at TEXT NOT NULL DEFAULT '',
          verified_at INTEGER NOT NULL,
          updated_at INTEGER NOT NULL
        )
        """)
        self.conn.commit()
        self.transport = transport

    @staticmethod
    def config():
        token = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
        ping_secret = os.environ.get("GUMROAD_PING_SECRET", "")
        allowed = {
            item.strip() for item in os.environ.get("GUMROAD_ALLOWED_PERMALINKS", "").split(",")
            if item.strip()
        }
        return token, ping_secret, allowed

    @classmethod
    def configured(cls) -> bool:
        token, secret, allowed = cls.config()
        return bool(token and len(secret) >= 32 and allowed)

    def verify_and_record(self, ping: dict) -> dict:
        token, _, allowed = self.config()
        if not token or not allowed:
            raise GumroadError("Gumroad read-only sales integration is not configured")
        resource = str(ping.get("resource_name", "sale")).strip().lower()
        if resource not in {"sale", "refund"}:
            return {"outcome": "ignored_unsupported_event", "resource_name": resource}
        sale_id = str(ping.get("sale_id", "")).strip()
        if not sale_id or len(sale_id) > 180 or any(ch in sale_id for ch in "/\\?#"):
            raise GumroadError("invalid Gumroad sale identifier")
        url = "https://api.gumroad.com/v2/sales/" + quote(sale_id, safe="")
        try:
            with httpx.Client(timeout=12.0, follow_redirects=False,
                              transport=self.transport) as client:
                response = client.get(url, params={"access_token": token},
                                      headers={"Accept": "application/json"})
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            raise GumroadError("Gumroad sale verification request failed") from exc
        if not isinstance(body, dict) or body.get("success") is not True:
            raise GumroadError("Gumroad did not verify this sale")
        sale = body.get("sale")
        if not isinstance(sale, dict) or str(sale.get("id", "")) != sale_id:
            raise GumroadError("Gumroad sale identity did not match the Ping")
        permalink = str(sale.get("product_permalink", "")).strip()
        if permalink not in allowed:
            raise GumroadError("sale product is not in GhostCorp's approved product allowlist")
        refunded = _truthy(sale.get("refunded", False))
        if resource == "refund" and not refunded:
            raise GumroadError("Gumroad has not confirmed the refund")
        status = "REFUNDED" if refunded else "PAID_VERIFIED"
        amount_raw = str(sale.get("price", ""))
        currency = str(sale.get("currency", "")).upper()
        provider_created_at = str(sale.get("created_at", ""))
        now = int(time.time())
        self.conn.execute(
            """INSERT INTO gumroad_verified_sales
               (sale_id,product_permalink,status,amount_raw,currency,
                provider_created_at,verified_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?)
               ON CONFLICT(sale_id) DO UPDATE SET
                 product_permalink=excluded.product_permalink,
                 status=excluded.status,amount_raw=excluded.amount_raw,
                 currency=excluded.currency,
                 provider_created_at=excluded.provider_created_at,
                 updated_at=excluded.updated_at""",
            (sale_id, permalink, status, amount_raw, currency,
             provider_created_at, now, now),
        )
        self.conn.commit()
        return {"outcome": "recorded", "sale_id": sale_id, "product_permalink": permalink,
                "status": status, "amount_raw": amount_raw, "currency": currency,
                "amount_units": "GUMROAD_API_RAW_UNCONVERTED"}

    def list(self, limit: int = 100) -> list[dict]:
        limit = max(1, min(int(limit), 300))
        rows = self.conn.execute(
            """SELECT sale_id,product_permalink,status,amount_raw,currency,
                      provider_created_at,verified_at,updated_at
               FROM gumroad_verified_sales ORDER BY updated_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
