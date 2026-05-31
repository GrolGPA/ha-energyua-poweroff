import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EnergyUAPowerOffAPI

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=2)


class EnergyUAPowerOffCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api: EnergyUAPowerOffAPI) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="EnergyUA PowerOff",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self):
        try:
            return await self.hass.async_add_executor_job(
                self.api.get_poweroff_schedule
            )
        except Exception as exc:
            raise UpdateFailed(f"Помилка отримання графіку: {exc}") from exc
