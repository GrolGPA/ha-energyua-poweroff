"""Provider plugin system for Energy-UA Power Off."""
from __future__ import annotations

import re
import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import requests
import urllib3
from bs4 import BeautifulSoup

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

    def __init__(self, base_url: str, group: str, verify_ssl: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.group = group
        self.verify_ssl = verify_ssl
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    @abstractmethod
    def get_poweroff_schedule(self) -> list[dict[str, str]]:
        """Fetch and return the power-off schedule."""

    # --- shared helpers ---

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
