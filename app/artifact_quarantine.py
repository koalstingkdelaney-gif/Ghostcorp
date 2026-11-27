"""Bounded, non-executing quarantine for artifacts produced in agent workspaces.

Artifacts are copied into a private directory, hashed and classified by a small
built-in content inspector. Nothing is extracted, rendered, executed, promoted,
or described as malware-free. A real malware scanner is not configured here.
"""
import hashlib
import json
import os
import re
import secrets
import sqlite3
import stat
import threading
import time
from pathlib import Path

from .workload_governance import WorkloadPolicyError, validate_artifact_name

_WORKSPACE_ID = re.compile(r"^ws_[a-f0-9]{32}$")
_ARTIFACT_ID = "gca_"
_DEFAULT_MAX_BYTES = 1_048_576
_ALLOWED_TEXT = {".txt", ".md", ".csv", ".log", ".json"}
_SCRIPT_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".sh", ".bash", ".bat", ".cmd", ".ps1", ".html", ".htm"}
_ARCHIVE_MAGICS = (b"PK\\x03\\x04", b"PK\\x05\\x06", b"PK\\x07\\x08",
                   b"\\x1f\\x8b", b"7z\\xbc\\xaf\\x27\\x1c", b"Rar!\\x1a\\x07")


class ArtifactPolicyError(ValueError):
    """An artifact or filesystem path violates quarantine policy."""


class ArtifactQuarantineUnavailable(RuntimeError):
    """Quarantine is not configured or its prerequisites are unavailable."""


def _inspect_bytes(data, artifact_name):
    """Classify content without parsing archives or executing/rendering it."""
    suffix = Path(artifact_name).suffix.lower()
    flags = ["malware_scanner_not_configured"]
    if data.startswith((b"\\x7fELF", b"MZ")) or data.startswith(b"#!") or suffix in _SCRIPT_SUFFIXES:
        detected = "EXECUTABLE_OR_SCRIPT"
        flags.append("executable_or_script_content")
    elif data.startswith(_ARCHIVE_MAGICS) or (len(data) > 262 and data[257:262] == b"ustar"):
        detected = "ARCHIVE"
        flags.append("archive_not_extracted")
    elif data.startswith(b"%PDF-"):
        detected = "PDF_DOCUMENT"
        flags.append("binary_document_not_scanned")
    elif data.startswith(b"\\x89PNG\\r\\n\\x1a\\n") or data.startswith(b"\\xff\\xd8\\xff") or data.startswith((b"GIF87a", b"GIF89a")) or (data.startswith(b"RIFF") and data[8:12] == b"WEBP"):
        detected = "IMAGE"
        flags.append("binary_image_not_scanned")
    else:
        try:
            text = data.decode("utf-8")
            if "\\x00" in text:
                raise UnicodeDecodeError("utf-8", data, 0, 1, "NUL byte")
        except UnicodeDecodeError:
            detected = "UNKNOWN_BINARY"
            flags.append("unknown_binary_format")
        else:
            if suffix == ".json":
                try:
                    json.loads(text)
                    detected = "JSON_TEXT"
                except (ValueError, TypeError):
                    detected = "TEXT_UNTYPED"
                    flags.append("malformed_json")
            elif suffix in _ALLOWED_TEXT:
                detected = "TEXT"
            else:
                detected = "TEXT_UNTYPED"
                flags.append("unrecognized_text_extension")
    return {"detected_type": detected, "risk_flags": flags,
            "review_required": True, "automatic_release": False}


class ArtifactQuarantine:
    """Copy bounded regular files from active workspaces into private quarantine."""

    def __init__(self, db_path, workspace_root=None, quarantine_root=None,
                 clock=None, max_bytes=_DEFAULT_MAX_BYTES):
        if not isinstance(max_bytes, int) or not 1 <= max_bytes <= 10_485_760:
            raise ValueError("artifact size limit must be between 1 byte and 10 MiB")
        self.workspace_root = Path(workspace_root).expanduser().absolute() if workspace_root else None
        self.quarantine_root = Path(quarantine_root).expanduser().absolute() if quarantine_root else None
        self.clock = clock or time.time
        self.max_bytes = max_bytes
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=10)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=10000")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS quarantined_artifacts (
            artifact_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            artifact_name TEXT NOT NULL,
            stored_name TEXT NOT NULL UNIQUE,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            detected_type TEXT NOT NULL,
            risk_flags TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )""")
        self.conn.commit()

    def status(self):
        configured = bool(self.workspace_root and self.quarantine_root)
        return {
            "enabled": configured,
            "workspace_root_configured": bool(self.workspace_root),
            "quarantine_root_configured": bool(self.quarantine_root),
            "max_file_bytes": self.max_bytes,
            "malware_scanner": "NOT_CONFIGURED",
            "automatic_extraction": False,
            "automatic_execution": False,
            "automatic_release": False,
            "note": "Quarantined files remain private and pending review; built-in inspection is not antivirus scanning.",
        }

    @staticmethod
    def _directory_flags():
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise ArtifactQuarantineUnavailable("safe no-follow directory operations are unavailable on this host")
        return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW

    def _open_directory(self, path, create=False):
        if path is None:
            raise ArtifactQuarantineUnavailable("workspace and quarantine roots must both be configured")
        if create:
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            info = path.lstat()
        except FileNotFoundError as exc:
            raise ArtifactQuarantineUnavailable("configured directory does not exist") from exc
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise ArtifactPolicyError("configured root must be a real directory")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise ArtifactPolicyError("configured root permissions must be private (0700 or stricter)")
        try:
            return os.open(str(path), self._directory_flags())
        except OSError as exc:
            raise ArtifactPolicyError("configured root could not be opened without following links") from exc

    def _open_workspace_file(self, workspace_id, artifact_name):
        if not isinstance(workspace_id, str) or not _WORKSPACE_ID.fullmatch(workspace_id):
            raise ArtifactPolicyError("invalid workspace identity")
        if not isinstance(artifact_name, str) or artifact_name.startswith("/") or artifact_name.endswith("/") or "//" in artifact_name or any(part in {"", ".", ".."} for part in artifact_name.split("/")):
            raise ArtifactPolicyError("artifact path must be a strict relative path")
        try:
            safe_name = validate_artifact_name(artifact_name)
        except WorkloadPolicyError as exc:
            raise ArtifactPolicyError(str(exc)) from exc

        with self._lock:
            try:
                row = self.conn.execute(
                    "SELECT agent_id,status,expires_at FROM agent_workspaces WHERE workspace_id=?",
                    (workspace_id,),
                ).fetchone()
            except sqlite3.OperationalError as exc:
                raise ArtifactQuarantineUnavailable("agent workspace registry is not initialized") from exc
        if not row:
            raise LookupError("workspace not found")
        if row["status"] != "ACTIVE" or int(row["expires_at"]) <= int(self.clock()):
            raise ArtifactPolicyError("workspace is not active")

        root_fd = self._open_directory(self.workspace_root)
        opened_dirs = [root_fd]
        source_fd = None
        try:
            workspace_fd = os.open(workspace_id, self._directory_flags(), dir_fd=root_fd)
            opened_dirs.append(workspace_fd)
            workspace_info = os.fstat(workspace_fd)
            if stat.S_IMODE(workspace_info.st_mode) & 0o077:
                raise ArtifactPolicyError("workspace permissions are not private")
            marker_fd = os.open(".ghostcorp-workspace", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=workspace_fd)
            try:
                marker_info = os.fstat(marker_fd)
                if not stat.S_ISREG(marker_info.st_mode) or os.read(marker_fd, 128).decode("utf-8", "replace") != workspace_id:
                    raise ArtifactPolicyError("workspace ownership marker is missing or invalid")
            finally:
                os.close(marker_fd)

            parts = safe_name.split("/")
            parent_fd = workspace_fd
            for part in parts[:-1]:
                next_fd = os.open(part, self._directory_flags(), dir_fd=parent_fd)
                opened_dirs.append(next_fd)
                parent_fd = next_fd
            source_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
            info = os.fstat(source_fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ArtifactPolicyError("artifact must be a single-link regular file")
            if info.st_size < 1 or info.st_size > self.max_bytes:
                raise ArtifactPolicyError("artifact is empty or exceeds the configured size limit")
            return source_fd, dict(row), info
        except FileNotFoundError as exc:
            if source_fd is not None:
                os.close(source_fd)
            raise LookupError("artifact or workspace path not found") from exc
        except OSError as exc:
            if source_fd is not None:
                os.close(source_fd)
            raise ArtifactPolicyError("artifact path contains a link or cannot be opened safely") from exc
        except Exception:
            if source_fd is not None:
                os.close(source_fd)
            raise
        finally:
            for fd in reversed(opened_dirs):
                os.close(fd)

    def quarantine(self, workspace_id, artifact_name):
        source_fd, workspace, before = self._open_workspace_file(workspace_id, artifact_name)
        try:
            quarantine_fd = self._open_directory(self.quarantine_root, create=True)
        except Exception:
            os.close(source_fd)
            raise
        artifact_id = _ARTIFACT_ID + secrets.token_hex(16)
        stored_name = artifact_id + ".bin"
        destination_fd = None
        created = False
        try:
            destination_fd = os.open(
                stored_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600, dir_fd=quarantine_fd,
            )
            created = True
            digest = hashlib.sha256()
            chunks = []
            total = 0
            while True:
                chunk = os.read(source_fd, 65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > self.max_bytes:
                    raise ArtifactPolicyError("artifact grew beyond the configured size limit")
                digest.update(chunk)
                chunks.append(chunk)
                view = memoryview(chunk)
                while view:
                    written = os.write(destination_fd, view)
                    if written <= 0:
                        raise OSError("quarantine write made no progress")
                    view = view[written:]
            after = os.fstat(source_fd)
            if total < 1 or after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns or total != before.st_size:
                raise ArtifactPolicyError("artifact changed while it was being quarantined")
            os.fsync(destination_fd)
            inspected = _inspect_bytes(b"".join(chunks), artifact_name)
            now = int(self.clock())
            record = {
                "artifact_id": artifact_id,
                "workspace_id": workspace_id,
                "agent_id": workspace["agent_id"],
                "artifact_name": artifact_name,
                "sha256": digest.hexdigest(),
                "size_bytes": total,
                **inspected,
                "status": "QUARANTINED",
                "created_at": now,
            }
            with self._lock:
                self.conn.execute("BEGIN IMMEDIATE")
                try:
                    self.conn.execute(
                        """INSERT INTO quarantined_artifacts
                        (artifact_id,workspace_id,agent_id,artifact_name,stored_name,sha256,
                         size_bytes,detected_type,risk_flags,status,created_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (artifact_id, workspace_id, workspace["agent_id"], artifact_name,
                         stored_name, record["sha256"], total, inspected["detected_type"],
                         json.dumps(inspected["risk_flags"]), "QUARANTINED", now),
                    )
                    self.conn.commit()
                except Exception:
                    self.conn.rollback()
                    raise
            return record
        except Exception:
            if created:
                try:
                    os.unlink(stored_name, dir_fd=quarantine_fd)
                except OSError:
                    pass
            raise
        finally:
            if destination_fd is not None:
                os.close(destination_fd)
            os.close(quarantine_fd)
            os.close(source_fd)

    def list(self, limit=100):
        if not isinstance(limit, int):
            raise ValueError("limit must be an integer")
        limit = max(1, min(limit, 500))
        with self._lock:
            rows = self.conn.execute(
                """SELECT artifact_id,workspace_id,agent_id,artifact_name,sha256,size_bytes,
                          detected_type,risk_flags,status,created_at
                   FROM quarantined_artifacts ORDER BY created_at DESC,artifact_id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["risk_flags"] = json.loads(item["risk_flags"])
            item["review_required"] = True
            item["automatic_release"] = False
            result.append(item)
        return result
