from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
import requests
from bs4 import BeautifulSoup

from custom_components.energyua_poweroff.providers.energy_ua import EnergyUAProvider
from custom_components.energyua_poweroff.providers.zoe import ZOEProvider

ARTICLES_HTML = (
    "<article><h2>7 БЕРЕЗНЯ</h2>"
    "<p>11.2: 01:00 – 03:00</p><p>1.2: 09:00 – 14:00, 22:00 – 24:00</p></article>"
    "<article><h2>7 БЕРЕЗНЯ</h2><p>1.2: 01:00 – 02:00</p></article>"
)


def _fetch(html):
    return patch(
        "custom_components.energyua_poweroff.providers.BaseProvider._fetch_soup",
        return_value=BeautifulSoup(html, "html.parser"),
    )


def test_zoe_adjacent_paragraphs_do_not_leak_between_groups():
    with _fetch(ARTICLES_HTML):
        schedule = ZOEProvider("https://example.com", "1.2").get_poweroff_schedule()

    assert [outage.hours for outage in schedule] == ["09:00-14:00", "22:00-24:00"]
    assert len({outage.day for outage in schedule}) == 1


def test_energy_ua_article_fallback():
    with _fetch(ARTICLES_HTML):
        schedule = EnergyUAProvider(
            "https://example.com", "1.2"
        ).get_poweroff_schedule()

    assert [outage.hours for outage in schedule] == ["09:00-14:00", "22:00-24:00"]


def test_energy_ua_url_uses_dash_separated_queue():
    with _fetch(ARTICLES_HTML) as fetch:
        EnergyUAProvider("https://example.com", "6.2").get_poweroff_schedule()

    fetch.assert_called_once_with("https://example.com/cherga/6-2")


def test_energy_ua_falls_back_to_grupa_path():
    forbidden = requests.Response()
    forbidden.status_code = 403
    soup = BeautifulSoup(ARTICLES_HTML, "html.parser")
    with patch(
        "custom_components.energyua_poweroff.providers.BaseProvider._fetch_soup",
        side_effect=[requests.HTTPError(response=forbidden), soup, soup],
    ) as fetch:
        provider = EnergyUAProvider("https://example.com", "6.2")
        provider.get_poweroff_schedule()
        provider.get_poweroff_schedule()

    assert [c.args[0] for c in fetch.call_args_list] == [
        "https://example.com/cherga/6-2",
        "https://example.com/grupa/6-2",
        "https://example.com/grupa/6-2",
    ]


def test_energy_ua_table():
    html = (
        "<table><tr><th>День</th><th>Години</th></tr>"
        "<tr><td>07.03.2026</td><td>08:00–12:00, 18:00–24:00</td></tr></table>"
    )
    with _fetch(html):
        schedule = EnergyUAProvider(
            "https://example.com", "1.2"
        ).get_poweroff_schedule()

    assert [(o.day, o.hours) for o in schedule] == [
        ("2026-03-07", "08:00-12:00"),
        ("2026-03-07", "18:00-24:00"),
    ]


def test_invalid_range_is_skipped():
    html = (
        "<table><tr><th>День</th><th>Години</th></tr>"
        "<tr><td>07.03.2026</td><td>08:00–12:00, 25:00–26:00</td></tr></table>"
    )
    with _fetch(html):
        schedule = EnergyUAProvider(
            "https://example.com", "1.2"
        ).get_poweroff_schedule()

    assert [o.hours for o in schedule] == ["08:00-12:00"]


def test_outages_use_provider_time_zone():
    tz = ZoneInfo("Europe/Kyiv")
    with _fetch(ARTICLES_HTML):
        schedule = ZOEProvider(
            "https://example.com", "1.2", time_zone=tz
        ).get_poweroff_schedule()

    assert all(outage.start.tzinfo is tz for outage in schedule)


def test_registry():
    from custom_components.energyua_poweroff.providers import (
        get_provider,
        get_providers,
    )

    assert set(get_providers()) == {"zoe", "energy_ua"}
    assert get_provider("zoe") is ZOEProvider
    with pytest.raises(KeyError):
        get_provider("unknown")
