from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_PROVIDER,
    CONF_BASE_URL,
    CONF_GROUP,
    CONF_VERIFY_SSL,
    DEFAULT_PROVIDER,
)
from .coordinator import EnergyUAPowerOffCoordinator
from .providers import get_provider

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "calendar"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Energy-UA Power Off from a config entry."""
    provider_key = entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
    provider_cls = get_provider(provider_key)
    base_url = entry.data.get(CONF_BASE_URL, provider_cls.default_base_url)
    group = entry.data[CONF_GROUP]
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, False)

    provider = provider_cls(base_url, group, verify_ssl=verify_ssl)

    coordinator = EnergyUAPowerOffCoordinator(hass, provider)
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
