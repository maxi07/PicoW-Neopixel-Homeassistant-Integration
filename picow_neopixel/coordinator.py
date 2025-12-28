"""Data update coordinator for PicoW NeoPixel."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_CONTROL, API_INFO, API_STATE, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PicoWNeoPixelCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the PicoW NeoPixel device."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self.host = entry.data[CONF_HOST]
        self.port = entry.data.get(CONF_PORT, DEFAULT_PORT)
        self.session = async_get_clientsession(hass)
        self._available = True

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    @property
    def base_url(self) -> str:
        """Return the base URL for the device."""
        return f"http://{self.host}:{self.port}"

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via API."""
        try:
            async with asyncio.timeout(10):
                state = await self._get_state()
                info = await self._get_info()

                self._available = True

                return {
                    "state": state,
                    "info": info,
                }
        except asyncio.TimeoutError as err:
            self._available = False
            raise UpdateFailed(f"Timeout communicating with device at {self.host}") from err
        except aiohttp.ClientError as err:
            self._available = False
            raise UpdateFailed(f"Error communicating with device at {self.host}: {err}") from err
        except Exception as err:
            self._available = False
            _LOGGER.exception("Unexpected error fetching data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def _get_state(self) -> dict[str, Any]:
        """Get current state from device."""
        url = f"{self.base_url}{API_STATE}"
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Device returned status {response.status}")
                return await response.json()
        except Exception as err:
            _LOGGER.error("Error getting state from %s: %s", url, err)
            raise

    async def _get_info(self) -> dict[str, Any]:
        """Get device info."""
        url = f"{self.base_url}{API_INFO}"
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Device returned status {response.status}")
                return await response.json()
        except Exception as err:
            _LOGGER.error("Error getting info from %s: %s", url, err)
            raise

    async def async_send_command(self, command: dict[str, Any]) -> dict[str, Any]:
        """Send command to device."""
        url = f"{self.base_url}{API_CONTROL}"
        
        try:
            async with asyncio.timeout(10):
                async with self.session.post(
                    url,
                    json=command,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error(
                            "Command failed with status %s: %s",
                            response.status,
                            error_text
                        )
                        raise UpdateFailed(f"Command failed: {response.status}")
                    
                    result = await response.json()
                    
                    # Update coordinator data with new state
                    if "state" in result:
                        self.async_set_updated_data({
                            "state": result["state"],
                            "info": self.data.get("info", {}),
                        })
                    
                    return result
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout sending command to %s", self.host)
            raise UpdateFailed("Timeout sending command") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error sending command to %s: %s", self.host, err)
            raise UpdateFailed(f"Error sending command: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error sending command: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    @property
    def available(self) -> bool:
        """Return if device is available."""
        return self._available
