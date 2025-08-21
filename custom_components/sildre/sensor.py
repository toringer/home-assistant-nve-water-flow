"""Sensor platform for Sildre."""
from __future__ import annotations

import logging
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
    UnitOfTemperature,
    UnitOfLength,
    UnitOfElectricPotential,
    UnitOfSpeed,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    ATTR_LAST_UPDATE,
    ATTR_OBSERVATION_TIME,
    ATTR_PARAMETER_ID,
    ATTR_PARAMETER_NAME,
    ATTR_STATION_ID,
    ATTR_STATION_NAME,
    ATTR_UNIT,
    DOMAIN,
    SENSOR_CUL_QM,
    SENSOR_CUL_Q5,
    SENSOR_CUL_Q50
)
from .coordinator import SildreCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Sildre sensor platform."""
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: SildreCoordinator = domain_data["coordinator"]

    # Get station info from coordinator
    station_id = coordinator.station_id
    station_name = coordinator.station_name
    station_series_list = coordinator.station_series_list
    # Create sensors for the station
    entities = []

    for parameter in station_series_list:
        parameter_id = str(parameter.get("parameter"))
        parameter_name = parameter.get("parameter_name")
        unit = parameter.get("unit")

        entities.append(
            SildreMeasurementSensor(
                coordinator,
                station_id,
                station_name,
                parameter_name,
                unit,
                "mdi:water",
                SensorDeviceClass.VOLUME_FLOW_RATE,
                SensorStateClass.MEASUREMENT,
                parameter_id,
            )
        )

    # Create culQ sensors (these are from station info, not parameters)
    entities.append(
        SildreCulQSensor(
            coordinator,
            station_id,
            station_name,
            SENSOR_CUL_QM,
        )
    )

    entities.append(
        SildreCulQSensor(
            coordinator,
            station_id,
            station_name,
            SENSOR_CUL_Q5,
        )
    )

    entities.append(
        SildreCulQSensor(
            coordinator,
            station_id,
            station_name,
            SENSOR_CUL_Q50,
        )
    )

    async_add_entities(entities, update_before_add=True)

    # The coordinator is already started in the main init
    _LOGGER.info(
        "Sildre sensors setup completed for station %s", station_id)


class SildreBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Sildre sensors."""

    def __init__(
        self,
        coordinator: SildreCoordinator,
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
            name=self.station_name,
            manufacturer="Norwegian Water Resources and Energy Directorate",
            model="Hydrological Monitoring Station",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available and self.coordinator.data is not None
        )


class SildreMeasurementSensor(SildreBaseSensor):
    """Representation of an NVE measurement sensor."""

    def __init__(
        self,
        coordinator: SildreCoordinator,
        station_id: str,
        station_name: str,
        sensor_name: str,
        unit: str,
        icon: str,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass = SensorStateClass.MEASUREMENT,
        parameter_id: str | None = None,
    ) -> None:
        """Initialize the measurement sensor."""
        super().__init__(coordinator, station_id, station_name)
        self.sensor_name = sensor_name
        self.unit = unit
        self.icon = icon
        self.device_class = device_class
        self.state_class = state_class
        self.parameter_id = parameter_id

        # Set unique ID
        self._attr_unique_id = f"{station_id}_{parameter_id}"

        # Set name
        self._attr_name = f"{station_name} {sensor_name}"

        # Set device class and state class
        if self.unit == "m³/s":
            self._attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
            self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND
        elif self.unit == "°C":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif self.unit == "m":
            self._attr_device_class = SensorDeviceClass.DISTANCE
            self._attr_native_unit_of_measurement = UnitOfLength.METERS
        elif self.unit == "Volt":
            self._attr_device_class = SensorDeviceClass.VOLTAGE
            self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        elif self.unit == "m/s":
            self._attr_device_class = SensorDeviceClass.SPEED
            self._attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
        elif self.unit == "mm":
            self._attr_device_class = SensorDeviceClass.PRECIPITATION
            self._attr_native_unit_of_measurement = UnitOfLength.MILLIMETERS
        else:
            self._attr_device_class = SensorDeviceClass.GENERIC
            self._attr_native_unit_of_measurement = self.unit

        self._attr_state_class = state_class

        self._attr_icon = icon

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            _LOGGER.debug("No coordinator data for sensor %s",
                          self._attr_unique_id)
            return None

        parameter = self.coordinator.get_data_for_parameter(self.parameter_id)
        if not parameter:
            _LOGGER.debug("No parameter data found for parameter %s for sensor %s",
                          self.parameter_id, self._attr_unique_id)
            return None

        latest_value = parameter.get("value")
        _LOGGER.debug("Sensor %s found value: %s",
                      self._attr_unique_id, latest_value)
        return latest_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return {}

        parameter = self.coordinator.get_data_for_parameter(self.parameter_id)
        station_data = self.coordinator.data
        attrs = {
            ATTR_ATTRIBUTION: "Data provided by NVE Hydrological API",
            ATTR_STATION_NAME: station_data.get("station_name"),
            ATTR_STATION_ID: station_data.get("station_id"),
            ATTR_PARAMETER_NAME: self.sensor_name,
            ATTR_PARAMETER_ID: self.parameter_id,
            ATTR_UNIT: self.unit,
            ATTR_LAST_UPDATE: station_data.get("last_update"),
            ATTR_OBSERVATION_TIME: parameter.get("time")
        }
        return attrs


class SildreCulQSensor(SildreBaseSensor):
    """Representation of an NVE culQ (flood statistics) sensor."""

    def __init__(
        self,
        coordinator: SildreCoordinator,
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
        if not self.coordinator.data:
            return None

        station_data = self.coordinator.data
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
        if not self.coordinator.data:
            return {}

        station_data = self.coordinator.data

        attrs = {
            ATTR_ATTRIBUTION: "Data provided by NVE Hydrological API",
            ATTR_STATION_NAME: station_data.get("station_name", self.station_name),
            ATTR_STATION_ID: self.station_id,
            "culq_type": self.culq_type,
        }

        return attrs
