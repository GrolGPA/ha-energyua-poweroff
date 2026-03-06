from homeassistant.helpers.entity import Entity
from .api import EnergyUAPowerOffAPI
from .const import DOMAIN, CONF_BASE_URL, CONF_GROUP, DEFAULT_BASE_URL


async def async_setup_entry(hass, entry, async_add_entities):
    base_url = entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)
    group = entry.data.get(CONF_GROUP)
    api = EnergyUAPowerOffAPI(base_url, group)

    async_add_entities([EnergyUAPowerOffSensor(api, entry)], True)


class EnergyUAPowerOffSensor(Entity):
    def __init__(self, api, entry):
        self.api = api
        self._state = None
        self._attr_name = f"Power Off Schedule ({entry.data.get(CONF_GROUP)})"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_sensor"
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        try:
            data = await self.hass.async_add_executor_job(self.api.get_poweroff_schedule)
            self._state = f"{len(data)} entries"
            self._attr_extra_state_attributes = {"schedule": data}
        except Exception as e:
            self._state = "Error"
            self._attr_extra_state_attributes = {"error": str(e)}
