import sqlite3
from pathlib import Path

from scripts.backup_db import integrity_check, snapshot_sqlite


def test_snapshot_sqlite_is_consistent_and_readable(tmp_path: Path):
    source = tmp_path / "source.db"
    snapshot = tmp_path / "snapshot.db"
    con = sqlite3.connect(source)
    con.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT)")
    con.execute("INSERT INTO notes(body) VALUES ('checkpoint')")
    con.commit()
    con.close()

    snapshot_sqlite(source, snapshot)
    integrity_check(snapshot)
    restored = sqlite3.connect(snapshot)
    try:
        assert restored.execute("SELECT body FROM notes").fetchone()[0] == "checkpoint"
    finally:
        restored.close()
