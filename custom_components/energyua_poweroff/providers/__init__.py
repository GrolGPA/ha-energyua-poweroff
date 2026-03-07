"""Provider plugin system for Energy-UA Power Off."""
from __future__ import annotations

import re
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import requests
import urllib3
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MONTHS_UA = {
    "січня": 1, "лютого": 2, "березня": 3, "квітня": 4,
    "травня": 5, "червня": 6, "липня": 7, "серпня": 8,
    "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12,
}


class BaseProvider(ABC):
    """Abstract base class for power outage data providers.

    Data contract — get_poweroff_schedule() must return:
        list[dict] where each dict is:
        {
            "day":   "YYYY-MM-DD",      # str, date of outage
            "hours": "HH:MM-HH:MM",     # str, single time range
        }
    """

    # --- subclasses MUST override these ---
    key: str = ""               # unique provider id, e.g. "zoe"
    name: str = ""              # human-readable, e.g. "Запоріжжяобленерго"
    default_base_url: str = ""  # e.g. "https://www.zoe.com.ua"

    def __init__(self, base_url: str, group: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.group = group

    @abstractmethod
    def get_poweroff_schedule(self) -> list[dict[str, str]]:
        """Fetch and return the power-off schedule."""

    # --- shared helpers ---

    def _fetch_soup(self, url: str) -> BeautifulSoup:
        """GET *url* and return a BeautifulSoup tree."""
        response = requests.get(url, timeout=15, verify=False)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    @staticmethod
    def _extract_date_from_title(title: str) -> str | None:
        """Extract 'YYYY-MM-DD' from a Ukrainian title like '7 БЕРЕЗНЯ'."""
        match = re.search(
            r"(\d{1,2})\s+"
            r"(СІЧНЯ|ЛЮТОГО|БЕРЕЗНЯ|КВІТНЯ|ТРАВНЯ|ЧЕРВНЯ|"
            r"ЛИПНЯ|СЕРПНЯ|ВЕРЕСНЯ|ЖОВТНЯ|ЛИСТОПАДА|ГРУДНЯ)",
            title,
            re.IGNORECASE,
        )
        if not match:
            return None
        day = int(match.group(1))
        month = MONTHS_UA.get(match.group(2).lower())
        if not month:
            return None
        year = datetime.now().year
        return f"{year}-{month:02d}-{day:02d}"

    @staticmethod
    def _extract_hours_for_group(content: str, group: str) -> list[str]:
        """Find outage hours for *group* inside *content*.

        Handles formats like:
            1.2: 09:00 – 14:00
            3.1: 00:00 – 00:30, 07:30 – 11:00
        Returns a list of normalised "HH:MM-HH:MM" strings.
        """
        escaped = re.escape(group)
        pattern = (
            rf"{escaped}:\s*"
            rf"(\d{{1,2}}:\d{{2}}\s*[–\-]\s*\d{{1,2}}:\d{{2}}"
            rf"(?:,\s*\d{{1,2}}:\d{{2}}\s*[–\-]\s*\d{{1,2}}:\d{{2}})*)"
        )
        match = re.search(pattern, content)
        if not match:
            return []

        raw = match.group(1)
        ranges = [r.strip() for r in raw.split(",")]
        return [re.sub(r"\s*[–\-]\s*", "-", r) for r in ranges]


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------
# Lazy-import concrete providers to avoid circular imports.
# Each provider module registers itself by being listed here.

def _load_providers() -> dict[str, type[BaseProvider]]:
    from .zoe import ZOEProvider
    from .energy_ua import EnergyUAProvider

    providers: dict[str, type[BaseProvider]] = {}
    for cls in (ZOEProvider, EnergyUAProvider):
        providers[cls.key] = cls
    return providers


_PROVIDERS: dict[str, type[BaseProvider]] | None = None


def get_providers() -> dict[str, type[BaseProvider]]:
    """Return the provider registry (loaded once)."""
    global _PROVIDERS  # noqa: PLW0603
    if _PROVIDERS is None:
        _PROVIDERS = _load_providers()
    return _PROVIDERS


def get_provider(key: str) -> type[BaseProvider]:
    """Return a provider class by its key."""
    providers = get_providers()
    if key not in providers:
        raise KeyError(f"Unknown provider: {key!r}. Available: {list(providers)}")
    return providers[key]
