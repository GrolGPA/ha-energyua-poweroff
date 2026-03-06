import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_BASE_URL, CONF_GROUP, DEFAULT_BASE_URL


class EnergyUAPowerOffFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Перевірка на дублікат
            await self.async_set_unique_id(
                f"{user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL)}_{user_input[CONF_GROUP]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Energy-UA PowerOff ({user_input[CONF_GROUP]})",
                data=user_input,
            )

        data_schema = vol.Schema({
            vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
            vol.Required(CONF_GROUP): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
