"""Constants for the NVE Water Flow integration."""

DOMAIN = "nve_water_flow"

# Configuration keys
CONF_API_KEY = "api_key"
CONF_STATIONS = "stations"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

# API configuration
NVE_API_BASE_URL = "https://hydapi.nve.no/api/v1"
WATER_FLOW_PARAMETER_ID = 1001  # Discharge parameter ID

# Sensor attributes
ATTR_STATION_ID = "station_id"
ATTR_STATION_NAME = "station_name"
ATTR_PARAMETER_NAME = "parameter_name"
ATTR_UNIT = "unit"
ATTR_QUALITY = "quality"
ATTR_CORRECTION = "correction"
ATTR_LAST_UPDATE = "last_update"

# Sensor names
SENSOR_WATER_FLOW = "water_flow"
SENSOR_WATER_FLOW_UNIT = "water_flow_unit"
SENSOR_LAST_UPDATE = "last_update"
