"""Provider for energy-ua.info sites (Прикарпаттяобленерго, Львівобленерго, etc.).

These sites use the URL pattern /{cherga}/{group} and render a simple HTML table
with columns: day | hours.
"""
from __future__ import annotations

import logging

from . import BaseProvider

_LOGGER = logging.getLogger(__name__)


class EnergyUAProvider(BaseProvider):
    """Scrapes {subdomain}.energy-ua.info/cherga/{group} — HTML table format."""

    key = "energy_ua"
    name = "Energy-UA (energy-ua.info)"
    default_base_url = "https://prykarpattya.energy-ua.info"

    def get_poweroff_schedule(self) -> list[dict[str, str]]:
        url = f"{self.base_url}/cherga/{self.group}"
        soup = self._fetch_soup(url)

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

    # ------------------------------------------------------------------
    def _parse_table(self, table) -> list[dict[str, str]]:
        """Parse a <table> with rows [day, hours, …]."""
        rows = table.find_all("tr")
        data: list[dict[str, str]] = []

        for row in rows[1:]:  # skip header
            cols = [col.get_text(strip=True) for col in row.find_all("td")]
            if len(cols) < 2:
                continue

            day_raw = cols[0].strip()
            hours_raw = cols[1].strip()

            # Normalise date if it looks like a Ukrainian date string
            date_str = self._extract_date_from_title(day_raw)
            if not date_str:
                # Already in YYYY-MM-DD or DD.MM.YYYY?
                date_str = self._normalise_date(day_raw)
            if not date_str:
                continue

            # Split multiple ranges separated by commas
            for hours in self._split_hours(hours_raw):
                data.append({"day": date_str, "hours": hours})

        return data

    def _parse_articles(self, articles) -> list[dict[str, str]]:
        """Fallback: parse <article> blocks with embedded queue data."""
        data: list[dict[str, str]] = []
        seen_dates: set[str] = set()

        for article in articles:
            title_el = article.find(["h2", "h3", "h1"])
            if not title_el:
                continue

            date_str = self._extract_date_from_title(title_el.get_text())
            if not date_str or date_str in seen_dates:
                continue
            seen_dates.add(date_str)

            content = article.get_text()
            hours_list = self._extract_hours_for_group(content, self.group)

            for hours in hours_list:
                data.append({"day": date_str, "hours": hours})

        return data

    # ------------------------------------------------------------------
    @staticmethod
    def _normalise_date(raw: str) -> str | None:
        """Try to convert DD.MM.YYYY or DD.MM to YYYY-MM-DD."""
        import re
        from datetime import datetime

        m = re.match(r"(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?$", raw.strip())
        if not m:
            return None
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else datetime.now().year
        return f"{year}-{month:02d}-{day:02d}"

    @staticmethod
    def _split_hours(raw: str) -> list[str]:
        """Split '08:00–12:00, 18:00–22:00' into normalised ranges."""
        import re

        ranges = [r.strip() for r in raw.split(",")]
        result: list[str] = []
        for r in ranges:
            normalised = re.sub(r"\s*[–\-]\s*", "-", r)
            if re.match(r"\d{1,2}:\d{2}-\d{1,2}:\d{2}$", normalised):
                result.append(normalised)
        return result
