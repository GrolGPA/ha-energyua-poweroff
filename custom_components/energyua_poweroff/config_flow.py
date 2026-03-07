from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, CONF_PROVIDER, CONF_BASE_URL, CONF_GROUP, DEFAULT_PROVIDER
from .providers import get_providers


class EnergyUAPowerOffFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self) -> None:
        self._provider_key: str | None = None

    async def async_step_user(self, user_input=None):
        """Step 1 — choose the provider (oblast / data source)."""
        providers = get_providers()

        if user_input is not None:
            self._provider_key = user_input[CONF_PROVIDER]
            return await self.async_step_details()

        provider_options = {k: cls.name for k, cls in providers.items()}

        data_schema = vol.Schema({
            vol.Required(CONF_PROVIDER, default=DEFAULT_PROVIDER): vol.In(
                provider_options
            ),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_details(self, user_input=None):
        """Step 2 — enter group and optional base_url."""
        providers = get_providers()
        provider_cls = providers[self._provider_key]
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input.get(CONF_BASE_URL, provider_cls.default_base_url)
            group = user_input[CONF_GROUP]

            await self.async_set_unique_id(f"{self._provider_key}_{base_url}_{group}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{provider_cls.name} ({group})",
                data={
                    CONF_PROVIDER: self._provider_key,
                    CONF_BASE_URL: base_url,
                    CONF_GROUP: group,
                },
            )

        data_schema = vol.Schema({
            vol.Optional(
                CONF_BASE_URL, default=provider_cls.default_base_url
            ): str,
            vol.Required(CONF_GROUP): str,
        })

        return self.async_show_form(
            step_id="details",
            data_schema=data_schema,
            errors=errors,
        )
