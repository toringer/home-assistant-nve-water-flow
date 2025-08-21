"""Data coordinator for Sildre integration."""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .nve_api import NVEAPI
from .const import UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

# Base update interval with variance to prevent API collisions
BASE_UPDATE_INTERVAL = timedelta(seconds=UPDATE_INTERVAL_SECONDS)
VARIANCE_SECONDS = 30


class SildreCoordinator(DataUpdateCoordinator):
    """Coordinator for Sildre data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: NVEAPI,
        station_id: str,
        station_name: str,
        station_series_list: list[Any],
        update_interval: timedelta | None = None,
    ) -> None:
        """Initialize the coordinator."""
        # Calculate update interval with random variance to prevent API collisions
        if update_interval is None:
            variance = timedelta(
                seconds=random.randint(-VARIANCE_SECONDS, VARIANCE_SECONDS))
            update_interval = BASE_UPDATE_INTERVAL + variance

        _LOGGER.debug(
            "Initializing coordinator for station %s with update interval: %s",
            station_id, update_interval
        )

        super().__init__(
            hass,
            logging.getLogger(__name__),
            name="sildre",
            update_interval=update_interval,
        )
        self.api = api
        self.station_id = station_id
        self.station_name = station_name
        self.station_series_list = station_series_list
        self.station_data = {}
        self._last_update: Optional[datetime] = None

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data from NVE API for the station."""
        _LOGGER.debug("Updating data for station: %s", self.station_id)

        try:
            station_data = await self._fetch_station_data()
            if station_data:
                data = station_data
            else:
                _LOGGER.warning(
                    "No data received for station: %s", self.station_id)
                data = {}

        except Exception as err:
            _LOGGER.error(
                "Error updating data for station %s: %s", self.station_id, err
            )
            data = {}

        self._last_update = datetime.now()
        _LOGGER.debug("Data update completed for station: %s", self.station_id)
        self.station_data = station_data
        return data

    async def _fetch_station_data(self) -> Optional[Dict[str, Any]]:
        """Fetch all data for the station."""
        station_data = {
            "station_id": self.station_id,
            "station_name": self.station_name,
            "last_update": datetime.now().isoformat(),
        }

        # Fetch sildre data
        parameter_ids = [str(series.get("parameter"))
                         for series in self.station_series_list]
        series_data = await self.api.get_series_data(self.station_id, parameter_ids)
        if series_data:
            station_data["series_data"] = series_data

        # Fetch station info (includes culQ data)
        station_info = await self.api.get_station_info(self.station_id)
        if station_info:
            # Extract culQ values from station info
            culq_data = {}
            if "culQm" in station_info:
                culq_data["culQm"] = station_info["culQm"]
            if "culQ5" in station_info:
                culq_data["culQ5"] = station_info["culQ5"]
            if "culQ50" in station_info:
                culq_data["culQ50"] = station_info["culQ50"]

            if culq_data:
                station_data["culq_data"] = culq_data

        # Only return data if we have at least some information
        if len(station_data) > 2:  # More than just station_id and last_update
            return station_data

        return None

    def get_data_for_parameter(self, parameter_id: str) -> Any:
        """Get data for a specific parameter."""
        if not self.station_data:
            return None

        series_data = self.station_data.get("series_data", [])
        for serie in series_data:
            if str(serie.get("parameter")) == parameter_id:
                return serie

        return None

    @property
    def last_update(self) -> Optional[datetime]:
        """Return the last update time."""
        return self._last_update
