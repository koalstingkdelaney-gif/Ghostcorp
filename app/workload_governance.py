"""Signed, allowlisted workload authorization and per-agent quotas.

This module authorizes only fixed public workloads. It does not execute code,
download packages, dispatch contributor jobs, or grant filesystem access.
"""
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
import threading
from pathlib import PurePosixPath

PROFILES = {
    "public-build-test": {"cpu_cores": 1, "memory_mb": 512, "timeout_seconds": 600,
                          "network": "none", "artifact_limit_bytes": 1048576},
    "synthetic-benchmark": {"cpu_cores": 1, "memory_mb": 256, "timeout_seconds": 120,
                            "network": "none", "artifact_limit_bytes": 262144},
}
_AGENT = re.compile(r"^[A-Za-z0-9_-]{3,80}$")
_SHA = re.compile(r"^[a-f0-9]{40}$")


class WorkloadPolicyError(ValueError):
    pass


class WorkloadAuthority:
    def __init__(self, signing_key=None, clock=None):
        self.signing_key = signing_key
        self.clock = clock or time.time

    def issue(self, workload_type, agent_id, source_revision, ttl_seconds=900):
        if not self.signing_key or len(self.signing_key.encode()) < 32:
            raise WorkloadPolicyError("workload signing key is not configured with at least 32 characters")
        if workload_type not in PROFILES:
            raise WorkloadPolicyError("workload type is not allowlisted")
        if not isinstance(agent_id, str) or not _AGENT.fullmatch(agent_id):
            raise WorkloadPolicyError("invalid agent identity")
        if not isinstance(source_revision, str) or not _SHA.fullmatch(source_revision):
            raise WorkloadPolicyError("source revision must be a full 40-character commit SHA")
        if not isinstance(ttl_seconds, int) or not 60 <= ttl_seconds <= 3600:
            raise WorkloadPolicyError("manifest lifetime must be between 60 and 3600 seconds")
        now = int(self.clock())
        body = {
            "schema": "ghostcorp-workload-v1",
            "workload_id": "gcw_" + secrets.token_urlsafe(12),
            "workload_type": workload_type,
            "agent_id": agent_id,
            "source_revision": source_revision,
            "profile": PROFILES[workload_type],
            "issued_at": now,
            "expires_at": now + ttl_seconds,
            "nonce": secrets.token_urlsafe(18),
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        signature = hmac.new(self.signing_key.encode(), canonical, hashlib.sha256).hexdigest()
        return {**body, "signature": signature}

    def verify(self, manifest):
        if not self.signing_key or len(self.signing_key.encode()) < 32:
            raise WorkloadPolicyError("workload signing key is not configured")
        if not isinstance(manifest, dict):
            return False
        signature = manifest.get("signature")
        body = {k: v for k, v in manifest.items() if k != "signature"}
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        expected = hmac.new(self.signing_key.encode(), canonical, hashlib.sha256).hexdigest()
        if not isinstance(signature, str) or not hmac.compare_digest(signature, expected):
            return False
        now = int(self.clock())
        return (body.get("schema") == "ghostcorp-workload-v1"
                and isinstance(body.get("issued_at"), int)
                and isinstance(body.get("expires_at"), int)
                and body["issued_at"] <= now + 30
                and now <= body["expires_at"]
                and body.get("workload_type") in PROFILES
                and body.get("profile") == PROFILES.get(body.get("workload_type")))


class QuotaLedger:
    """SQLite-backed reservation ledger; no execution is performed here."""
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=10)
        self.conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self.conn.execute("PRAGMA busy_timeout=10000")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS workload_quota_events (
            reservation_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL,
            task_key TEXT NOT NULL, reserved_seconds INTEGER NOT NULL,
            actual_seconds INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL, created_at INTEGER NOT NULL,
            settled_at INTEGER, UNIQUE(agent_id, task_key))""")
        self.conn.commit()

    def reserve(self, agent_id, task_key, seconds, max_active=1, daily_seconds=1800):
        if not isinstance(agent_id, str) or not _AGENT.fullmatch(agent_id):
            raise WorkloadPolicyError("invalid agent identity")
        if not isinstance(task_key, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{3,120}", task_key):
            raise WorkloadPolicyError("invalid idempotency key")
        if not isinstance(seconds, int) or not 1 <= seconds <= 600:
            raise WorkloadPolicyError("reservation must be between 1 and 600 seconds")
        now = int(self._now())
        with self._lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                prior = self.conn.execute(
                    "SELECT * FROM workload_quota_events WHERE agent_id=? AND task_key=?",
                    (agent_id, task_key)).fetchone()
                if prior:
                    self.conn.commit()
                    return {**dict(prior), "outcome": "EXISTING"}
                active = self.conn.execute(
                    "SELECT COUNT(*) FROM workload_quota_events WHERE agent_id=? AND status='RESERVED'",
                    (agent_id,)).fetchone()[0]
                used = self.conn.execute(
                    "SELECT COALESCE(SUM(CASE WHEN status='SETTLED' THEN actual_seconds ELSE reserved_seconds END),0) "
                    "FROM workload_quota_events WHERE agent_id=? AND created_at>=?",
                    (agent_id, now - 86400)).fetchone()[0]
                if active >= max_active:
                    raise WorkloadPolicyError("agent concurrent-workload quota reached")
                if used + seconds > daily_seconds:
                    raise WorkloadPolicyError("agent daily execution-time quota reached")
                reservation_id = "gcr_" + secrets.token_urlsafe(12)
                self.conn.execute(
                    "INSERT INTO workload_quota_events VALUES(?,?,?,?,0,'RESERVED',?,NULL)",
                    (reservation_id, agent_id, task_key, seconds, now))
                self.conn.commit()
                return {"reservation_id": reservation_id, "agent_id": agent_id,
                        "task_key": task_key, "reserved_seconds": seconds,
                        "status": "RESERVED", "outcome": "CREATED"}
            except Exception:
                self.conn.rollback()
                raise

    def settle(self, reservation_id, actual_seconds):
        if not isinstance(actual_seconds, int) or not 0 <= actual_seconds <= 600:
            raise WorkloadPolicyError("actual execution time must be between 0 and 600 seconds")
        with self._lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                row = self.conn.execute(
                    "SELECT * FROM workload_quota_events WHERE reservation_id=?",
                    (reservation_id,)).fetchone()
                if not row:
                    raise LookupError("reservation not found")
                if row["status"] != "RESERVED":
                    raise WorkloadPolicyError("reservation is already settled")
                if actual_seconds > row["reserved_seconds"]:
                    raise WorkloadPolicyError("actual time cannot exceed the reserved limit")
                self.conn.execute(
                    "UPDATE workload_quota_events SET actual_seconds=?,status='SETTLED',settled_at=? "
                    "WHERE reservation_id=?", (actual_seconds, int(self._now()), reservation_id))
                self.conn.commit()
                return {"reservation_id": reservation_id, "status": "SETTLED",
                        "actual_seconds": actual_seconds}
            except Exception:
                self.conn.rollback()
                raise

    def status(self, agent_id):
        rows = self.conn.execute(
            "SELECT status,COUNT(*) AS count,COALESCE(SUM(CASE WHEN status='SETTLED' "
            "THEN actual_seconds ELSE reserved_seconds END),0) AS seconds "
            "FROM workload_quota_events WHERE agent_id=? AND created_at>=? GROUP BY status",
            (agent_id, int(self._now()) - 86400)).fetchall()
        return {"agent_id": agent_id, "window": "rolling_24_hours",
                "events": [dict(row) for row in rows],
                "default_daily_seconds": 1800, "default_concurrent_reservations": 1}

    def _now(self):
        return time.time()


def validate_artifact_name(name):
    """Reject traversal, absolute paths, hidden paths, and platform separators."""
    if not isinstance(name, str) or not name or len(name) > 180 or "\x00" in name:
        raise WorkloadPolicyError("invalid artifact name")
    if "\\" in name:
        raise WorkloadPolicyError("artifact names must use POSIX separators")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise WorkloadPolicyError("artifact path must be a safe relative path")
    if any(part.startswith(".") for part in path.parts):
        raise WorkloadPolicyError("hidden artifact paths are not accepted")
    return path.as_posix()
