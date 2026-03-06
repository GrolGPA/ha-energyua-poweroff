import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

MONTHS_UA = {
    "січня": 1, "лютого": 2, "березня": 3, "квітня": 4,
    "травня": 5, "червня": 6, "липня": 7, "серпня": 8,
    "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12,
}


class EnergyUAPowerOffAPI:
    def __init__(self, base_url: str, group: str):
        self.base_url = base_url.rstrip('/')
        self.group = group

    def get_poweroff_schedule(self):
        url = f"{self.base_url}/outage/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        articles = soup.find_all("article")
        if not articles:
            raise ValueError("Не знайдено записів на сторінці")

        data = []
        seen_dates = set()

        for article in articles:
            title_el = article.find(["h2", "h3", "h1"])
            if not title_el:
                continue
            title = title_el.get_text()

            date_str = self._extract_date(title)
            if not date_str or date_str in seen_dates:
                continue
            seen_dates.add(date_str)

            content = article.get_text()
            hours_list = self._extract_hours_for_group(content, self.group)

            for hours in hours_list:
                data.append({
                    "day": date_str,
                    "hours": hours,
                })

        return data

    def _extract_date(self, title):
        """Витягує дату з заголовка статті, напр. '7 БЕРЕЗНЯ'."""
        match = re.search(
            r'(\d{1,2})\s+'
            r'(СІЧНЯ|ЛЮТОГО|БЕРЕЗНЯ|КВІТНЯ|ТРАВНЯ|ЧЕРВНЯ|'
            r'ЛИПНЯ|СЕРПНЯ|ВЕРЕСНЯ|ЖОВТНЯ|ЛИСТОПАДА|ГРУДНЯ)',
            title, re.IGNORECASE,
        )
        if not match:
            return None
        day = int(match.group(1))
        month = MONTHS_UA.get(match.group(2).lower())
        if not month:
            return None
        year = datetime.now().year
        return f"{year}-{month:02d}-{day:02d}"

    def _extract_hours_for_group(self, content, group):
        """Знаходить години відключення для конкретної черги.

        Формат на сайті: '1.2: 09:00 – 14:00' або
        '3.1: 00:00 – 00:30, 07:30 – 11:00' (кілька діапазонів).
        """
        escaped = re.escape(group)
        pattern = (
            rf'{escaped}:\s*'
            rf'(\d{{1,2}}:\d{{2}}\s*[–\-]\s*\d{{1,2}}:\d{{2}}'
            rf'(?:,\s*\d{{1,2}}:\d{{2}}\s*[–\-]\s*\d{{1,2}}:\d{{2}})*)'
        )
        match = re.search(pattern, content)
        if not match:
            return []

        raw = match.group(1)
        ranges = [r.strip() for r in raw.split(",")]
        result = []
        for r in ranges:
            normalized = re.sub(r'\s*[–\-]\s*', '-', r)
            result.append(normalized)
        return result
