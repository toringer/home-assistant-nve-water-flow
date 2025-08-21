"""Options flow for Sildre integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class SildreOptionsFlow(config_entries.OptionsFlow):
    """Handle Sildre options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    # No configurable options remaining
                }
            ),
        )


@callback
def async_get_options_flow(
    config_entry: config_entries.ConfigEntry,
) -> SildreOptionsFlow:
    """Get the options flow for this handler."""
    return SildreOptionsFlow(config_entry)
