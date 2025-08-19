from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS progress (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  cursor TEXT
);
"""


class SQLiteProgressRepo:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as con:
            con.executescript(SCHEMA)
            con.commit()

    def get_last(self) -> str | None:
        with sqlite3.connect(self.db_path) as con:
            cur = con.execute("SELECT cursor FROM progress WHERE id=1")
            row = cur.fetchone()
            return row[0] if row and row[0] else None

    def set_last(self, ident: str) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "INSERT INTO progress(id, cursor) VALUES(1, ?) ON CONFLICT(id) DO UPDATE SET cursor=excluded.cursor",
                (ident,),
            )
            con.commit()

