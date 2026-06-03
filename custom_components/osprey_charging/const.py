"""Constants for the Osprey EV Charging integration."""

DOMAIN = "osprey_charging"

CONF_STATION_IDS = "station_ids"

DEFAULT_SCAN_INTERVAL = 300  # 5 minutes in seconds

API_BASE_URL = "https://apigw.ospreycharging.co.uk/portal/location/point"

# Connector standard identifiers as returned by the Osprey API
CONNECTOR_TYPE_CCS = "IEC_62196_T2_COMBO"
CONNECTOR_TYPE_TYPE2 = "IEC_62196_T2"
CONNECTOR_TYPE_CHADEMO = "CHADEMO"

# Human-readable labels for each connector type
CONNECTOR_TYPE_LABELS = {
    CONNECTOR_TYPE_CCS: "CCS",
    CONNECTOR_TYPE_TYPE2: "Type 2",
    CONNECTOR_TYPE_CHADEMO: "CHAdeMO",
}

# All connector types we expose sensors for
ALL_CONNECTOR_TYPES = [
    CONNECTOR_TYPE_CCS,
    CONNECTOR_TYPE_TYPE2,
    CONNECTOR_TYPE_CHADEMO,
]

# EVSE statuses that count as "available"
AVAILABLE_STATUSES = {"AVAILABLE"}
