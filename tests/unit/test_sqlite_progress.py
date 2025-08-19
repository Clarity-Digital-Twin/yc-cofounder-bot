from pathlib import Path

from yc_matcher.infrastructure.sqlite_progress import SQLiteProgressRepo


def test_progress_repo_roundtrip(tmp_path: Path):
    db = tmp_path / "progress.sqlite"
    repo = SQLiteProgressRepo(db)
    assert repo.get_last() is None
    repo.set_last("abc123")
    assert repo.get_last() == "abc123"
    repo.set_last("def456")
    assert repo.get_last() == "def456"

