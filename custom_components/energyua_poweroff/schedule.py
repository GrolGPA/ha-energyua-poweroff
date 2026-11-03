"""Pure helpers for turning provider schedule records into datetime ranges."""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, tzinfo
from typing import NamedTuple

_HOURS_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$")


class Outage(NamedTuple):
    """A single power outage as a pair of timezone-aware datetimes."""

    start: datetime
    end: datetime

    @property
    def day(self) -> str:
        return self.start.date().isoformat()

    @property
    def hours(self) -> str:
        """'HH:MM-HH:MM'; an end at the next midnight is shown as '24:00'."""
        end = f"{self.end:%H:%M}"
        if self.end.date() > self.start.date() and end == "00:00":
            end = "24:00"
        return f"{self.start:%H:%M}-{end}"

    def as_dict(self) -> dict[str, str]:
        return {
            "day": self.day,
            "hours": self.hours,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }


def parse_time_range(day: str, hours: str, tz: tzinfo) -> Outage:
    """Convert 'YYYY-MM-DD' + 'HH:MM-HH:MM' into an aware Outage.

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

    return Outage(start, end)


def merge_ranges(outages: list[Outage]) -> list[Outage]:
    """Sort outages and merge those that overlap or touch each other."""
    merged: list[Outage] = []
    for start, end in sorted(outages):
        if merged and start <= merged[-1].end:
            merged[-1] = Outage(merged[-1].start, max(merged[-1].end, end))
        else:
            merged.append(Outage(start, end))
    return merged
