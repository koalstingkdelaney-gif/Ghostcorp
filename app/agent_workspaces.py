"""Owner-gated, per-agent temporary workspace allocation.

This module allocates empty directories only. It does not execute workloads,
mount contributor files, or provide a security boundary against the host.
"""
import re
import secrets
import shutil
import sqlite3
import threading
import time
from pathlib import Path

_AGENT = re.compile(r"^[A-Za-z0-9_-]{3,80}$")
_WORKSPACE = re.compile(r"^ws_[a-f0-9]{32}$")


class WorkspacePolicyError(ValueError):
    pass


class AgentWorkspaceManager:
    def __init__(self, db_path, root=None, clock=None):
        self.root = Path(root).expanduser().absolute() if root else None
        self.clock = clock or time.time
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=10)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=10000")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS agent_workspaces (
            workspace_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL,
            status TEXT NOT NULL, created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL)""")
        self.conn.commit()

    def status(self):
        return {"enabled": bool(self.root), "root_configured": bool(self.root),
                "mode": "directory-allocation-only",
                "note": "No code execution, artifact ingestion, or host isolation is provided."}

    def _require_root(self):
        if self.root is None:
            raise WorkspacePolicyError("workspace root is not configured")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.is_symlink() or not self.root.is_dir():
            raise WorkspacePolicyError("workspace root must be a real directory")
        return self.root

    def create(self, agent_id, ttl_seconds=3600):
        if not isinstance(agent_id, str) or not _AGENT.fullmatch(agent_id):
            raise WorkspacePolicyError("invalid agent identity")
        if not isinstance(ttl_seconds, int) or not 60 <= ttl_seconds <= 86400:
            raise WorkspacePolicyError("workspace lifetime must be between 60 and 86400 seconds")
        root = self._require_root()
        with self._lock:
            workspace_id = "ws_" + secrets.token_hex(16)
            path = root / workspace_id
            path.mkdir(mode=0o700)
            marker = path / ".ghostcorp-workspace"
            marker.write_text(workspace_id, encoding="utf-8")
            now = int(self.clock())
            try:
                self.conn.execute(
                    "INSERT INTO agent_workspaces VALUES(?,?, 'ACTIVE', ?, ?)",
                    (workspace_id, agent_id, now, now + ttl_seconds))
                self.conn.commit()
            except Exception:
                shutil.rmtree(path)
                raise
        return {"workspace_id": workspace_id, "agent_id": agent_id,
                "status": "ACTIVE", "expires_at": now + ttl_seconds,
                "path": str(path), "execution_enabled": False}

    def list(self, agent_id=None):
        query = "SELECT workspace_id,agent_id,status,created_at,expires_at FROM agent_workspaces"
        args = ()
        if agent_id is not None:
            if not isinstance(agent_id, str) or not _AGENT.fullmatch(agent_id):
                raise WorkspacePolicyError("invalid agent identity")
            query += " WHERE agent_id=?"
            args = (agent_id,)
        query += " ORDER BY created_at DESC LIMIT 500"
        return [dict(row) for row in self.conn.execute(query, args).fetchall()]

    def release(self, workspace_id):
        if not isinstance(workspace_id, str) or not _WORKSPACE.fullmatch(workspace_id):
            raise WorkspacePolicyError("invalid workspace identity")
        root = self._require_root()
        with self._lock:
            row = self.conn.execute(
                "SELECT * FROM agent_workspaces WHERE workspace_id=?", (workspace_id,)
            ).fetchone()
            if not row:
                raise LookupError("workspace not found")
            path = root / workspace_id
            if path.parent != root or path.is_symlink():
                raise WorkspacePolicyError("workspace path failed safety validation")
            marker = path / ".ghostcorp-workspace"
            if path.exists():
                if not marker.is_file() or marker.is_symlink() or marker.read_text(encoding="utf-8") != workspace_id:
                    raise WorkspacePolicyError("workspace ownership marker is missing or invalid")
                shutil.rmtree(path)
            self.conn.execute(
                "UPDATE agent_workspaces SET status='RELEASED' WHERE workspace_id=?",
                (workspace_id,))
            self.conn.commit()
            return {"workspace_id": workspace_id, "status": "RELEASED"}

    def cleanup_expired(self, limit=100):
        now = int(self.clock())
        rows = self.conn.execute(
            "SELECT workspace_id FROM agent_workspaces WHERE status='ACTIVE' AND expires_at<=? "
            "ORDER BY expires_at LIMIT ?", (now, max(1, min(int(limit), 500)))).fetchall()
        results = []
        for row in rows:
            try:
                results.append(self.release(row["workspace_id"]))
            except (LookupError, WorkspacePolicyError, OSError):
                results.append({"workspace_id": row["workspace_id"], "status": "CLEANUP_BLOCKED"})
        return results
