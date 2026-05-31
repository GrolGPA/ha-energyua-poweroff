import logging
from datetime import datetime, timedelta
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_GROUP
from .coordinator import EnergyUAPowerOffCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EnergyUACalendar(coordinator, entry)])


class EnergyUACalendar(CoordinatorEntity, CalendarEntity):
    def __init__(self, coordinator: EnergyUAPowerOffCoordinator, entry):
        super().__init__(coordinator)
        self._attr_name = f"Energy-UA PowerOff ({entry.data.get(CONF_GROUP)})"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_calendar"

    def _build_events(self):
        data = self.coordinator.data
        if not data:
            return []

        events = []
        tz = dt_util.DEFAULT_TIME_ZONE

        for item in data:
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

        return events

    @property
    def event(self):
        now = dt_util.now()
        future_events = [e for e in self._build_events() if e.start > now]
        if future_events:
            return sorted(future_events, key=lambda x: x.start)[0]
        return None

    async def async_get_events(self, hass, start_date, end_date):
        return [
            event
            for event in self._build_events()
            if event.end > start_date and event.start < end_date
        ]
        ]
