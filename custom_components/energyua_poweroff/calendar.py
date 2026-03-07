from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_GROUP

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    group = entry.data.get(CONF_GROUP)
    async_add_entities([EnergyUACalendar(coordinator, entry, group)], True)


class EnergyUACalendar(CoordinatorEntity, CalendarEntity):
    """Calendar entity that shows power outage events."""

    def __init__(self, coordinator, entry, group):
        super().__init__(coordinator)
        self._attr_name = f"Energy-UA PowerOff ({group})"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_calendar"
        self._events: list[CalendarEvent] = []
        self._next_event: CalendarEvent | None = None

    def _handle_coordinator_update(self) -> None:
        """Rebuild calendar events when the coordinator fetches new data."""
        self._rebuild_events()
        super()._handle_coordinator_update()

    def _rebuild_events(self) -> None:
        data = self.coordinator.data
        if not data:
            self._events = []
            self._next_event = None
            return

        events: list[CalendarEvent] = []
        now = dt_util.now()
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

                events.append(
                    CalendarEvent(
                        summary="Відключення електроенергії",
                        start=start,
                        end=end,
                    )
                )
            except Exception as exc:
                _LOGGER.debug("Помилка парсингу запису %s: %s", item, exc)
                continue

        self._events = events

        future = [e for e in events if e.start > now]
        self._next_event = sorted(future, key=lambda x: x.start)[0] if future else None

    @property
    def event(self) -> CalendarEvent | None:
        # Ensure events are built on first access
        if not self._events and self.coordinator.data:
            self._rebuild_events()
        return self._next_event

    async def async_get_events(self, hass, start_date, end_date):
        return [
            event
            for event in self._events
            if event.end > start_date and event.start < end_date
        ]
