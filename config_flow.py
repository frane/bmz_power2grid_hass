from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_UNIT_ID, CONF_SCAN_INTERVAL, DEFAULT_PORT, DEFAULT_UNIT_ID, DEFAULT_SCAN_INTERVAL

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is None:
            schema = vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): int,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            })
            return self.async_show_form(step_id="user", data_schema=schema)

        await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input.get(CONF_PORT, DEFAULT_PORT)}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"BMZ Power2Grid ({user_input[CONF_HOST]})",
            data=user_input,
        )