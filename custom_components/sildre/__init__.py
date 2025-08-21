"""The Sildre integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_API_KEY, CONF_STATION_ID, CONF_STATION_NAME, CONF_STATION_SERIES_LIST, DOMAIN
from .nve_api import NVEAPI
from .coordinator import NVEWaterFlowCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sildre from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get configuration
    api_key = entry.data[CONF_API_KEY]
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME, station_id)
    station_series_list = entry.data.get(CONF_STATION_SERIES_LIST, [])
    # Create API client
    api = NVEAPI(api_key, hass)

    try:
        # Test connection
        await api.test_connection()
    except Exception as err:
        _LOGGER.error("Failed to connect to NVE API: %s", err)
        raise ConfigEntryNotReady from err

    # Create coordinator for data updates
    coordinator = NVEWaterFlowCoordinator(
        hass=hass,
        api=api,
        station_id=station_id,
        station_name=station_name,
        station_series_list=station_series_list,
    )

    # Store coordinator and API client in hass data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Close API session and clean up coordinator
        if entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # No migration needed for version 1
        return True

    return False
