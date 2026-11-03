"""Provider for energy-ua.info sites (Прикарпаттяобленерго, Львівобленерго, etc.).

These sites use the URL pattern /{cherga|grupa}/{N-M} (group "N.M"); the path
segment differs per region. They render a simple HTML table with columns:
day | hours.
"""
from __future__ import annotations

import re
from datetime import date

import requests

from ..schedule import Outage
from .base import BaseProvider

# e.g. prykarpattya uses /cherga/, dnipro uses /grupa/
PATH_SEGMENTS = ("cherga", "grupa")


class EnergyUAProvider(BaseProvider):
    """Scrapes {subdomain}.energy-ua.info/{cherga|grupa}/{N-M} — HTML table format."""

    key = "energy_ua"
    name = "Energy-UA (energy-ua.info)"
    default_base_url = "https://prykarpattya.energy-ua.info"

    _path_segment: str | None = None

    def get_poweroff_schedule(self) -> list[Outage]:
        url, soup = self._fetch_group_page()

        # ---- strategy 1: HTML table ----
        table = soup.find("table")
        if table:
            return self._parse_table(table)

        # ---- strategy 2: blog-style articles (same as ZOE) ----
        articles = soup.find_all("article")
        if articles:
            return self._parse_articles(articles)

        raise ValueError(
            f"Не знайдено таблицю чи записи на сторінці {url}"
        )

    def _fetch_group_page(self):
        """Fetch the group page, remembering which path segment the region uses."""
        slug = self.group.replace(".", "-")
        segments = (
            [self._path_segment] if self._path_segment else list(PATH_SEGMENTS)
        )
        last_exc: requests.HTTPError | None = None
        for segment in segments:
            url = f"{self.base_url}/{segment}/{slug}"
            try:
                soup = self._fetch_soup(url)
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status not in (403, 404):
                    raise
                last_exc = exc
                continue
            self._path_segment = segment
            return url, soup
        assert last_exc is not None
        raise last_exc

    # ------------------------------------------------------------------
    def _parse_table(self, table) -> list[Outage]:
        """Parse a <table> with rows [day, hours, …]."""
        rows = table.find_all("tr")
        outages: list[Outage] = []
        today = self._today()

        for row in rows[1:]:  # skip header
            cols = [col.get_text(strip=True) for col in row.find_all("td")]
            if len(cols) < 2:
                continue

            day_raw = cols[0].strip()
            hours_raw = cols[1].strip()

            # Normalise date if it looks like a Ukrainian date string
            day = self._extract_date_from_title(day_raw, today=today)
            if not day:
                # Already in YYYY-MM-DD or DD.MM.YYYY?
                day = self._normalise_date(day_raw, today=today)
            if not day:
                continue

            # Split multiple ranges separated by commas
            outages.extend(self._build_outages(day, self._split_hours(hours_raw)))

        return outages

    # ------------------------------------------------------------------
    @classmethod
    def _normalise_date(cls, raw: str, today: date | None = None) -> str | None:
        """Try to convert DD.MM.YYYY or DD.MM to YYYY-MM-DD."""
        m = re.match(r"(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?$", raw.strip())
        if not m:
            return None
        year = int(m.group(3)) if m.group(3) else None
        return cls._resolve_date(int(m.group(1)), int(m.group(2)), year, today)

    @staticmethod
    def _split_hours(raw: str) -> list[str]:
        """Split '08:00–12:00, 18:00–22:00' into normalised ranges."""
        ranges = [r.strip() for r in raw.split(",")]
        result: list[str] = []
        for r in ranges:
            normalised = re.sub(r"\s*[–\-]\s*", "-", r)
            if re.match(r"\d{1,2}:\d{2}-\d{1,2}:\d{2}$", normalised):
                result.append(normalised)
        return result
