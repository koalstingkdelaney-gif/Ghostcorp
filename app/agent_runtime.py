"""Durable, division-scoped agent task queue.

This is a real queue primitive, not an AI model or always-on worker. Agents
authenticate with provisioned machine tokens; tasks cannot cross divisions.
"""
import hashlib
import json
import secrets
import sqlite3
import time
from pathlib import Path


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class AgentRuntime:
    def __init__(self, db_path):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
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
          updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_agent_tasks_ready
          ON agent_tasks(division_slug,status,id);
        """)
        self.conn.commit()

    def authenticate(self, token):
        digest = hashlib.sha256(token.encode()).hexdigest()
        row = self.conn.execute(
          "SELECT machine_id,division_slug,role,status FROM machine_agents WHERE token_hash=?",
          (digest,)
        ).fetchone()
        if not row or row["status"] != "PROVISIONED":
            return None
        return dict(row)

    def enqueue(self, key, division, role, task_type, payload):
        try:
            self.conn.execute(
              """INSERT INTO agent_tasks(task_key,division_slug,required_role,task_type,
                 payload,created_at,updated_at) VALUES(?,?,?,?,?,?,?)""",
              (key,division,role,task_type,json.dumps(payload),_now(),_now())
            )
            self.conn.commit()
            return "queued"
        except sqlite3.IntegrityError:
            return "duplicate"

    def claim(self, agent, lease_seconds=300):
        now=int(time.time())
        self.conn.execute(
          """UPDATE agent_tasks SET status='queued',claimed_by='',lease_token_hash='',
             lease_until=0,updated_at=? WHERE status='claimed' AND lease_until<?""",
          (_now(),now)
        )
        row=self.conn.execute(
          """SELECT * FROM agent_tasks WHERE division_slug=? AND status='queued'
             AND (required_role='' OR required_role=?) ORDER BY id LIMIT 1""",
          (agent["division_slug"],agent["role"])
        ).fetchone()
        if not row:
            self.conn.commit()
            return None
        lease=secrets.token_urlsafe(32)
        self.conn.execute(
          """UPDATE agent_tasks SET status='claimed',claimed_by=?,lease_token_hash=?,
             lease_until=?,updated_at=? WHERE id=? AND status='queued'""",
          (agent["machine_id"],hashlib.sha256(lease.encode()).hexdigest(),
           now+lease_seconds,_now(),row["id"])
        )
        self.conn.commit()
        return {"task_id":row["id"],"task_key":row["task_key"],
                "division":row["division_slug"],"task_type":row["task_type"],
                "payload":json.loads(row["payload"]),"lease_token":lease,
                "lease_expires_at":now+lease_seconds}

    def complete(self, agent, task_id, lease_token, result):
        digest=hashlib.sha256(lease_token.encode()).hexdigest()
        cur=self.conn.execute(
          """UPDATE agent_tasks SET status='completed',result=?,updated_at=?
             WHERE id=? AND division_slug=? AND claimed_by=? AND lease_token_hash=?
             AND status='claimed' AND lease_until>=?""",
          (json.dumps(result),_now(),task_id,agent["division_slug"],
           agent["machine_id"],digest,int(time.time()))
        )
        self.conn.commit()
        return cur.rowcount == 1

    def status(self):
        rows=self.conn.execute(
          "SELECT status,COUNT(*) AS count FROM agent_tasks GROUP BY status"
        ).fetchall()
        return {"mode":"DURABLE_QUEUE_NO_WORKERS_CONFIGURED",
                "counts":{r["status"]:r["count"] for r in rows},
                "tasks_total":sum(r["count"] for r in rows)}
