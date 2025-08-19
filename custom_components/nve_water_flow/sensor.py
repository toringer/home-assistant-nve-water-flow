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
from .coordinator import NVEWaterFlowCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NVE Water Flow sensor platform."""
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: NVEWaterFlowCoordinator = domain_data["coordinator"]

    # Get station info from coordinator
    station_id = coordinator.station_id
    station_name = coordinator.station_name

    # Create sensors for the station
    entities = []

    # Create water flow sensor
    entities.append(
        NVEMeasurementSensor(
            coordinator,
            station_id,
            station_name,
            SENSOR_WATER_FLOW,
            "Water Flow",
            UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND,
            "mdi:water",
            SensorDeviceClass.VOLUME_FLOW_RATE,
            SensorStateClass.MEASUREMENT,
            "1001",  # Default water flow parameter ID
        )
    )

    # Create culQ sensors (these are from station info, not parameters)
    entities.append(
        NVECulQSensor(
            coordinator,
            station_id,
            station_name,
            SENSOR_CUL_QM,
        )
    )

    entities.append(
        NVECulQSensor(
            coordinator,
            station_id,
            station_name,
            SENSOR_CUL_Q5,
        )
    )

    entities.append(
        NVECulQSensor(
            coordinator,
            station_id,
            station_name,
            SENSOR_CUL_Q50,
        )
    )

    async_add_entities(entities)

    # Start the coordinator if not already started
    if not coordinator.data:
        await coordinator.async_config_entry_first_refresh()


class NVEBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for NVE Water Flow sensors."""

    def __init__(
        self,
        coordinator: NVEWaterFlowCoordinator,
        station_id: str,
        station_name: str,
    ) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self.station_id = station_id
        self.station_name = station_name

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


class NVEMeasurementSensor(NVEBaseSensor):
    """Representation of an NVE measurement sensor."""

    def __init__(
        self,
        coordinator: NVEWaterFlowCoordinator,
        station_id: str,
        station_name: str,
        sensor_type: str,
        sensor_name: str,
        unit: str,
        icon: str,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass = SensorStateClass.MEASUREMENT,
        parameter_id: str | None = None,
    ) -> None:
        """Initialize the measurement sensor."""
        super().__init__(coordinator, station_id, station_name)
        self.sensor_type = sensor_type
        self.sensor_name = sensor_name
        self.unit = unit
        self.icon = icon
        self.device_class = device_class
        self.state_class = state_class
        self.parameter_id = parameter_id

        # Set unique ID
        self._attr_unique_id = f"{station_id}_{sensor_type}"

        # Set name
        self._attr_name = f"{station_name} {sensor_name}"

        # Set device class and state class
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

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


class NVECulQSensor(NVEBaseSensor):
    """Representation of an NVE culQ (flood statistics) sensor."""

    def __init__(
        self,
        coordinator: NVEWaterFlowCoordinator,
        station_id: str,
        station_name: str,
        culq_type: str,
    ) -> None:
        """Initialize the culQ sensor."""
        super().__init__(coordinator, station_id, station_name)
        self.culq_type = culq_type

        # Set unique ID based on culQ type
        self._attr_unique_id = f"{station_id}_{culq_type}"

        # Set name based on culQ type
        if culq_type == SENSOR_CUL_QM:
            self._attr_name = f"{station_name} Mean Flooding (culQm)"
        elif culq_type == SENSOR_CUL_Q5:
            self._attr_name = f"{station_name} 5-Year Flood Return Period (culQ5)"
        elif culq_type == SENSOR_CUL_Q50:
            self._attr_name = f"{station_name} 50-Year Flood Return Period (culQ50)"
        else:
            self._attr_name = f"{station_name} {culq_type}"

        # Set device class and state class for culQ sensor
        self._attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND
        self._attr_icon = "mdi:chart-line"

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
            "culq_type": self.culq_type,
        }

        return attrs
