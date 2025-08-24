from datetime import date, timedelta
from pathlib import Path

from yc_matcher.infrastructure.persistence.sqlite_quota import SQLiteDailyWeeklyQuota, _iso_week


def test_iso_week_format():
    assert _iso_week(date(2025, 1, 6)).endswith("W02")  # Monday of week 2


def test_daily_quota_increments_until_limit(tmp_path: Path):
    db = tmp_path / "quota.sqlite"
    day = date(2025, 1, 7)
    q = SQLiteDailyWeeklyQuota(db_path=db, today=lambda: day)
    assert q.check_and_increment_daily(2) is True
    assert q.check_and_increment_daily(2) is True
    assert q.check_and_increment_daily(2) is False


def test_weekly_quota_across_days(tmp_path: Path):
    db = tmp_path / "quota.sqlite"
    start = date(2025, 1, 6)  # Monday
    q = SQLiteDailyWeeklyQuota(db_path=db, today=lambda: start)
    # 3 sends this week allowed up to 3
    assert q.check_and_increment_weekly(3) is True
    assert q.check_and_increment_weekly(3) is True
    # Advance day within same week
    q.today = lambda: start + timedelta(days=2)
    assert q.check_and_increment_weekly(3) is True
    # Over limit
    assert q.check_and_increment_weekly(3) is False
