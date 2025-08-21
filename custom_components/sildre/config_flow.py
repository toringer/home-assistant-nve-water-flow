"""Config flow for Sildre integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_API_KEY,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_STATION_SERIES_LIST,
    DOMAIN,
)
from .nve_api import NVEAPI, InvalidAPIKey, CannotConnect

_LOGGER = logging.getLogger(__name__)


class NVEWaterFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sildre."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api_key: str | None = None
        self.station_id: str | None = None
        self.station_name: str | None = None
        self.series_list: list[Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self.api_key = user_input[CONF_API_KEY]

            try:
                # Test the API key
                api = NVEAPI(self.api_key, self.hass)
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
                    # Validate station ID and get station name using the API
                    api = NVEAPI(self.api_key, self.hass)
                    station_info = await api.get_station_info(station_id)
                    if not station_info:
                        errors["base"] = "invalid_station"
                    else:
                        # Extract station name from station info
                        self.station_id = station_id
                        self.station_name = station_info.get("station_name")
                        self.series_list = station_info.get("series_list", [])

                        _LOGGER.info("Validated station %s: %s with %d series",
                                     station_id, self.station_name, len(self.series_list))

                        # Create the config entry with station name
                        return self.async_create_entry(
                            title=f"Sildre - {self.station_name}",
                            data={
                                CONF_API_KEY: self.api_key,
                                CONF_STATION_ID: self.station_id,
                                CONF_STATION_NAME: self.station_name,
                                CONF_STATION_SERIES_LIST: self.series_list,
                            },
                        )
                except InvalidAPIKey:
                    errors["base"] = "invalid_api_key"
                except CannotConnect:
                    errors["base"] = "cannot_connect"
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
