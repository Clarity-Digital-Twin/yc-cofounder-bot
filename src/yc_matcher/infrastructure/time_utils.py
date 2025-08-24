"""Centralized timezone utilities for consistent timestamp handling.

Professional teams always:
1. Store timestamps in UTC (for consistency)
2. Convert to local time only for display
3. Use timezone-aware datetime objects
4. Have a single source of truth for time operations

This module ensures all timestamps in the codebase are handled consistently.
"""

from datetime import UTC, datetime, timedelta


def utc_now() -> datetime:
    """Get current time in UTC with timezone info.

    Returns:
        datetime: Current UTC time with tzinfo=UTC
    """
    return datetime.now(UTC)


def utc_timestamp() -> float:
    """Get current Unix timestamp (seconds since epoch).

    Returns:
        float: Unix timestamp
    """
    return utc_now().timestamp()


def utc_isoformat() -> str:
    """Get current UTC time as ISO 8601 string.

    Returns:
        str: ISO format string like '2025-08-24T04:00:00.000000+00:00'
    """
    return utc_now().isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to timezone-aware datetime.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        datetime: Timezone-aware datetime object

    Raises:
        ValueError: If timestamp format is invalid
    """
    # Handle both 'Z' suffix and '+00:00' for UTC
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str[:-1] + '+00:00'

    # Parse ISO format
    dt = datetime.fromisoformat(timestamp_str)

    # If no timezone, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    return dt


def is_within_hours(timestamp: datetime, hours: float = 1.0) -> bool:
    """Check if timestamp is within the last N hours.

    Args:
        timestamp: Timezone-aware datetime to check
        hours: Number of hours to look back (default 1)

    Returns:
        bool: True if timestamp is within the time window
    """
    # Ensure timestamp is timezone-aware
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    cutoff = utc_now() - timedelta(hours=hours)
    return timestamp > cutoff


def format_for_display(timestamp: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp for UI display.

    Args:
        timestamp: Datetime to format
        format: strftime format string

    Returns:
        str: Formatted timestamp string
    """
    # Could convert to local time here if needed
    # For now, we'll display UTC with indicator
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    return timestamp.strftime(format) + " UTC"


def unix_to_datetime(unix_ts: float) -> datetime:
    """Convert Unix timestamp to UTC datetime.

    Args:
        unix_ts: Unix timestamp (seconds since epoch)

    Returns:
        datetime: UTC datetime with timezone info
    """
    return datetime.fromtimestamp(unix_ts, tz=UTC)


def local_to_utc(local_dt: datetime) -> datetime:
    """Convert local/naive datetime to UTC.

    Args:
        local_dt: Local or naive datetime

    Returns:
        datetime: UTC datetime with timezone info
    """
    if local_dt.tzinfo is None:
        # Assume it's local time, convert to UTC
        # This is a simplification - in production you'd use pytz or zoneinfo
        import time
        offset = time.timezone if not time.daylight else time.altzone
        utc_dt = local_dt + timedelta(seconds=offset)
        return utc_dt.replace(tzinfo=UTC)
    else:
        # Already has timezone, convert to UTC
        return local_dt.astimezone(UTC)
