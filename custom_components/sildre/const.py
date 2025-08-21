"""Constants for the Sildre integration."""

DOMAIN = "sildre"
VERSION = "1.0.0"

# Configuration keys
CONF_API_KEY = "api_key"
CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
# List of dicts with 'parameter' and 'parameterName'
CONF_STATION_SERIES_LIST = "station_series_list"

# API configuration
NVE_API_BASE_URL = "https://hydapi.nve.no/api/v1"

# Update interval (30 minutes base with 30 seconds variance to prevent API collisions)
UPDATE_INTERVAL_SECONDS = 600  # 10 minutes in seconds

# Sensor attributes
ATTR_STATION_ID = "station_id"
ATTR_STATION_NAME = "station_name"
ATTR_PARAMETER_NAME = "parameter_name"
ATTR_PARAMETER_ID = "parameter_id"
ATTR_UNIT = "unit"
ATTR_QUALITY = "quality"
ATTR_CORRECTION = "correction"
ATTR_LAST_UPDATE = "last_update"
ATTR_OBSERVATION_TIME = "observation_time"

# Sensor names
SENSOR_WATER_FLOW = "water_flow"
SENSOR_LAST_UPDATE = "last_update"
SENSOR_CUL_QM = "cul_qm"
SENSOR_CUL_Q5 = "cul_q5"
SENSOR_CUL_Q50 = "cul_q50"
