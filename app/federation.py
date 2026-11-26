"""Identity-minimal GhostCorp federation registry.

This registry stores project/division identifiers and machine identities only.
It deliberately has no fields for personal names, personal email, birth dates,
government IDs, addresses, or identity documents. Provisioning is disabled
unless FEDERATION_ADMIN_TOKEN is configured outside the repository.
"""
import hashlib
import re
import secrets
import sqlite3
import time
from pathlib import Path


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class FederationRegistry:
    def __init__(self, db_path: str):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS divisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            purpose TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'PROVISIONED',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS machine_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL UNIQUE,
            division_slug TEXT NOT NULL,
            role TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PROVISIONED',
            created_at TEXT NOT NULL,
            FOREIGN KEY (division_slug) REFERENCES divisions(slug)
        );
        """)
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.commit()

    @staticmethod
    def valid_slug(value: str) -> bool:
        return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{1,38}[a-z0-9]", value))

    def create_division(self, slug: str, display_name: str, purpose: str):
        if not self.valid_slug(slug):
            raise ValueError("slug must be 3-40 lowercase letters, numbers, or hyphens")
        try:
            cur = self.conn.execute(
                "INSERT INTO divisions(slug,display_name,purpose,created_at) VALUES(?,?,?,?)",
                (slug, display_name.strip(), purpose.strip(), _now()),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValueError("division slug already exists") from exc

    def create_agent(self, division_slug: str, role: str):
        allowed_roles = {"coordinator", "researcher", "builder", "tester", "analyst", "operator"}
        if role not in allowed_roles:
            raise ValueError("unsupported machine role")
        if not self.conn.execute("SELECT 1 FROM divisions WHERE slug=?", (division_slug,)).fetchone():
            raise LookupError("division not found")
        machine_id = "gca_" + secrets.token_hex(12)
        token = secrets.token_urlsafe(32)
        self.conn.execute(
            """INSERT INTO machine_agents(machine_id,division_slug,role,token_hash,created_at)
               VALUES(?,?,?,?,?)""",
            (machine_id, division_slug, role, _token_hash(token), _now()),
        )
        self.conn.commit()
        return {"machine_id": machine_id, "division": division_slug, "role": role,
                "status": "PROVISIONED", "agent_token": token}

    def status(self):
        divisions = self.conn.execute(
            "SELECT slug,display_name,purpose,status,created_at FROM divisions ORDER BY id"
        ).fetchall()
        agents = self.conn.execute(
            "SELECT machine_id,division_slug,role,status,created_at FROM machine_agents ORDER BY id"
        ).fetchall()
        return {
            "mode": "registry_provisioned_not_running",
            "personal_identity_fields": False,
            "divisions": [dict(r) for r in divisions],
            "agents": [dict(r) for r in agents],
            "counts": {"divisions": len(divisions), "agents": len(agents)},
        }
