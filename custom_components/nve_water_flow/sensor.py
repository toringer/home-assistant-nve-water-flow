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
    CONF_NAME,
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
    CONF_STATIONS,
    DOMAIN,
    SENSOR_LAST_UPDATE,
    SENSOR_WATER_FLOW,
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
    stations = domain_data["stations"]

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

    # Create sensors for each station
    entities = []
    for station_name in stations:
        # Create water flow sensor
        entities.append(
            NVEWaterFlowSensor(
                coordinator,
                station_name,
                api,
                SENSOR_WATER_FLOW,
            )
        )

        # Create last update sensor
        entities.append(
            NVEWaterFlowSensor(
                coordinator,
                station_name,
                api,
                SENSOR_LAST_UPDATE,
            )
        )

    async_add_entities(entities)

    # Start the coordinator
    await coordinator.async_config_entry_first_refresh()


async def _async_update_data(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Update data from NVE API."""
    domain_data = hass.data[DOMAIN][entry_id]
    api = domain_data["api"]
    stations = domain_data["stations"]

    data = {}

    for station_name in stations:
        try:
            # Resolve station name to ID
            station_id = await api.resolve_station_name(station_name)
            if not station_id:
                _LOGGER.warning(
                    "Could not resolve station name: %s", station_name)
                continue

            # Get water flow data
            water_flow_data = await api.get_water_flow_data(station_id)
            if water_flow_data:
                data[station_name] = {
                    "station_id": station_id,
                    "water_flow_data": water_flow_data,
                }
            else:
                _LOGGER.warning(
                    "No water flow data for station: %s", station_name)

        except Exception as err:
            _LOGGER.error(
                "Error updating data for station %s: %s", station_name, err)

    return data


class NVEWaterFlowSensor(CoordinatorEntity, SensorEntity):
    """Representation of an NVE Water Flow sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        station_name: str,
        api: Any,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.station_name = station_name
        self.api = api
        self.sensor_type = sensor_type

        # Get the main device ID from the coordinator's data
        self.main_device_id = None
        if hasattr(coordinator, 'config_entry') and coordinator.config_entry:
            domain_data = coordinator.hass.data.get(DOMAIN, {}).get(
                coordinator.config_entry.entry_id, {})
            self.main_device_id = domain_data.get("main_device_id")

        # Set unique ID
        self._attr_unique_id = f"{station_name}_{sensor_type}"

        # Set attribution for all sensors
        self._attr_attribution = "Data provided by NVE Hydrological API"

        # Set name
        if sensor_type == SENSOR_WATER_FLOW:
            self._attr_name = f"{station_name} Water Flow"
        elif sensor_type == SENSOR_LAST_UPDATE:
            self._attr_name = f"{station_name} Last Update"

        # Set device class and state class for water flow sensor
        if sensor_type == SENSOR_WATER_FLOW:
            self._attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND

        # Set device class for last update sensor
        elif sensor_type == SENSOR_LAST_UPDATE:
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.station_name)},
            name=f"NVE Station {self.station_name}",
            manufacturer="Norwegian Water Resources and Energy Directorate",
            model="Hydrological Monitoring Station",
            sw_version="1.0.0",
            via_device=(
                DOMAIN, f"nve_water_flow_{self.coordinator.config_entry.entry_id}") if self.main_device_id else None,
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data or self.station_name not in self.coordinator.data:
            return None

        station_data = self.coordinator.data[self.station_name]
        water_flow_data = station_data.get("water_flow_data", {})

        if self.sensor_type == SENSOR_WATER_FLOW:
            return water_flow_data.get("value")
        elif self.sensor_type == SENSOR_LAST_UPDATE:
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
        if not self.coordinator.data or self.station_name not in self.coordinator.data:
            return {}

        station_data = self.coordinator.data[self.station_name]
        water_flow_data = station_data.get("water_flow_data", {})

        attrs = {
            ATTR_ATTRIBUTION: "Data provided by NVE Hydrological API",
            ATTR_STATION_NAME: water_flow_data.get("station_name"),
            ATTR_STATION_ID: water_flow_data.get("station_id"),
            ATTR_PARAMETER_NAME: water_flow_data.get("parameter_name"),
            ATTR_UNIT: water_flow_data.get("unit"),
        }

        # Add quality and correction info for water flow sensor
        if self.sensor_type == SENSOR_WATER_FLOW:
            attrs["quality"] = water_flow_data.get("quality")
            attrs[ATTR_CORRECTION] = water_flow_data.get("correction")
            attrs["method"] = water_flow_data.get("method")

        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.station_name in self.coordinator.data
            and self.coordinator.data[self.station_name].get("water_flow_data") is not None
        )

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": self.station_name,
            "model": VERSION,
            "manufacturer": "Norges vassdrags- og energidirektorat",
        }
