from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_profiles (
  profile_hash TEXT PRIMARY KEY,
  first_seen_ts REAL
);
"""


class SQLiteSeenRepo:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure()

    def _ensure(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as con:
            con.execute(SCHEMA)
            con.commit()

    def is_seen(self, profile_hash: str) -> bool:
        with sqlite3.connect(self.db_path) as con:
            cur = con.execute("SELECT 1 FROM seen_profiles WHERE profile_hash=?", (profile_hash,))
            return cur.fetchone() is not None

    def mark_seen(self, profile_hash: str) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "INSERT OR IGNORE INTO seen_profiles(profile_hash, first_seen_ts) VALUES (?, strftime('%s','now'))",
                (profile_hash,),
            )
            con.commit()
