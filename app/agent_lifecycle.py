"""Persistent agent wake/work/sleep/dream lifecycle.

Lifecycle state is coordination metadata, not evidence of consciousness. Dream
work is represented as proposals and must run in a separately provisioned,
restricted sandbox before any code is executed.
"""
import json
import sqlite3
import threading
import time
from pathlib import Path

MODES = {"INITIALIZING", "WORKING", "SLEEPING", "DREAMING", "WAKING", "PAUSED"}
TRANSITIONS = {
    "INITIALIZING": {"WORKING", "PAUSED"},
    "WORKING": {"SLEEPING", "PAUSED"},
    "SLEEPING": {"DREAMING", "WAKING", "PAUSED"},
    "DREAMING": {"WAKING", "PAUSED"},
    "WAKING": {"WORKING", "PAUSED"},
    "PAUSED": {"INITIALIZING", "WORKING", "SLEEPING"},
}
DREAM_TYPES = {"idea", "research", "prototype-plan", "skill-proposal", "world-change-proposal", "customer-research", "customer-acquisition-plan", "business-model", "workflow-improvement", "product-opportunity", "product-release-plan"}


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class AgentLifecycle:
    def __init__(self, db_path):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS agent_lifecycle (
          machine_id TEXT PRIMARY KEY,
          mode TEXT NOT NULL DEFAULT 'INITIALIZING',
          cycle INTEGER NOT NULL DEFAULT 0,
          last_transition TEXT NOT NULL,
          current_goal TEXT NOT NULL DEFAULT '',
          sleep_reason TEXT NOT NULL DEFAULT '',
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS dream_artifacts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          machine_id TEXT NOT NULL,
          division_slug TEXT NOT NULL,
          cycle INTEGER NOT NULL,
          artifact_type TEXT NOT NULL,
          title TEXT NOT NULL,
          summary TEXT NOT NULL,
          artifact TEXT NOT NULL DEFAULT '{}',
          status TEXT NOT NULL DEFAULT 'AWAITING_REVIEW',
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_dream_artifacts_review
          ON dream_artifacts(status,created_at DESC);
        """)
        self.conn.commit()

    def register(self, machine_id):
        with self.lock:
            self.conn.execute(
                """INSERT OR IGNORE INTO agent_lifecycle
                   (machine_id,mode,last_transition,updated_at) VALUES(?,'INITIALIZING',?,?)""",
                (machine_id,_now(),_now()))
            self.conn.commit()
            return self.get(machine_id)

    def get(self, machine_id):
        with self.lock:
            row = self.conn.execute(
                "SELECT * FROM agent_lifecycle WHERE machine_id=?", (machine_id,)
            ).fetchone()
            return dict(row) if row else None

    def transition(self, machine_id, target, goal="", reason=""):
        if target not in MODES:
            raise ValueError("unknown lifecycle mode")
        if len(goal) > 200 or len(reason) > 300:
            raise ValueError("goal or reason is too long")
        with self.lock:
            current = self.get(machine_id)
            if not current:
                raise LookupError("agent lifecycle is not registered")
            source = current["mode"]
            if target not in TRANSITIONS[source]:
                raise ValueError(f"invalid lifecycle transition: {source} -> {target}")
            cycle = current["cycle"] + (1 if target == "WORKING" and source in {"INITIALIZING","WAKING","PAUSED"} else 0)
            now = _now()
            self.conn.execute(
                """UPDATE agent_lifecycle SET mode=?,cycle=?,last_transition=?,
                   current_goal=?,sleep_reason=?,updated_at=? WHERE machine_id=?""",
                (target,cycle,now,goal.strip(),reason.strip() if target=="SLEEPING" else "",now,machine_id))
            self.conn.commit()
            return self.get(machine_id)

    def add_dream_artifact(self, machine_id, division_slug, artifact_type, title, summary, artifact=None):
        if artifact_type not in DREAM_TYPES:
            raise ValueError("unsupported dream artifact type")
        if not isinstance(title,str) or not 1 <= len(title.strip()) <= 100:
            raise ValueError("title must be 1-100 characters")
        if not isinstance(summary,str) or not 1 <= len(summary.strip()) <= 1000:
            raise ValueError("summary must be 1-1000 characters")
        artifact = {} if artifact is None else artifact
        encoded = json.dumps(artifact,separators=(",",":"),ensure_ascii=False)
        if not isinstance(artifact,dict) or len(encoded.encode("utf-8")) > 8192:
            raise ValueError("dream artifact must be a JSON object under 8 KiB")
        with self.lock:
            state = self.get(machine_id)
            if not state or state["mode"] != "DREAMING":
                raise ValueError("dream artifacts can only be submitted while DREAMING")
            cur = self.conn.execute(
                """INSERT INTO dream_artifacts
                   (machine_id,division_slug,cycle,artifact_type,title,summary,artifact,created_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (machine_id,division_slug,state["cycle"],artifact_type,title.strip(),
                 summary.strip(),encoded,_now()))
            self.conn.commit()
            return {"id":cur.lastrowid,"machine_id":machine_id,"division":division_slug,
                    "cycle":state["cycle"],"artifact_type":artifact_type,"title":title.strip(),
                    "summary":summary.strip(),"status":"AWAITING_REVIEW"}

    def artifacts(self, status="AWAITING_REVIEW", limit=100):
        limit=max(1,min(int(limit),300))
        with self.lock:
            rows=self.conn.execute(
                """SELECT id,machine_id,division_slug,cycle,artifact_type,title,summary,
                          artifact,status,created_at FROM dream_artifacts
                   WHERE status=? ORDER BY id DESC LIMIT ?""",(status,limit)).fetchall()
            return [{**dict(row),"artifact":json.loads(row["artifact"])} for row in rows]

    def review_artifact(self, artifact_id, decision, reviewer="owner"):
        if decision not in {"APPROVED", "REJECTED"}:
            raise ValueError("decision must be APPROVED or REJECTED")
        with self.lock:
            row = self.conn.execute(
                "SELECT id,status,machine_id,division_slug,title FROM dream_artifacts WHERE id=?",
                (int(artifact_id),)).fetchone()
            if not row:
                raise LookupError("dream artifact not found")
            if row["status"] != "AWAITING_REVIEW":
                raise ValueError("dream artifact has already been reviewed")
            now = _now()
            cur = self.conn.execute(
                "UPDATE dream_artifacts SET status=? WHERE id=? AND status='AWAITING_REVIEW'",
                (decision, int(artifact_id)))
            if cur.rowcount != 1:
                raise ValueError("dream artifact review conflict")
            self.conn.commit()
            return {"id": row["id"], "status": decision, "machine_id": row["machine_id"],
                    "division": row["division_slug"], "title": row["title"],
                    "reviewed_at": now, "reviewer": str(reviewer)[:80],
                    "promotion": "NOT_PERFORMED"}

    def snapshot(self):
        with self.lock:
            rows=self.conn.execute(
                "SELECT mode,COUNT(*) AS count FROM agent_lifecycle GROUP BY mode").fetchall()
            counts={r["mode"]:r["count"] for r in rows}
            agents=self.conn.execute(
                "SELECT * FROM agent_lifecycle ORDER BY machine_id").fetchall()
            return {"mode":"PERSISTENT_LIFECYCLE_COORDINATION_ONLY",
                    "counts":counts,"agents":[dict(r) for r in agents],
                    "dream_artifacts_pending_review":self.conn.execute(
                        "SELECT COUNT(*) FROM dream_artifacts WHERE status='AWAITING_REVIEW'").fetchone()[0],
                    "dream_execution_enabled":False}
