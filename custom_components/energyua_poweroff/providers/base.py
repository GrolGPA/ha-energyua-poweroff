"""Base class and shared helpers for power outage data providers."""
from __future__ import annotations

import re
import logging
from abc import ABC, abstractmethod
from datetime import date, datetime, tzinfo

import requests
import urllib3
from bs4 import BeautifulSoup

from ..schedule import Outage, parse_time_range

_LOGGER = logging.getLogger(__name__)

MONTHS_UA = {
    "січня": 1, "лютого": 2, "березня": 3, "квітня": 4,
    "травня": 5, "червня": 6, "липня": 7, "серпня": 8,
    "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12,
}

_TITLE_DATE_RE = re.compile(
    r"(\d{1,2})\s+(" + "|".join(MONTHS_UA) + r")", re.IGNORECASE
)

_TIME_RANGE = r"\d{1,2}:\d{2}\s*[–\-]\s*\d{1,2}:\d{2}"


class BaseProvider(ABC):
    """Abstract base class for power outage data providers.

    Data contract — get_poweroff_schedule() must return a list of Outage
    (see schedule.py): timezone-aware (start, end) datetimes. Use
    _build_outages() to create them from "YYYY-MM-DD" + "HH:MM-HH:MM".
    """

    # --- subclasses MUST override these ---
    key: str = ""               # unique provider id, e.g. "zoe"
    name: str = ""              # human-readable, e.g. "Запоріжжяобленерго"
    default_base_url: str = ""  # e.g. "https://www.zoe.com.ua"

    def __init__(
        self,
        base_url: str,
        group: str,
        verify_ssl: bool = False,
        time_zone: tzinfo | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.group = group
        self.verify_ssl = verify_ssl
        self.time_zone = time_zone or datetime.now().astimezone().tzinfo
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    @abstractmethod
    def get_poweroff_schedule(self) -> list[Outage]:
        """Fetch and return the power-off schedule."""

    # --- shared helpers ---

    def _today(self) -> date:
        return datetime.now(self.time_zone).date()

    def _build_outages(self, day: str, hours_list: list[str]) -> list[Outage]:
        """Create Outages for *day*; malformed ranges are logged and skipped."""
        outages: list[Outage] = []
        for hours in hours_list:
            try:
                outages.append(parse_time_range(day, hours, self.time_zone))
            except ValueError as exc:
                _LOGGER.warning(
                    "Пропущено некоректний запис %s %s: %s", day, hours, exc
                )
        return outages

    def _fetch_soup(self, url: str) -> BeautifulSoup:
        """GET *url* and return a BeautifulSoup tree."""
        response = requests.get(url, timeout=15, verify=self.verify_ssl)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    @staticmethod
    def _resolve_date(
        day: int, month: int, year: int | None = None, today: date | None = None
    ) -> str | None:
        """Build 'YYYY-MM-DD'; a missing year is the one closest to *today*.

        This keeps '1 СІЧНЯ' in a December schedule in the next year (and the
        opposite in January). Returns None for impossible dates.
        """
        today = today or date.today()
        candidates = [year] if year is not None else [
            today.year - 1, today.year, today.year + 1
        ]

        best: date | None = None
        for candidate in candidates:
            try:
                resolved = date(candidate, month, day)
            except ValueError:
                continue
            if best is None or abs((resolved - today).days) < abs((best - today).days):
                best = resolved
        return best.isoformat() if best else None

    @classmethod
    def _extract_date_from_title(
        cls, title: str, today: date | None = None
    ) -> str | None:
        """Extract 'YYYY-MM-DD' from a Ukrainian title like '7 БЕРЕЗНЯ'."""
        match = _TITLE_DATE_RE.search(title)
        if not match:
            return None
        month = MONTHS_UA[match.group(2).lower()]
        return cls._resolve_date(int(match.group(1)), month, today=today)

    @staticmethod
    def _extract_hours_for_group(content: str, group: str) -> list[str]:
        """Find outage hours for *group* inside *content*.

        Handles formats like:
            1.2: 09:00 – 14:00
            3.1: 00:00 – 00:30, 07:30 – 11:00
        Every occurrence of the group is collected; the lookbehind prevents
        '1.2' from matching inside '11.2' or '2.1.2'.
        Returns a list of unique normalised "HH:MM-HH:MM" strings.
        """
        pattern = (
            rf"(?<![\d.]){re.escape(group)}:\s*"
            rf"({_TIME_RANGE}(?:,\s*{_TIME_RANGE})*)"
        )

        result: list[str] = []
        for match in re.finditer(pattern, content):
            for raw_range in match.group(1).split(","):
                normalised = re.sub(r"\s*[–\-]\s*", "-", raw_range.strip())
                if normalised not in result:
                    result.append(normalised)
        return result

    def _parse_articles(self, articles) -> list[Outage]:
        """Parse blog-style <article> blocks: a date title + 'group: hours' lines.

        Only the first article for each date is used (newest first on the site).
        """
        outages: list[Outage] = []
        seen_dates: set[str] = set()
        today = self._today()

        for article in articles:
            title_el = article.find(["h2", "h3", "h1"])
            if not title_el:
                continue

            day = self._extract_date_from_title(title_el.get_text(), today=today)
            if not day or day in seen_dates:
                continue
            seen_dates.add(day)

            # "\n" keeps text of adjacent tags apart
            content = article.get_text("\n")
            hours_list = self._extract_hours_for_group(content, self.group)
            outages.extend(self._build_outages(day, hours_list))

        return outages
