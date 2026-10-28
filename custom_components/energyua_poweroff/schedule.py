"""Pure helpers for turning provider schedule records into datetime ranges."""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, tzinfo

_HOURS_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$")

DateRange = tuple[datetime, datetime]


def parse_time_range(day: str, hours: str, tz: tzinfo) -> DateRange:
    """Convert 'YYYY-MM-DD' + 'HH:MM-HH:MM' into aware (start, end) datetimes.

    The end may be '24:00' (midnight of the next day). A range whose end is not
    after its start is treated as crossing midnight.
    Raises ValueError for malformed input.
    """
    match = _HOURS_RE.match(hours)
    if not match:
        raise ValueError(f"Invalid hours range: {hours!r}")
    start_h, start_m, end_h, end_m = (int(g) for g in match.groups())

    if start_h > 23 or start_m > 59 or end_m > 59:
        raise ValueError(f"Invalid hours range: {hours!r}")
    if end_h > 24 or (end_h == 24 and end_m != 0):
        raise ValueError(f"Invalid hours range: {hours!r}")

    day_date = date.fromisoformat(day)
    start = datetime.combine(day_date, time(start_h, start_m), tzinfo=tz)

    if end_h == 24:
        end = datetime.combine(day_date + timedelta(days=1), time(0, 0), tzinfo=tz)
    else:
        end = datetime.combine(day_date, time(end_h, end_m), tzinfo=tz)
        if end <= start:
            end += timedelta(days=1)

    return start, end


def merge_ranges(ranges: list[DateRange]) -> list[DateRange]:
    """Sort ranges and merge those that overlap or touch each other."""
    merged: list[DateRange] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
