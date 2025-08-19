"""Data coordinator for NVE Water Flow integration."""
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


class NVEWaterFlowCoordinator(DataUpdateCoordinator):
    """Coordinator for NVE Water Flow data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: NVEAPI,
        station_id: str,
        station_name: str,
        update_interval: timedelta | None = None,
    ) -> None:
        """Initialize the coordinator."""
        # Calculate update interval with random variance to prevent API collisions
        if update_interval is None:
            variance = timedelta(seconds=random.randint(-VARIANCE_SECONDS, VARIANCE_SECONDS))
            update_interval = BASE_UPDATE_INTERVAL + variance
            
        _LOGGER.debug(
            "Initializing coordinator for station %s with update interval: %s", 
            station_id, update_interval
        )
        
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name="nve_water_flow",
            update_interval=update_interval,
        )
        self.api = api
        self.station_id = station_id
        self.station_name = station_name
        self._last_update: Optional[datetime] = None

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data from NVE API for the station."""
        _LOGGER.debug("Updating data for station: %s", self.station_id)

        try:
            station_data = await self._fetch_station_data()
            if station_data:
                data = {self.station_id: station_data}
            else:
                _LOGGER.warning("No data received for station: %s", self.station_id)
                data = {}

        except Exception as err:
            _LOGGER.error(
                "Error updating data for station %s: %s", self.station_id, err
            )
            data = {}

        self._last_update = datetime.now()
        _LOGGER.debug("Data update completed for station: %s", self.station_id)

        return data

    async def _fetch_station_data(self) -> Optional[Dict[str, Any]]:
        """Fetch all data for the station."""
        station_data = {
            "station_id": self.station_id,
            "station_name": self.station_name,
            "last_update": datetime.now().isoformat(),
        }

        # Fetch water flow data
        water_flow_data = await self.api.get_water_flow_data(self.station_id)
        if water_flow_data:
            station_data["water_flow_data"] = water_flow_data

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

    def get_station_data(self) -> Optional[Dict[str, Any]]:
        """Get data for the station from the coordinator."""
        if not self.data or self.station_id not in self.data:
            return None
        return self.data[self.station_id]

    @property
    def last_update(self) -> Optional[datetime]:
        """Return the last update time."""
        return self._last_update
