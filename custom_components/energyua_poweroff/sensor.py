import logging

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_GROUP
from .coordinator import EnergyUAPowerOffCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EnergyUAPowerOffSensor(coordinator, entry)])


class EnergyUAPowerOffSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator: EnergyUAPowerOffCoordinator, entry):
        super().__init__(coordinator)
        self._attr_name = f"Power Off Schedule ({entry.data.get(CONF_GROUP)})"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_sensor"

    @property
    def state(self):
        if self.coordinator.data is None:
            return "Unavailable"
        return f"{len(self.coordinator.data)} entries"

    @property
    def extra_state_attributes(self):
        if self.coordinator.data is None:
            return {}
        return {"schedule": self.coordinator.data}
