"""Provider for Запоріжжяобленерго (www.zoe.com.ua)."""
from __future__ import annotations

import logging

from . import BaseProvider

_LOGGER = logging.getLogger(__name__)


class ZOEProvider(BaseProvider):
    """Scrapes zoe.com.ua/outage/ — blog-style articles with queue data."""

    key = "zoe"
    name = "Запоріжжяобленерго (zoe.com.ua)"
    default_base_url = "https://www.zoe.com.ua"

    def get_poweroff_schedule(self) -> list[dict[str, str]]:
        url = f"{self.base_url}/outage/"
        soup = self._fetch_soup(url)

        articles = soup.find_all("article")
        if not articles:
            raise ValueError("Не знайдено записів на сторінці")

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
