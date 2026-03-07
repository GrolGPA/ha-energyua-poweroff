from __future__ import annotations

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_GROUP


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    group = entry.data.get(CONF_GROUP)
    async_add_entities([EnergyUAPowerOffSensor(coordinator, entry, group)], True)


class EnergyUAPowerOffSensor(CoordinatorEntity, Entity):
    """Sensor showing the number of scheduled outages."""

    def __init__(self, coordinator, entry, group):
        super().__init__(coordinator)
        self._attr_name = f"Power Off Schedule ({group})"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_sensor"
        self._group = group

    @property
    def state(self):
        data = self.coordinator.data
        if data is None:
            return None
        return f"{len(data)} entries"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if data is None:
            return {}
        return {"schedule": data}
