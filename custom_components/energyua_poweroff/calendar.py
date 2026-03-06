import logging
from datetime import datetime, timedelta
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.util import dt as dt_util

from .api import EnergyUAPowerOffAPI
from .const import DOMAIN, CONF_BASE_URL, CONF_GROUP, DEFAULT_BASE_URL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    base_url = entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)
    group = entry.data.get(CONF_GROUP)

    api = EnergyUAPowerOffAPI(base_url, group)

    async_add_entities([EnergyUACalendar(api, entry)], True)


class EnergyUACalendar(CalendarEntity):
    def __init__(self, api, entry):
        self.api = api
        self._attr_name = f"Energy-UA PowerOff ({entry.data.get(CONF_GROUP)})"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_calendar"
        self._events = []
        self._next_event = None

    async def async_update(self):
        data = await self.hass.async_add_executor_job(
            self.api.get_poweroff_schedule
        )

        events = []
        now = dt_util.now()
        tz = dt_util.DEFAULT_TIME_ZONE

        for item in data:
            # Очікується формат:
            # {"day": "2026-03-07", "hours": "07:30-09:30"}

            try:
                date_str = item["day"]
                hours = item["hours"]

                start_str, end_str = hours.split("-")

                start_naive = datetime.strptime(
                    f"{date_str} {start_str.strip()}", "%Y-%m-%d %H:%M"
                )
                end_naive = datetime.strptime(
                    f"{date_str} {end_str.strip()}", "%Y-%m-%d %H:%M"
                )

                start = start_naive.replace(tzinfo=tz)
                end = end_naive.replace(tzinfo=tz)

                # Якщо кінець = 00:00, це означає кінець дня (наступна доба)
                if end <= start:
                    end += timedelta(days=1)

                event = CalendarEvent(
                    summary="Відключення електроенергії",
                    start=start,
                    end=end,
                )
                events.append(event)

            except Exception as exc:
                _LOGGER.debug("Помилка парсингу запису %s: %s", item, exc)
                continue

        self._events = events

        # Визначаємо наступну подію
        future_events = [e for e in events if e.start > now]
        if future_events:
            self._next_event = sorted(future_events, key=lambda x: x.start)[0]
        else:
            self._next_event = None

    @property
    def event(self):
        return self._next_event

    async def async_get_events(self, hass, start_date, end_date):
        return [
            event
            for event in self._events
            if event.end > start_date and event.start < end_date
        ]
