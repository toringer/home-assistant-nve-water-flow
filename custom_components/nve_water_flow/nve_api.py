"""NVE Hydrological API client."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import aiohttp

from .const import NVE_API_BASE_URL, WATER_FLOW_PARAMETER_ID

_LOGGER = logging.getLogger(__name__)


class NVEAPI:
    """NVE Hydrological API client."""

    def __init__(self, api_key: str) -> None:
        """Initialize the NVE API client."""
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"X-API-Key": self.api_key}
            )
        return self.session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def test_connection(self) -> bool:
        """Test the API connection and key validity."""
        try:
            session = await self._get_session()
            async with session.get(f"{NVE_API_BASE_URL}/Parameters") as response:
                if response.status == 200:
                    return True
                elif response.status == 401:
                    raise InvalidAPIKey("Invalid API key")
                else:
                    raise CannotConnect(
                        f"API returned status {response.status}")
        except aiohttp.ClientError as err:
            raise CannotConnect(f"Failed to connect to NVE API: {err}")

    async def resolve_station_name(self, station_name: str) -> Optional[str]:
        """Resolve a station name to a station ID."""
        try:
            session = await self._get_session()
            params = {"StationName": station_name}

            async with session.get(f"{NVE_API_BASE_URL}/Stations", params=params) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to fetch stations: %s",
                                  response.status)
                    return None

                data = await response.json()
                stations = data.get("data", [])

                if not stations:
                    _LOGGER.warning(
                        "No stations found for name: %s", station_name)
                    return None

                if len(stations) > 1:
                    _LOGGER.warning(
                        "Multiple stations found for name '%s', using first match",
                        station_name
                    )

                station_id = stations[0].get("stationId")
                if not station_id:
                    _LOGGER.error(
                        "Station ID not found in response for: %s", station_name)
                    return None

                _LOGGER.info("Resolved station '%s' to ID: %s",
                             station_name, station_id)
                return station_id

        except Exception as err:
            _LOGGER.error("Error resolving station name '%s': %s",
                          station_name, err)
            return None

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

            async with session.get(f"{NVE_API_BASE_URL}/Observations", params=params) as response:
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

            async with session.get(f"{NVE_API_BASE_URL}/Stations", params=params) as response:
                if response.status != 200:
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

        except Exception as err:
            _LOGGER.error(
                "Error fetching station info for %s: %s", station_id, err)
            return None


class InvalidAPIKey(Exception):
    """Raised when the API key is invalid."""


class CannotConnect(Exception):
    """Raised when unable to connect to the API."""
