from __future__ import annotations

import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_GROUP
from .coordinator import EnergyUAPowerOffCoordinator
from .schedule import merge_ranges, parse_time_range

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EnergyUACalendar(coordinator, entry)])


class EnergyUACalendar(CoordinatorEntity, CalendarEntity):
    def __init__(self, coordinator: EnergyUAPowerOffCoordinator, entry):
        super().__init__(coordinator)
        self._attr_name = f"Energy-UA PowerOff ({entry.data.get(CONF_GROUP)})"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_calendar"
        self._events: list[CalendarEvent] = self._build_events()

    def _build_events(self) -> list[CalendarEvent]:
        """Convert coordinator data into sorted, merged calendar events."""
        ranges = []
        tz = dt_util.get_default_time_zone()

        for item in self.coordinator.data or []:
            try:
                ranges.append(parse_time_range(item["day"], item["hours"], tz))
            except (KeyError, TypeError, ValueError) as exc:
                _LOGGER.warning("Не вдалося розпарсити запис %s: %s", item, exc)

        return [
            CalendarEvent(
                summary="Відключення електроенергії",
                start=start,
                end=end,
            )
            for start, end in merge_ranges(ranges)
        ]

    def _handle_coordinator_update(self) -> None:
        self._events = self._build_events()
        super()._handle_coordinator_update()

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current outage or, if none is active, the next one.

        Home Assistant re-writes the entity state at the start and end of
        this event, so the calendar switches on/off exactly on time.
        """
        now = dt_util.now()
        return next((e for e in self._events if e.end > now), None)

    async def async_get_events(self, hass, start_date, end_date):
        return [
            event
            for event in self._events
            if event.end > start_date and event.start < end_date
        ]
