from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, CONF_PROVIDER, CONF_BASE_URL, CONF_GROUP, DEFAULT_PROVIDER
from .providers import get_provider

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "calendar"]
UPDATE_INTERVAL = timedelta(minutes=30)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Energy-UA Power Off from a config entry."""
    provider_key = entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
    provider_cls = get_provider(provider_key)
    base_url = entry.data.get(CONF_BASE_URL, provider_cls.default_base_url)
    group = entry.data[CONF_GROUP]

    provider = provider_cls(base_url, group)

    async def _async_update_data():
        return await hass.async_add_executor_job(provider.get_poweroff_schedule)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=_async_update_data,
        update_interval=UPDATE_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entries from older versions."""
    if entry.version == 1:
        _LOGGER.info("Migrating config entry %s from version 1 to 2", entry.entry_id)
        new_data = {**entry.data, CONF_PROVIDER: DEFAULT_PROVIDER}
        if CONF_BASE_URL not in new_data:
            new_data[CONF_BASE_URL] = "https://www.zoe.com.ua"
        hass.config_entries.async_update_entry(entry, data=new_data, version=2)
    return True
