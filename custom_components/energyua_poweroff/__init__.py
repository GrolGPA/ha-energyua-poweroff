from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import EnergyUAPowerOffAPI
from .const import DOMAIN, CONF_BASE_URL, CONF_GROUP, CONF_VERIFY_SSL, DEFAULT_BASE_URL
from .coordinator import EnergyUAPowerOffCoordinator

PLATFORMS = ["sensor", "calendar"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    base_url = entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)
    group = entry.data.get(CONF_GROUP)
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, False)
    api = EnergyUAPowerOffAPI(base_url, group, verify_ssl=verify_ssl)

    coordinator = EnergyUAPowerOffCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
