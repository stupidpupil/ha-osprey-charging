"""Sensor platform for Osprey EV Charging integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ALL_CONNECTOR_TYPES,
    CONNECTOR_TYPE_LABELS,
    CONNECTOR_TYPE_CCS,
    CONNECTOR_TYPE_CHADEMO,
    AVAILABLE_STATUSES,
)
from . import OspreyCoordinator

_LOGGER = logging.getLogger(__name__)

# Coordinator manages all fetching; entities do not update independently.
PARALLEL_UPDATES = 0

# Map connector type constants to MDI icon names
_CONNECTOR_ICONS: dict[str, str] = {
    CONNECTOR_TYPE_CCS: "mdi:ev-plug-ccs2",
    CONNECTOR_TYPE_CHADEMO: "mdi:ev-plug-chademo",
}
_DEFAULT_CONNECTOR_ICON = "mdi:ev-plug-type2"


@dataclass(frozen=True)
class OspreyConnectorSensorDescription(SensorEntityDescription):
    """Describes an Osprey connector count sensor."""
    connector_type: str = ""
    count_available_only: bool = True  # True = available count, False = total count


def _build_sensor_descriptions() -> list[OspreyConnectorSensorDescription]:
    """Build sensor descriptions for all connector types (total + available)."""
    descriptions = []
    for connector_type in ALL_CONNECTOR_TYPES:
        label = CONNECTOR_TYPE_LABELS[connector_type]
        slug = label.lower().replace(" ", "_")
        icon = _CONNECTOR_ICONS.get(connector_type, _DEFAULT_CONNECTOR_ICON)

        descriptions.append(OspreyConnectorSensorDescription(
            key=f"available_{slug}",
            name=f"Available {label} Chargers",
            icon=icon,
            native_unit_of_measurement="chargers",
            connector_type=connector_type,
            count_available_only=True,
        ))

        descriptions.append(OspreyConnectorSensorDescription(
            key=f"total_{slug}",
            name=f"Total {label} Chargers",
            icon=icon,
            native_unit_of_measurement="chargers",
            connector_type=connector_type,
            count_available_only=False,
        ))

    return descriptions


SENSOR_DESCRIPTIONS = _build_sensor_descriptions()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Osprey Charging sensor entities from a config entry."""
    coordinator: OspreyCoordinator = entry.runtime_data

    async_add_entities(
        OspreyChargingSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class OspreyChargingSensor(CoordinatorEntity[OspreyCoordinator], SensorEntity):
    """A sensor representing a connector type count at an Osprey charging location."""

    entity_description: OspreyConnectorSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OspreyCoordinator,
        description: OspreyConnectorSensorDescription,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        location_name: str = coordinator.data.get("name", coordinator.station_id)

        self._attr_unique_id = f"{coordinator.station_id}_{description.key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.station_id)},
            name=location_name,
            manufacturer="Osprey Charging",
            model="EV Charging Location",
            configuration_url="https://ospreycharging.co.uk",
        )

        # Compute initial value immediately — coordinator data is already available
        # at construction time (async_config_entry_first_refresh has completed).
        self._attr_native_value = self._count_connectors(coordinator.data)

    @property
    def available(self) -> bool:
        """Return False if the coordinator has no data for this station."""
        return super().available and self.coordinator.data is not None

    def _count_connectors(self, data: dict | None = None) -> int:
        """Count connectors of the configured type, optionally filtering to available EVSEs only."""
        connector_type = self.entity_description.connector_type
        available_only = self.entity_description.count_available_only
        station_data = data if data is not None else self.coordinator.data
        if station_data is None:
            return 0

        count = 0
        for evse in station_data.get("evses", []):
            if available_only and evse.get("status") not in AVAILABLE_STATUSES:
                continue
            for connector in evse.get("connectors", []):
                if connector.get("standard") == connector_type:
                    count += 1
        return count

    @callback
    def _handle_coordinator_update(self) -> None:
        """Recompute state when coordinator data changes and push to HA."""
        if self.available:
            self._attr_native_value = self._count_connectors()
        else:
            self._attr_native_value = None
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes about this location."""
        data = self.coordinator.data
        if not self.available or data is None:
            return {}

        attrs: dict = {}
        attrs["station_id"] = self.coordinator.station_id
        attrs["address"] = data.get("address", "")
        attrs["city"] = data.get("city", "")
        attrs["postal_code"] = data.get("postalCode", "")

        coords = data.get("coordinates", {})
        if coords:
            attrs["latitude"] = coords.get("latitude")
            attrs["longitude"] = coords.get("longitude")

        opening = data.get("openingTimes", {})
        attrs["open_24_7"] = opening.get("twentyfourseven", False)

        connector_type = self.entity_description.connector_type
        evse_statuses = []
        for evse in data.get("evses", []):
            for connector in evse.get("connectors", []):
                if connector.get("standard") == connector_type:
                    evse_statuses.append({
                        "evse_id": evse.get("evseId"),
                        "station_id": evse.get("stationId"),
                        "status": evse.get("status"),
                        "max_kw": connector.get("maxElectricPower"),
                    })
        attrs["evses"] = evse_statuses

        return attrs
