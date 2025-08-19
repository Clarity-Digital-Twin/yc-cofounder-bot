from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS quota_daily (
  day TEXT PRIMARY KEY,
  count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS quota_weekly (
  week TEXT PRIMARY KEY,
  count INTEGER NOT NULL
);
"""


def _iso_week(d: date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


@dataclass
class SQLiteDailyWeeklyQuota:
    db_path: Path
    today: Callable[[], date] | None = None

    def __post_init__(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as con:
            con.executescript(SCHEMA)
            con.commit()

    def _today(self) -> date:
        return self.today() if self.today is not None else date.today()

    def check_and_increment(self, limit: int) -> bool:
        # default daily behavior
        return self.check_and_increment_daily(limit)

    def check_and_increment_daily(self, daily_limit: int) -> bool:
        d = self._today().isoformat()
        with sqlite3.connect(self.db_path) as con:
            cur = con.execute("SELECT count FROM quota_daily WHERE day=?", (d,))
            row = cur.fetchone()
            count = int(row[0]) if row else 0
            if count >= daily_limit:
                return False
            new = count + 1
            con.execute(
                "INSERT INTO quota_daily(day,count) VALUES(?,?) ON CONFLICT(day) DO UPDATE SET count=excluded.count",
                (d, new),
            )
            con.commit()
            return True

    def check_and_increment_weekly(self, weekly_limit: int) -> bool:
        w = _iso_week(self._today())
        with sqlite3.connect(self.db_path) as con:
            cur = con.execute("SELECT count FROM quota_weekly WHERE week=?", (w,))
            row = cur.fetchone()
            count = int(row[0]) if row else 0
            if count >= weekly_limit:
                return False
            new = count + 1
            con.execute(
                "INSERT INTO quota_weekly(week,count) VALUES(?,?) ON CONFLICT(week) DO UPDATE SET count=excluded.count",
                (w, new),
            )
            con.commit()
            return True
