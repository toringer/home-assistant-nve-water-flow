"""NVE Hydrological API client."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import aiohttp

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import NVE_API_BASE_URL, VERSION

_LOGGER = logging.getLogger(__name__)


class NVEAPI:
    """NVE Hydrological API client."""

    def __init__(self, api_key: str, hass) -> None:
        """Initialize the NVE API client."""
        self.api_key = api_key
        self.hass = hass
        self.session: Optional[aiohttp.ClientSession] = None
        # Create headers once during initialization
        self.headers = {"X-API-Key": self.api_key,
                        "User-Agent": f"home-assistant-sildre/{VERSION} https://github.com/toringer/home-assistant-sildre"}

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        _LOGGER.debug("Getting aiohttp session for NVE API")
        if self.session is None or self.session.closed:
            # Use Home Assistant's managed session
            _LOGGER.debug("Creating new aiohttp session for NVE API")
            self.session = async_get_clientsession(self.hass)
        return self.session

    async def close(self) -> None:
        """Close the aiohttp session."""
        # Home Assistant manages the session lifecycle, so we don't close it
        self.session = None

    async def test_connection(self) -> bool:
        """Test the API connection and key validity."""
        _LOGGER.debug("Testing NVE API connection with")
        try:
            session = await self._get_session()

            async with session.get(f"{NVE_API_BASE_URL}/Parameters", headers=self.headers) as response:
                if response.status == 200:
                    return True
                elif response.status == 401:
                    raise InvalidAPIKey("Invalid API key")
                else:
                    raise CannotConnect(
                        f"API returned status {response.status}")
        except aiohttp.ClientError as err:
            raise CannotConnect(f"Failed to connect to NVE API: {err}")

    async def get_series_data(
        self, station_id: str, parameters: list[str], resolution_time: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Get data for a specific station."""
        _LOGGER.debug("Fetching data for station %s", station_id)
        try:
            session = await self._get_session()
            params = {
                "StationId": station_id,
                "Parameter": ",".join(parameters),
                "ResolutionTime": resolution_time,
            }

            async with session.get(f"{NVE_API_BASE_URL}/Observations", params=params, headers=self.headers) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch data for station %s: %s",
                        station_id, response.status
                    )
                    return None

                data = await response.json()
                series_data = data.get("data", [])
                retval = []
                for series in series_data:
                    observations = series.get("observations", [])
                    if not observations:
                        _LOGGER.warning(
                            "No observations found for parameter %s for station: %s", series.get("parameter"), station_id)
                        continue

                    retval.append({
                        "parameter": series.get("parameter"),
                        "time": observations[-1].get("time"),
                        "value": observations[-1].get("value"),
                        "correction": observations[-1].get("correction"),
                        "quality": observations[-1].get("quality")
                    })
                return retval

        except Exception as err:
            _LOGGER.error(
                "Error fetching data for station %s: %s", station_id, err
            )
            return None

    async def get_station_info(self, station_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a station."""
        _LOGGER.debug("Fetching station info for station %s", station_id)
        try:
            session = await self._get_session()
            params = {"StationId": station_id}

            async with session.get(f"{NVE_API_BASE_URL}/Stations", params=params, headers=self.headers) as response:
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

                station = stations[0]
                series_list_raw = stations[0].get("seriesList", [])
                series_list = []
                for series in series_list_raw:
                    series_list.append({
                        "parameter_name": series.get("parameterName"),
                        "parameter": str(series.get("parameter")),
                        "unit": series.get("unit")
                    })

                retval = {
                    "station_id": station.get("stationId"),
                    "station_name": station.get("stationName"),
                    "culQm": station.get("culQm"),
                    "culQ5": station.get("culQ5"),
                    "culQ50": station.get("culQ50"),
                    "series_list": series_list,
                }
                return retval

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
