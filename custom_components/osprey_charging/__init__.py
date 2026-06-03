"""Osprey EV Charging integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from dataclasses import dataclass

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_STATION_IDS, DEFAULT_SCAN_INTERVAL, API_BASE_URL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_STATION_IDS): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=30)
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

# Type alias for the data stored on each config entry
type OspreyConfigEntry = ConfigEntry["OspreyCoordinator"]


class OspreyCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches data for a single Osprey station."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        scan_interval: int,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=timedelta(seconds=scan_interval),
            # Data is a plain dict — __eq__ works, so skip redundant callbacks
            always_update=False,
        )
        self.station_id = station_id
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        """Fetch data for this station from the Osprey API."""
        url = f"{API_BASE_URL}/{self.station_id}"
        try:
            async with asyncio.timeout(10):
                async with self._session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as err:
            if self.data is not None:
                _LOGGER.warning(
                    "Network error fetching station %s, using cached data: %s",
                    self.station_id, err,
                )
                return self.data
            raise UpdateFailed(f"Could not fetch station {self.station_id}: {err}") from err
        except TimeoutError:
            if self.data is not None:
                _LOGGER.warning(
                    "Timeout fetching station %s, using cached data", self.station_id
                )
                return self.data
            raise UpdateFailed(f"Timeout fetching station {self.station_id}")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Create a config entry for each station ID declared in YAML."""
    if DOMAIN not in config:
        return True

    station_ids: list[str] = config[DOMAIN][CONF_STATION_IDS]
    scan_interval: int = config[DOMAIN]["scan_interval"]

    # Find station IDs that don't yet have a config entry
    existing_ids = {
        entry.data[CONF_STATION_IDS]
        for entry in hass.config_entries.async_entries(DOMAIN)
    }

    for station_id in station_ids:
        if station_id not in existing_ids:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": "import"},
                    data={
                        CONF_STATION_IDS: station_id,
                        "scan_interval": scan_interval,
                    },
                )
            )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: OspreyConfigEntry) -> bool:
    """Set up a single Osprey station from a config entry."""
    station_id: str = entry.data[CONF_STATION_IDS]
    scan_interval: int = entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    coordinator = OspreyCoordinator(hass, station_id, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator on the entry so sensor platform can retrieve it
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: OspreyConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
