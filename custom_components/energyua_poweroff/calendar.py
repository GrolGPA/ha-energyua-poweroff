from __future__ import annotations

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_GROUP
from .coordinator import EnergyUAPowerOffCoordinator


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
        """Convert coordinator data (sorted, merged outages) into events."""
        return [
            CalendarEvent(
                summary="Відключення електроенергії",
                start=outage.start,
                end=outage.end,
            )
            for outage in self.coordinator.data or []
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
