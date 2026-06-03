"""Config flow for Osprey EV Charging integration.

This integration is configured via YAML. The config flow exists solely to
support programmatic entry creation from async_setup (source: import) and
to enable device registry support. There is no UI flow.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN, CONF_STATION_IDS


class OspreyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Osprey EV Charging."""

    VERSION = 1

    async def async_step_import(self, data: dict) -> ConfigFlowResult:
        """Handle import from YAML configuration."""
        station_id: str = data[CONF_STATION_IDS]

        # Prevent duplicate entries for the same station
        await self.async_set_unique_id(station_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=station_id,  # Will be updated to the location name after first fetch
            data=data,
        )
