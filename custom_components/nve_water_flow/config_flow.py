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
    CONF_STATIONS,
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
        self.station_names: list[str] = []

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
                return await self.async_step_stations()
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

    async def async_step_stations(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the stations configuration step."""
        errors = {}

        if user_input is not None:
            station_names_text = user_input[CONF_STATIONS]
            self.station_names = [
                name.strip() for name in station_names_text.split("\n") if name.strip()
            ]

            if not self.station_names:
                errors["base"] = "invalid_station"
            else:
                try:
                    # Validate station names
                    api = NVEAPI(self.api_key)
                    for station_name in self.station_names:
                        station_id = await api.resolve_station_name(station_name)
                        if not station_id:
                            errors["base"] = "invalid_station"
                            break

                    if not errors:
                        # Create the config entry
                        return self.async_create_entry(
                            title="NVE Water Flow",
                            data={
                                CONF_API_KEY: self.api_key,
                                CONF_STATIONS: self.station_names,
                            },
                        )
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="stations",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATIONS): str,
                }
            ),
            errors=errors,
        )


class InvalidAPIKey(HomeAssistantError):
    """Error to indicate there is an invalid API key."""


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the API."""
