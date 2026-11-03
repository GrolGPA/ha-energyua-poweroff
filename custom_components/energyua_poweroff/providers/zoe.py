"""Provider for Запоріжжяобленерго (www.zoe.com.ua)."""
from __future__ import annotations

from ..schedule import Outage
from .base import BaseProvider


class ZOEProvider(BaseProvider):
    """Scrapes zoe.com.ua/outage/ — blog-style articles with queue data."""

    key = "zoe"
    name = "Запоріжжяобленерго (zoe.com.ua)"
    default_base_url = "https://www.zoe.com.ua"

    def get_poweroff_schedule(self) -> list[Outage]:
        soup = self._fetch_soup(f"{self.base_url}/outage/")

        articles = soup.find_all("article")
        if not articles:
            raise ValueError("Не знайдено записів на сторінці")

        return self._parse_articles(articles)
