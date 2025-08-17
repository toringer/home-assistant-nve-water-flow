"""NVE Hydrological API client."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import aiohttp

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import NVE_API_BASE_URL, WATER_FLOW_PARAMETER_ID

_LOGGER = logging.getLogger(__name__)


class NVEAPI:
    """NVE Hydrological API client."""

    def __init__(self, api_key: str, hass) -> None:
        """Initialize the NVE API client."""
        self.api_key = api_key
        self.hass = hass
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            # Use Home Assistant's managed session
            self.session = async_get_clientsession(self.hass)
        return self.session

    async def close(self) -> None:
        """Close the aiohttp session."""
        # Home Assistant manages the session lifecycle, so we don't close it
        self.session = None

    async def test_connection(self) -> bool:
        """Test the API connection and key validity."""
        try:
            session = await self._get_session()
            # Pass headers in the request since we can't modify session headers
            headers = {"X-API-Key": self.api_key}
            
            async with session.get(f"{NVE_API_BASE_URL}/Parameters", headers=headers) as response:
                if response.status == 200:
                    return True
                elif response.status == 401:
                    raise InvalidAPIKey("Invalid API key")
                else:
                    raise CannotConnect(
                        f"API returned status {response.status}")
        except aiohttp.ClientError as err:
            raise CannotConnect(f"Failed to connect to NVE API: {err}")

    async def get_water_flow_data(
        self, station_id: str, resolution_time: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Get water flow data for a specific station."""
        try:
            session = await self._get_session()
            params = {
                "StationId": station_id,
                "Parameter": WATER_FLOW_PARAMETER_ID,
                "ResolutionTime": resolution_time,
            }
            headers = {"X-API-Key": self.api_key}

            async with session.get(f"{NVE_API_BASE_URL}/Observations", params=params, headers=headers) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch water flow data for station %s: %s",
                        station_id, response.status
                    )
                    return None

                data = await response.json()
                series_data = data.get("data", [])

                if not series_data:
                    _LOGGER.warning(
                        "No water flow data found for station: %s", station_id)
                    return None

                # Get the first (and should be only) series
                series = series_data[0]
                observations = series.get("observations", [])

                if not observations:
                    _LOGGER.warning(
                        "No observations found for station: %s", station_id)
                    return None

                # Get the latest observation
                latest_observation = observations[-1]

                return {
                    "station_id": station_id,
                    "station_name": series.get("stationName", "Unknown"),
                    "parameter_name": series.get("parameterName", "Unknown"),
                    "unit": series.get("unit", "Unknown"),
                    "value": latest_observation.get("value"),
                    "time": latest_observation.get("time"),
                    "quality": latest_observation.get("quality"),
                    "correction": latest_observation.get("correction"),
                    "method": series.get("method", "Unknown"),
                }

        except Exception as err:
            _LOGGER.error(
                "Error fetching water flow data for station %s: %s", station_id, err
            )
            return None

    async def get_station_info(self, station_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a station."""
        try:
            session = await self._get_session()
            params = {"StationId": station_id}
            headers = {"X-API-Key": self.api_key}

            async with session.get(f"{NVE_API_BASE_URL}/Stations", params=params, headers=headers) as response:
                if response.status == 401:
                    raise InvalidAPIKey("Invalid API key")
                elif response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch station info for %s: %s",
                        station_id, response.status
                    )
                    return None

                data = await response.json()
                stations = data.get("data", [])

                if not stations:
                    return None

                return stations[0]

        except InvalidAPIKey:
            # Re-raise InvalidAPIKey exceptions
            raise
        except Exception as err:
            _LOGGER.error(
                "Error fetching station info for %s: %s", station_id, err)
            return None


class InvalidAPIKey(Exception):
    """Raised when the API key is invalid."""


class CannotConnect(Exception):
    """Raised when unable to connect to the API."""
