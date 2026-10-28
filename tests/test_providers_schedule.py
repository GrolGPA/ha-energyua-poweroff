from unittest.mock import patch

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

    assert [item["hours"] for item in schedule] == ["09:00-14:00", "22:00-24:00"]
    assert len({item["day"] for item in schedule}) == 1


def test_energy_ua_article_fallback():
    with _fetch(ARTICLES_HTML):
        schedule = EnergyUAProvider(
            "https://example.com", "1.2"
        ).get_poweroff_schedule()

    assert [item["hours"] for item in schedule] == ["09:00-14:00", "22:00-24:00"]


def test_energy_ua_table():
    html = (
        "<table><tr><th>День</th><th>Години</th></tr>"
        "<tr><td>07.03.2026</td><td>08:00–12:00, 18:00–24:00</td></tr></table>"
    )
    with _fetch(html):
        schedule = EnergyUAProvider(
            "https://example.com", "1.2"
        ).get_poweroff_schedule()

    assert schedule == [
        {"day": "2026-03-07", "hours": "08:00-12:00"},
        {"day": "2026-03-07", "hours": "18:00-24:00"},
    ]
