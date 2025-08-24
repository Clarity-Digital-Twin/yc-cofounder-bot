"""Unit tests for time_utils module."""

from datetime import datetime, timezone
from unittest.mock import patch

UTC = timezone.utc  # Python 3.10 compatibility

from yc_matcher.infrastructure.utils.time_utils import (
    format_for_display,
    is_within_hours,
    parse_timestamp,
    unix_to_datetime,
)


class TestTimeUtils:
    """Test time utility functions."""

    def test_parse_timestamp_with_unix_timestamp(self) -> None:
        """Test parsing Unix timestamp."""
        # Unix timestamp for 2024-01-15 10:30:00 UTC
        timestamp = 1705318200
        result = parse_timestamp(timestamp)

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_timestamp_with_iso_string(self) -> None:
        """Test parsing ISO format string."""
        timestamp = "2024-01-15T10:30:00Z"
        result = parse_timestamp(timestamp)

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_timestamp_with_datetime(self) -> None:
        """Test passing datetime object directly."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = parse_timestamp(dt)

        assert result == dt

    def test_parse_timestamp_invalid_input(self) -> None:
        """Test handling invalid timestamp input."""
        # Invalid string
        result = parse_timestamp("not-a-date")
        assert result is None

        # Invalid type
        result = parse_timestamp({"key": "value"})
        assert result is None

    def test_unix_to_datetime(self) -> None:
        """Test converting Unix timestamp to datetime."""
        # Unix timestamp for 2024-01-15 10:30:00 UTC
        timestamp = 1705318200
        result = unix_to_datetime(timestamp)

        assert isinstance(result, datetime)
        assert result.tzinfo == UTC
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_format_for_display(self) -> None:
        """Test formatting datetime for display."""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)

        # Test default format
        result = format_for_display(dt)
        assert "10:30:45" in result

        # Test custom format
        result = format_for_display(dt, fmt="%Y-%m-%d")
        assert result == "2024-01-15"

    def test_format_for_display_none_input(self) -> None:
        """Test formatting None datetime."""
        result = format_for_display(None)
        assert result == "N/A"

    def test_is_within_hours(self) -> None:
        """Test checking if datetime is within hours."""
        # Mock current time as 2024-01-15 12:00:00 UTC
        mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        with patch("yc_matcher.infrastructure.utils.time_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromisoformat = datetime.fromisoformat

            # 30 minutes ago - should be within 1 hour
            recent_dt = datetime(2024, 1, 15, 11, 30, 0, tzinfo=UTC)
            assert is_within_hours(recent_dt, hours=1) is True

            # 2 hours ago - should not be within 1 hour
            old_dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
            assert is_within_hours(old_dt, hours=1) is False

            # 2 hours ago - should be within 3 hours
            assert is_within_hours(old_dt, hours=3) is True

    def test_is_within_hours_none_input(self) -> None:
        """Test is_within_hours with None input."""
        assert is_within_hours(None) is False

    def test_is_within_hours_naive_datetime(self) -> None:
        """Test is_within_hours with naive datetime."""
        # Naive datetime (no timezone)
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)

        # Should handle gracefully
        result = is_within_hours(naive_dt)
        assert isinstance(result, bool)
