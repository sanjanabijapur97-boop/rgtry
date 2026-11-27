"""UTC datetime and ISO 8601 formatting/parsing utilities."""

import re
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
DATE_ONLY_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def utc_now() -> datetime:
    """Return current timezone-aware UTC datetime (second precision)."""
    return datetime.now(timezone.utc).replace(microsecond=0)


def to_utc_iso(dt: datetime) -> str:
    """Format a datetime in UTC ISO 8601 with trailing Z."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_iso() -> str:
    """Return current UTC timestamp formatted as ISO 8601."""
    return to_utc_iso(utc_now())


def parse_deadline_to_utc_iso(raw_value: str) -> str:
    """Parse an ISO 8601 date or datetime into a UTC ISO 8601 string.

    Date-only inputs (YYYY-MM-DD) close at 23:59:00 Asia/Kolkata and are converted to UTC.
    """
    cleaned = raw_value.strip()
    if DATE_ONLY_REGEX.match(cleaned):
        parsed_date = date.fromisoformat(cleaned)
        ist_dt = datetime.combine(parsed_date, time(23, 59, 0), tzinfo=IST)
        return to_utc_iso(ist_dt)

    if "T" not in cleaned and "t" not in cleaned and " " not in cleaned:
        raise ValueError("Invalid ISO 8601 date or datetime format.")

    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return to_utc_iso(dt)
