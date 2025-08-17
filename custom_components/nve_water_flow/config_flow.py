"""Config flow for NVE Water Flow integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_API_KEY,
    CONF_STATION_ID,
    DOMAIN,
)
from .nve_api import NVEAPI

_LOGGER = logging.getLogger(__name__)


class NVEWaterFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NVE Water Flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api_key: str | None = None
        self.station_id: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self.api_key = user_input[CONF_API_KEY]

            try:
                # Test the API key
                api = NVEAPI(self.api_key)
                await api.test_connection()
                return await self.async_step_station()
            except InvalidAPIKey:
                errors["base"] = "invalid_api_key"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the station configuration step."""
        errors = {}

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]

            if not station_id:
                errors["base"] = "invalid_station"
            else:
                try:
                    # Validate station ID using the API
                    api = NVEAPI(self.api_key)
                    station_info = await api.get_station_info(station_id)
                    if not station_info:
                        errors["base"] = "invalid_station"
                    else:
                        self.station_id = station_id
                        # Create the config entry
                        return self.async_create_entry(
                            title="NVE Water Flow",
                            data={
                                CONF_API_KEY: self.api_key,
                                CONF_STATION_ID: self.station_id,
                            },
                        )
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_ID): str,
                }
            ),
            errors=errors,
        )


class InvalidAPIKey(HomeAssistantError):
    """Error to indicate there is an invalid API key."""


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the API."""
