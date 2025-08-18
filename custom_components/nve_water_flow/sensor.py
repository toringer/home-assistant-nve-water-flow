"""Sensor platform for NVE Water Flow."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    ATTR_CORRECTION,
    ATTR_LAST_UPDATE,
    ATTR_PARAMETER_NAME,
    ATTR_STATION_ID,
    ATTR_STATION_NAME,
    ATTR_UNIT,
    CONF_API_KEY,
    CONF_STATION_ID,
    DOMAIN,
    SENSOR_LAST_UPDATE,
    SENSOR_WATER_FLOW,
    SENSOR_CUL_QM,
    SENSOR_CUL_Q5,
    SENSOR_CUL_Q50,
    VERSION
)

_LOGGER = logging.getLogger(__name__)

# Fixed update interval for coordinator (3600 seconds = 1 hour)
UPDATE_INTERVAL = timedelta(seconds=3600)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NVE Water Flow sensor platform."""
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    api = domain_data["api"]
    station_id = domain_data["station_id"]

    # Create coordinator for data updates with fixed 3600 second interval
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="nve_water_flow",
        update_method=lambda: _async_update_data(hass, config_entry.entry_id),
        update_interval=UPDATE_INTERVAL,
    )

    # Store coordinator in hass data
    domain_data["coordinator"] = coordinator

    # Get station info to get the station name
    station_info = await api.get_station_info(station_id)
    station_name = station_info.get(
        "stationName", station_id) if station_info else station_id

    # Create sensors for the station
    entities = []

    # Create water flow sensor
    entities.append(
        NVEWaterFlowSensor(
            coordinator,
            station_id,
            station_name,
            api,
        )
    )

    # Create last update sensor
    entities.append(
        NVELastUpdateSensor(
            coordinator,
            station_id,
            station_name,
            api,
        )
    )

    # Create culQ sensors
    entities.append(
        NVECulQSensor(
            coordinator,
            station_id,
            station_name,
            api,
            SENSOR_CUL_QM,
        )
    )

    entities.append(
        NVECulQSensor(
            coordinator,
            station_id,
            station_name,
            api,
            SENSOR_CUL_Q5,
        )
    )

    entities.append(
        NVECulQSensor(
            coordinator,
            station_id,
            station_name,
            api,
            SENSOR_CUL_Q50,
        )
    )

    async_add_entities(entities)

    # Start the coordinator
    await coordinator.async_config_entry_first_refresh()


async def _async_update_data(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Update data from NVE API."""
    domain_data = hass.data[DOMAIN][entry_id]
    api = domain_data["api"]
    station_id = domain_data["station_id"]

    data = {}

    try:
        # Get water flow data directly using station ID
        water_flow_data = await api.get_water_flow_data(station_id)
        if water_flow_data:
            data[station_id] = {
                "station_id": station_id,
                "water_flow_data": water_flow_data,
            }
        else:
            _LOGGER.warning(
                "No water flow data for station: %s", station_id)

        # Get station info which includes culQ data
        station_info = await api.get_station_info(station_id)
        if station_info and station_id in data:
            # Extract culQ values from station info
            culq_data = {}
            if "culQm" in station_info:
                culq_data["culQm"] = station_info["culQm"]
            if "culQ5" in station_info:
                culq_data["culQ5"] = station_info["culQ5"]
            if "culQ50" in station_info:
                culq_data["culQ50"] = station_info["culQ50"]
            
            if culq_data:
                data[station_id]["culq_data"] = culq_data

    except Exception as err:
        _LOGGER.error(
            "Error updating data for station %s: %s", station_id, err)

    return data


class NVEBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for NVE Water Flow sensors."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        station_id: str,
        station_name: str,
        api: Any,
    ) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self.station_id = station_id
        self.station_name = station_name
        self.api = api

        # Get the main device ID from the coordinator's data
        self.main_device_id = None
        if hasattr(coordinator, 'config_entry') and coordinator.config_entry:
            domain_data = coordinator.hass.data.get(DOMAIN, {}).get(
                coordinator.config_entry.entry_id, {})
            self.main_device_id = domain_data.get("main_device_id")

        # Set attribution for all sensors
        self._attr_attribution = "Data provided by NVE Hydrological API"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.station_id)},
            name=f"NVE Station {self.station_name}",
            manufacturer="Norwegian Water Resources and Energy Directorate",
            model="Hydrological Monitoring Station",
            via_device=(
                DOMAIN, f"nve_water_flow_{self.coordinator.config_entry.entry_id}") if self.main_device_id else None,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.station_id in self.coordinator.data
            and self.coordinator.data[self.station_id].get("water_flow_data") is not None
        )


class NVEWaterFlowSensor(NVEBaseSensor):
    """Representation of an NVE Water Flow sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        station_id: str,
        station_name: str,
        api: Any,
    ) -> None:
        """Initialize the water flow sensor."""
        super().__init__(coordinator, station_id, station_name, api)

        # Set unique ID
        self._attr_unique_id = f"{station_id}_{SENSOR_WATER_FLOW}"

        # Set name
        self._attr_name = f"{station_name} Water Flow"

        # Set device class and state class for water flow sensor
        self._attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or self.station_id not in self.coordinator.data:
            return None

        station_data = self.coordinator.data[self.station_id]
        water_flow_data = station_data.get("water_flow_data", {})

        return water_flow_data.get("value")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data or self.station_id not in self.coordinator.data:
            return {}

        station_data = self.coordinator.data[self.station_id]
        water_flow_data = station_data.get("water_flow_data", {})

        attrs = {
            ATTR_ATTRIBUTION: "Data provided by NVE Hydrological API",
            ATTR_STATION_NAME: water_flow_data.get("station_name"),
            ATTR_STATION_ID: water_flow_data.get("station_id"),
            ATTR_PARAMETER_NAME: water_flow_data.get("parameter_name"),
            ATTR_UNIT: water_flow_data.get("unit"),
            "quality": water_flow_data.get("quality"),
            ATTR_CORRECTION: water_flow_data.get("correction"),
            "method": water_flow_data.get("method"),
        }

        return attrs


class NVELastUpdateSensor(NVEBaseSensor):
    """Representation of an NVE Last Update sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        station_id: str,
        station_name: str,
        api: Any,
    ) -> None:
        """Initialize the last update sensor."""
        super().__init__(coordinator, station_id, station_name, api)

        # Set unique ID
        self._attr_unique_id = f"{station_id}_{SENSOR_LAST_UPDATE}"

        # Set name
        self._attr_name = f"{station_name} Last Update"

        # Set device class for last update sensor
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or self.station_id not in self.coordinator.data:
            return None

        station_data = self.coordinator.data[self.station_id]
        water_flow_data = station_data.get("water_flow_data", {})

        time_str = water_flow_data.get("time")
        if time_str:
            try:
                # Parse ISO 8601 timestamp
                dt = datetime.fromisoformat(
                    time_str.replace("Z", "+00:00"))
                return dt
            except ValueError:
                _LOGGER.warning("Invalid timestamp format: %s", time_str)
                return None

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data or self.station_id not in self.coordinator.data:
            return {}

        station_data = self.coordinator.data[self.station_id]
        water_flow_data = station_data.get("water_flow_data", {})

        attrs = {
            ATTR_ATTRIBUTION: "Data provided by NVE Hydrological API",
            ATTR_STATION_NAME: water_flow_data.get("station_name"),
            ATTR_STATION_ID: water_flow_data.get("station_id"),
            ATTR_PARAMETER_NAME: water_flow_data.get("parameter_name"),
            ATTR_UNIT: water_flow_data.get("unit"),
        }

        return attrs


class NVECulQSensor(NVEBaseSensor):
    """Representation of an NVE culQ (flood statistics) sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        station_id: str,
        station_name: str,
        api: Any,
        culq_type: str,
    ) -> None:
        """Initialize the culQ sensor."""
        super().__init__(coordinator, station_id, station_name, api)
        self.culq_type = culq_type

        # Set unique ID based on culQ type
        self._attr_unique_id = f"{station_id}_{culq_type}"

        # Set name based on culQ type
        if culq_type == SENSOR_CUL_QM:
            self._attr_name = f"{station_name} Mean Flooding (culQm)"
            self.description = "Mean flooding based on the timestep for the observed values"
        elif culq_type == SENSOR_CUL_Q5:
            self._attr_name = f"{station_name} 5-Year Flood Return Period (culQ5)"
            self.description = "Flood with a return period of 5 years (20% probability each year)"
        elif culq_type == SENSOR_CUL_Q50:
            self._attr_name = f"{station_name} 50-Year Flood Return Period (culQ50)"
            self.description = "Flood with a return period of 50 years (2% probability each year)"

        # Set device class and state class for culQ sensor
        self._attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or self.station_id not in self.coordinator.data:
            return None

        station_data = self.coordinator.data[self.station_id]
        culq_data = station_data.get("culq_data", {})

        # Return the appropriate culQ value based on sensor type
        if self.culq_type == SENSOR_CUL_QM:
            return culq_data.get("culQm")
        elif self.culq_type == SENSOR_CUL_Q5:
            return culq_data.get("culQ5")
        elif self.culq_type == SENSOR_CUL_Q50:
            return culq_data.get("culQ50")

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data or self.station_id not in self.coordinator.data:
            return {}

        station_data = self.coordinator.data[self.station_id]

        attrs = {
            ATTR_ATTRIBUTION: "Data provided by NVE Hydrological API",
            ATTR_STATION_NAME: station_data.get("station_name", self.station_name),
            ATTR_STATION_ID: self.station_id,
            "description": self.description,
            "culq_type": self.culq_type,
        }

        return attrs
