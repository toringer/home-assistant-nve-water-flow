"""The NVE Water Flow integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_API_KEY, CONF_SCAN_INTERVAL, CONF_STATIONS, DOMAIN
from .nve_api import NVEAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NVE Water Flow from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get configuration
    api_key = entry.data[CONF_API_KEY]
    stations = entry.data[CONF_STATIONS]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, 300)

    # Create API client
    api = NVEAPI(api_key)
    
    try:
        # Test connection
        await api.test_connection()
    except Exception as err:
        _LOGGER.error("Failed to connect to NVE API: %s", err)
        raise ConfigEntryNotReady from err

    # Store API client in hass data
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "stations": stations,
        "scan_interval": scan_interval,
    }

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Close API session
        if entry.entry_id in hass.data[DOMAIN]:
            api = hass.data[DOMAIN][entry.entry_id]["api"]
            await api.close()
            hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # No migration needed for version 1
        return True

    return False
