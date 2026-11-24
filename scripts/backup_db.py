#!/usr/bin/env python3
"""Create a consistent, encrypted SQLite backup. Never writes plaintext into Git."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def integrity_check(db_path: Path) -> None:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        result = con.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"SQLite integrity check failed: {result}")
    finally:
        con.close()


def snapshot_sqlite(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Database not found: {source}")
    src = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
    dst = sqlite3.connect(str(destination))
    try:
        src.backup(dst)
        dst.commit()
    finally:
        dst.close()
        src.close()
    integrity_check(destination)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_backup(source: Path, backup_dir: Path, recipient: str, keep: int = 3) -> Path:
    age = shutil.which("age")
    if not age:
        raise RuntimeError("The age encryption utility is required; no plaintext backup was retained.")
    if not recipient.strip():
        raise RuntimeError("Set AGE_RECIPIENT to an owner-controlled age public recipient.")
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = backup_dir / f"agency-{stamp}.sqlite.age"

    with tempfile.TemporaryDirectory(prefix="ghostcorp-backup-") as temp:
        plain = Path(temp) / "snapshot.sqlite"
        roundtrip = Path(temp) / "verified.sqlite"
        encrypted = Path(temp) / "snapshot.sqlite.age"
        snapshot_sqlite(source, plain)

        subprocess.run(
            [age, "-r", recipient.strip(), "-o", str(encrypted), str(plain)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [age, "-d", "-o", str(roundtrip), str(encrypted)],
            check=True,
            capture_output=True,
            text=True,
        )
        integrity_check(roundtrip)
        if sha256(plain) != sha256(roundtrip):
            raise RuntimeError("Encrypted backup verification mismatch; refusing to publish backup.")
        shutil.copyfile(encrypted, output)

    manifest = {
        "created_at": stamp,
        "file": output.name,
        "encrypted_bytes": output.stat().st_size,
        "sha256": sha256(output),
        "encryption": "age recipient encryption",
        "restore_verified": True,
    }
    (backup_dir / f"{output.name}.json").write_text(json.dumps(manifest, indent=2) + "\n")
    backups = sorted(backup_dir.glob("agency-*.sqlite.age"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[keep:]:
        old.unlink(missing_ok=True)
        old.with_name(old.name + ".json").unlink(missing_ok=True)
    return output


def main() -> int:
    source = Path(os.environ.get("AGENCY_DB_PATH", "data/agency.db"))
    backup_dir = Path(os.environ.get("BACKUP_DIR", "backups"))
    recipient = os.environ.get("AGE_RECIPIENT", "")
    try:
        result = create_backup(source, backup_dir, recipient)
        print(json.dumps({"status": "verified_encrypted_backup", "path": str(result), "sha256": sha256(result)}))
        return 0
    except Exception as exc:
        print(f"BACKUP FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
