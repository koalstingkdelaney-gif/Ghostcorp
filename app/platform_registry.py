"""GhostCorp platform registry: capability status and opt-in compute contributors.

This module records consent and node health. It deliberately does not execute
remote code or scan public networks. Contributors are pending until an owner
approves enrollment and receives a one-time node token.
"""
import hashlib
import json
import secrets
import sqlite3
import time
from pathlib import Path


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


CAPABILITIES = [
    ("infrastructure-discovery", "Discover permitted free infrastructure", "PLANNED"),
    ("distributed-compute", "Opt-in contributor compute registry", "PARTIAL"),
    ("corporate-partnerships", "Corporate compute partnership pipeline", "PLANNED"),
    ("mesh-communications", "Meshtastic low-bandwidth communications adapter", "PLANNED"),
    ("persistent-memory", "Durable vector and knowledge-graph memory", "PLANNED"),
    ("software-factory", "Sandboxed build, test and release workflow", "PLANNED"),
    ("model-operations", "Local model catalogue and resource-aware routing", "PLANNED"),
    ("business-communications", "Authorized email and customer communication", "PLANNED"),
    ("security-recovery", "Security monitoring and recovery workflows", "PLANNED"),
    ("finance-controls", "Ledger, budget and payout approval controls", "PARTIAL"),
    ("vr-business-console", "VR headquarters business console", "PLANNED"),
    ("disaster-recovery", "Backup, failover and recovery verification", "PLANNED"),
]


class PlatformRegistry:
    def __init__(self, db_path):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS platform_capabilities(
          slug TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL,
          detail TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS compute_contributors(
          node_id TEXT PRIMARY KEY, display_name TEXT NOT NULL,
          consent_version TEXT NOT NULL, resources TEXT NOT NULL,
          status TEXT NOT NULL, token_hash TEXT NOT NULL DEFAULT '',
          last_seen TEXT NOT NULL DEFAULT '', metrics TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
        );
        """)
        columns = {row[1] for row in self.conn.execute('PRAGMA table_info(compute_contributors)')}
        if 'metrics' not in columns:
            self.conn.execute("ALTER TABLE compute_contributors ADD COLUMN metrics TEXT NOT NULL DEFAULT '{}'")
        for slug, title, status in CAPABILITIES:
            self.conn.execute(
                "INSERT OR IGNORE INTO platform_capabilities VALUES(?,?,?,?,?)",
                (slug, title, status, "Initial platform capability tracking record.", _now()))
        self.conn.commit()

    def capabilities(self):
        rows = self.conn.execute(
            "SELECT slug,title,status,detail,updated_at FROM platform_capabilities ORDER BY slug"
        ).fetchall()
        return [dict(r) for r in rows]

    def enroll(self, display_name, consent_version, resources):
        display_name = str(display_name).strip()
        if len(display_name) < 2 or len(display_name) > 80:
            raise ValueError("display name must contain 2 to 80 characters")
        if not isinstance(resources, dict):
            raise ValueError("resources must be an object")
        if "gpu" in resources and not isinstance(resources["gpu"], bool):
            raise ValueError("gpu must be a boolean")
        node_id = "gcnode_" + secrets.token_urlsafe(12)
        clean = {
            "cpu_cores": max(0, min(int(resources.get("cpu_cores", 0)), 256)),
            "ram_mb": max(0, min(int(resources.get("ram_mb", 0)), 1048576)),
            "disk_mb": max(0, min(int(resources.get("disk_mb", 0)), 10485760)),
            "gpu": bool(resources.get("gpu", False)),
            "allowed_workloads": ["public-build-test", "synthetic-benchmark"],
        }
        self.conn.execute(
            """INSERT INTO compute_contributors
            (node_id,display_name,consent_version,resources,status,created_at)
            VALUES(?,?,?,?,?,?)""",
            (node_id, display_name, consent_version, json.dumps(clean),
             "PENDING_REVIEW", _now()))
        self.conn.commit()
        return {"node_id": node_id, "status": "PENDING_REVIEW",
                "resources_recorded": clean, "message": "No workload can run before explicit approval."}

    def approve(self, node_id):
        row = self.conn.execute(
            "SELECT status FROM compute_contributors WHERE node_id=?", (node_id,)).fetchone()
        if not row:
            raise LookupError("contributor not found")
        if row["status"] != "PENDING_REVIEW":
            raise ValueError("only pending contributors can be approved")
        token = secrets.token_urlsafe(36)
        digest = hashlib.sha256(token.encode()).hexdigest()
        self.conn.execute(
            "UPDATE compute_contributors SET status='ACTIVE',token_hash=? WHERE node_id=?",
            (digest, node_id))
        self.conn.commit()
        return {"node_id": node_id, "status": "ACTIVE", "node_token": token,
                "warning": "Store this token securely; it is shown only once."}

    def authenticate(self, token):
        digest = hashlib.sha256(token.encode()).hexdigest()
        row = self.conn.execute(
            "SELECT node_id,status FROM compute_contributors WHERE token_hash=?",
            (digest,)).fetchone()
        return dict(row) if row and row["status"] == "ACTIVE" else None

    def heartbeat(self, node_id, metrics):
        safe = {
            "cpu_percent": max(0.0, min(float(metrics.get("cpu_percent", 0)), 100.0)),
            "ram_used_mb": max(0, min(int(metrics.get("ram_used_mb", 0)), 1048576)),
            "paused": bool(metrics.get("paused", False)),
        }
        cur = self.conn.execute(
            "UPDATE compute_contributors SET last_seen=?,metrics=? WHERE node_id=? AND status='ACTIVE'",
            (_now(), json.dumps(safe), node_id))
        self.conn.commit()
        if cur.rowcount != 1:
            raise LookupError("active contributor not found")
        return {"node_id": node_id, "status": "ACTIVE", "metrics": safe, "received_at": _now()}

    def revoke(self, node_id):
        cur = self.conn.execute(
            "UPDATE compute_contributors SET status='REVOKED',token_hash='' WHERE node_id=?",
            (node_id,))
        self.conn.commit()
        if cur.rowcount != 1:
            raise LookupError("contributor not found")
        return {"node_id": node_id, "status": "REVOKED"}

    def list_nodes(self):
        rows = self.conn.execute(
            """SELECT node_id,display_name,consent_version,resources,status,last_seen,metrics,created_at
            FROM compute_contributors ORDER BY created_at DESC""").fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["resources"] = json.loads(item["resources"])
            item["metrics"] = json.loads(item["metrics"])
            result.append(item)
        return result

    def capacity_snapshot(self):
        rows = self.conn.execute(
            "SELECT resources,metrics,last_seen FROM compute_contributors WHERE status='ACTIVE'"
        ).fetchall()
        totals = {"registered_nodes": len(rows), "declared_cpu_cores": 0,
                  "declared_ram_mb": 0, "declared_disk_mb": 0,
                  "nodes_reporting": 0, "nodes_paused": 0}
        for row in rows:
            resources = json.loads(row["resources"])
            metrics = json.loads(row["metrics"])
            totals["declared_cpu_cores"] += resources.get("cpu_cores", 0)
            totals["declared_ram_mb"] += resources.get("ram_mb", 0)
            totals["declared_disk_mb"] += resources.get("disk_mb", 0)
            if row["last_seen"]:
                totals["nodes_reporting"] += 1
            if metrics.get("paused"):
                totals["nodes_paused"] += 1
        totals["note"] = "Contributor-declared capacity, not independently verified or currently schedulable."
        return totals

    def summary(self):
        rows = self.conn.execute(
            "SELECT status,COUNT(*) AS n FROM compute_contributors GROUP BY status").fetchall()
        return {"contributors_by_status": {r["status"]: r["n"] for r in rows},
                "capabilities_tracked": len(CAPABILITIES),
                "capacity": self.capacity_snapshot(),
                "remote_code_execution": False,
                "compute_mode": "CONSENT_REGISTRY_ONLY"}
