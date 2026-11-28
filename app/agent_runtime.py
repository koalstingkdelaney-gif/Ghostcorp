"""Durable, division-scoped agent task queue.

This is queue infrastructure, not an AI model or always-on worker. Claims are
serialized with BEGIN IMMEDIATE so concurrent workers cannot receive the same
task. Expired leases are retried up to a bounded attempt count, then dead-lettered.
"""
import hashlib
import json
import secrets
import sqlite3
import time
import threading
from pathlib import Path


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _synchronized(method):
    def wrapped(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapped


class AgentRuntime:
    def __init__(self, db_path, max_attempts=5, max_payload_bytes=65536):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS agent_tasks (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          task_key TEXT NOT NULL UNIQUE,
          division_slug TEXT NOT NULL,
          required_role TEXT NOT NULL DEFAULT '',
          task_type TEXT NOT NULL,
          payload TEXT NOT NULL DEFAULT '{}',
          status TEXT NOT NULL DEFAULT 'queued',
          claimed_by TEXT NOT NULL DEFAULT '',
          lease_token_hash TEXT NOT NULL DEFAULT '',
          lease_until INTEGER NOT NULL DEFAULT 0,
          result TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          attempt_count INTEGER NOT NULL DEFAULT 0,
          max_attempts INTEGER NOT NULL DEFAULT 5,
          last_error TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_agent_tasks_ready
          ON agent_tasks(division_slug,status,id);
        """)
        columns = {r["name"] for r in self.conn.execute("PRAGMA table_info(agent_tasks)")}
        for name, declaration in (
            ("attempt_count", "INTEGER NOT NULL DEFAULT 0"),
            ("max_attempts", "INTEGER NOT NULL DEFAULT 5"),
            ("last_error", "TEXT NOT NULL DEFAULT ''"),
        ):
            if name not in columns:
                self.conn.execute(f"ALTER TABLE agent_tasks ADD COLUMN {name} {declaration}")
        self.conn.commit()
        self.max_attempts = max(1, min(int(max_attempts), 20))
        self.max_payload_bytes = max(1024, min(int(max_payload_bytes), 262144))

    @_synchronized
    def authenticate(self, token):
        digest = hashlib.sha256(token.encode()).hexdigest()
        row = self.conn.execute(
            "SELECT machine_id,division_slug,role,status FROM machine_agents WHERE token_hash=?",
            (digest,)
        ).fetchone()
        if not row or row["status"] != "PROVISIONED":
            return None
        return dict(row)

    @_synchronized
    def enqueue(self, key, division, role, task_type, payload):
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        if len(encoded.encode("utf-8")) > self.max_payload_bytes:
            raise ValueError("task payload exceeds configured size limit")
        try:
            self.conn.execute(
              """INSERT INTO agent_tasks(task_key,division_slug,required_role,task_type,
                 payload,created_at,updated_at,max_attempts) VALUES(?,?,?,?,?,?,?,?)""",
              (key,division,role,task_type,encoded,_now(),_now(),self.max_attempts)
            )
            self.conn.commit()
            return "queued"
        except sqlite3.IntegrityError:
            return "duplicate"

    @_synchronized
    def claim(self, agent, lease_seconds=300):
        lease_seconds = max(30, min(int(lease_seconds), 3600))
        # Sleeping agents cannot claim normal business work.
        has_lifecycle = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='agent_lifecycle'"
        ).fetchone()
        if has_lifecycle:
            lifecycle = self.conn.execute(
                "SELECT mode FROM agent_lifecycle WHERE machine_id=?",
                (agent["machine_id"],)
            ).fetchone()
            # Missing lifecycle state is not permission: agents must register
            # and explicitly enter WORKING before claiming business tasks.
            if not lifecycle or lifecycle["mode"] != "WORKING":
                return None
        now = int(time.time())
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            expired = self.conn.execute(
                """SELECT id,attempt_count,max_attempts FROM agent_tasks
                   WHERE status='claimed' AND lease_until<?""", (now,)
            ).fetchall()
            for row in expired:
                next_status = "dead_letter" if row["attempt_count"] >= row["max_attempts"] else "queued"
                self.conn.execute(
                    """UPDATE agent_tasks SET status=?,claimed_by='',lease_token_hash='',
                       lease_until=0,updated_at=? WHERE id=? AND status='claimed'""",
                    (next_status,_now(),row["id"])
                )
            row = self.conn.execute(
              """SELECT * FROM agent_tasks WHERE division_slug=? AND status='queued'
                 AND (required_role='' OR required_role=?) ORDER BY id LIMIT 1""",
              (agent["division_slug"],agent["role"])
            ).fetchone()
            if not row:
                self.conn.commit()
                return None
            lease = secrets.token_urlsafe(32)
            cur = self.conn.execute(
              """UPDATE agent_tasks SET status='claimed',claimed_by=?,lease_token_hash=?,
                 lease_until=?,attempt_count=attempt_count+1,updated_at=?
                 WHERE id=? AND status='queued'""",
              (agent["machine_id"],hashlib.sha256(lease.encode()).hexdigest(),
               now+lease_seconds,_now(),row["id"])
            )
            if cur.rowcount != 1:
                self.conn.rollback()
                return None
            self.conn.commit()
            return {"task_id":row["id"],"task_key":row["task_key"],
                    "division":row["division_slug"],"task_type":row["task_type"],
                    "payload":json.loads(row["payload"]),"lease_token":lease,
                    "lease_expires_at":now+lease_seconds,
                    "attempt":row["attempt_count"]+1,
                    "max_attempts":row["max_attempts"]}
        except Exception:
            self.conn.rollback()
            raise

    @_synchronized
    def complete(self, agent, task_id, lease_token, result):
        encoded = json.dumps(result, separators=(",", ":"), ensure_ascii=False)
        if len(encoded.encode("utf-8")) > self.max_payload_bytes:
            raise ValueError("task result exceeds configured size limit")
        digest=hashlib.sha256(lease_token.encode()).hexdigest()
        cur=self.conn.execute(
          """UPDATE agent_tasks SET status='completed',result=?,updated_at=?
             WHERE id=? AND division_slug=? AND claimed_by=? AND lease_token_hash=?
             AND status='claimed' AND lease_until>=?""",
          (encoded,_now(),task_id,agent["division_slug"],
           agent["machine_id"],digest,int(time.time()))
        )
        self.conn.commit()
        return cur.rowcount == 1

    @_synchronized
    def status(self):
        rows=self.conn.execute(
          "SELECT status,COUNT(*) AS count FROM agent_tasks GROUP BY status"
        ).fetchall()
        counts={r["status"]:r["count"] for r in rows}
        return {"mode":"DURABLE_QUEUE_NO_WORKERS_CONFIGURED",
                "counts":counts,"tasks_total":sum(counts.values()),
                "max_attempts":self.max_attempts,
                "payload_limit_bytes":self.max_payload_bytes}
