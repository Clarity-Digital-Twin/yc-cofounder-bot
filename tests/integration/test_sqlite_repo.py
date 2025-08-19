from pathlib import Path

from yc_matcher.infrastructure.sqlite_repo import SQLiteSeenRepo


def test_sqlite_seen_repo_roundtrip(tmp_path: Path):
    db = tmp_path / "seen.sqlite3"
    repo = SQLiteSeenRepo(db)
    ph = "abc123"
    assert repo.is_seen(ph) is False
    repo.mark_seen(ph)
    assert repo.is_seen(ph) is True
