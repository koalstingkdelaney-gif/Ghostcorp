"""Provider-neutral, simulation-only ledger event journal.

No wallet keys, bank details, card data, or personal identity are stored here.
This module does not move money, convert assets, or connect to a payment provider.
"""
import json
import re
import sqlite3
import time
from pathlib import Path


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class SimulationLedger:
    EVENT_TYPES = {"payment_pending", "payment_settled", "payment_available",
                   "refund", "dispute", "reconciled"}
    CURRENCIES = {"USD", "BTC", "USDC"}

    def __init__(self, db_path: str):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ledger_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                payment_id TEXT NOT NULL,
                division_slug TEXT NOT NULL,
                event_type TEXT NOT NULL,
                amount_minor INTEGER NOT NULL,
                currency TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'SIMULATED',
                details TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def record(self, event_id: str, payment_id: str, division_slug: str,
               event_type: str, amount_minor: int, currency: str, details: dict):
        if not re.fullmatch(r"[A-Za-z0-9._:-]{3,120}", event_id):
            raise ValueError("invalid event_id")
        if not re.fullmatch(r"[A-Za-z0-9._:-]{3,120}", payment_id):
            raise ValueError("invalid payment_id")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,38}[a-z0-9]", division_slug):
            raise ValueError("invalid division_slug")
        if event_type not in self.EVENT_TYPES:
            raise ValueError("unsupported event_type")
        if not isinstance(amount_minor, int) or isinstance(amount_minor, bool) or amount_minor <= 0:
            raise ValueError("amount_minor must be a positive integer")
        if currency not in self.CURRENCIES:
            raise ValueError("currency must be USD, BTC, or USDC")
        try:
            self.conn.execute(
                """INSERT INTO ledger_events(event_id,payment_id,division_slug,event_type,
                   amount_minor,currency,details,created_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (event_id, payment_id, division_slug, event_type, amount_minor,
                 currency, json.dumps(details or {}), _now()),
            )
            self.conn.commit()
            return "recorded"
        except sqlite3.IntegrityError:
            return "duplicate"

    def summary(self):
        rows = self.conn.execute(
            """SELECT event_type,currency,COUNT(*) AS count
               FROM ledger_events GROUP BY event_type,currency ORDER BY event_type,currency"""
        ).fetchall()
        total = self.conn.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0]
        return {"mode": "SIMULATED_ONLY", "live_money_enabled": False,
                "event_count": total, "groups": [dict(r) for r in rows]}
