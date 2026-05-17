"""Config flow for the PicoW NeoPixel integration.

Discovery is delegated to Home Assistant's built-in Zeroconf component. The
device advertises an ``_picow-neopixel._tcp.local.`` service which HA picks up
and forwards to :meth:`async_step_zeroconf`. Users who prefer to enter the IP
manually can still do so via :meth:`async_step_user`.

This module deliberately does **not** scan the LAN for devices. Issuing
unsolicited HTTP requests against every IP on the network is not an acceptable
discovery pattern for a Home Assistant integration.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import (
    CONF_DEVICE_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


class CannotConnect(Exception):
    """Raised when the device cannot be reached."""


class UnknownError(Exception):
    """Raised on an unexpected error while talking to the device."""


async def _async_fetch_device_info(
    hass: HomeAssistant, host: str, port: int
) -> dict[str, Any]:
    """Fetch ``/info`` from the device and return ``{title, device_id, capabilities}``.

    Retries up to three times with short back-off. Raises :class:`CannotConnect`
    on connection / protocol issues and :class:`UnknownError` on anything else.
    """
    url = f"http://{host}:{port}/info"
    session = async_get_clientsession(hass)
    last_error: Exception | None = None

    for attempt in range(1, 4):
        _LOGGER.debug("Fetching device info from %s (attempt %d/3)", url, attempt)
        try:
            async with asyncio.timeout(10):
                async with session.get(url) as response:
                    if response.status != 200:
                        raise CannotConnect(
                            f"Device returned HTTP {response.status}"
                        )
                    info = await response.json()
                    if not isinstance(info, dict) or "device" not in info:
                        raise CannotConnect("Invalid /info response")
                    device = info["device"]
                    device_id = device.get("id")
                    if not device_id:
                        raise CannotConnect("Device did not report an id")
                    return {
                        "title": device.get("name", DEFAULT_NAME),
                        "device_id": device_id,
                        "capabilities": info.get("capabilities", {}),
                    }
        except CannotConnect as err:
            last_error = err
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.debug("Connection attempt %d failed: %s", attempt, err)
            last_error = CannotConnect(str(err))
        except Exception as err:  # noqa: BLE001 - surface as UnknownError
            _LOGGER.exception("Unexpected error fetching %s", url)
            raise UnknownError(str(err)) from err

        if attempt < 3:
            await asyncio.sleep(1)

    assert last_error is not None
    raise last_error


class PicoWNeoPixelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for PicoW NeoPixel devices."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize transient state for a single flow."""
        self._discovered_host: str | None = None
        self._discovered_port: int = DEFAULT_PORT
        self._discovered_device_id: str | None = None
        self._discovered_name: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual host/port entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            try:
                info = await _async_fetch_device_info(self.hass, host, port)
            except CannotConnect:
                errors["base"] = ERROR_CANNOT_CONNECT
            except UnknownError:
                errors["base"] = ERROR_UNKNOWN
            else:
                await self.async_set_unique_id(info["device_id"])
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: host, CONF_PORT: port}
                )
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_NAME: info["title"],
                        CONF_DEVICE_ID: info["device_id"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle a device announcing itself via zeroconf/mDNS."""
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT

        # Zeroconf properties arrive as ``dict[str, str | None]``.
        properties: dict[str, Any] = dict(discovery_info.properties or {})
        device_id = properties.get("id") or properties.get("device_id")
        name = properties.get("name")

        _LOGGER.debug(
            "Zeroconf discovery: host=%s port=%s properties=%s",
            host,
            port,
            properties,
        )

        if not device_id:
            # The device should publish its id as a TXT record, but fall back
            # to a single /info call if it doesn't.
            try:
                info = await _async_fetch_device_info(self.hass, host, port)
            except (CannotConnect, UnknownError):
                return self.async_abort(reason="cannot_connect")
            device_id = info["device_id"]
            name = name or info["title"]

        await self.async_set_unique_id(str(device_id))
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: host, CONF_PORT: port}
        )

        friendly_name = name or DEFAULT_NAME
        self._discovered_host = host
        self._discovered_port = port
        self._discovered_device_id = str(device_id)
        self._discovered_name = friendly_name

        # Surfaces the friendly name in the "Discovered" card.
        self.context["title_placeholders"] = {"name": friendly_name}

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask the user to confirm adding a zeroconf-discovered device."""
        assert self._discovered_host is not None
        assert self._discovered_device_id is not None

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _async_fetch_device_info(
                    self.hass, self._discovered_host, self._discovered_port
                )
            except CannotConnect:
                errors["base"] = ERROR_CANNOT_CONNECT
            except UnknownError:
                errors["base"] = ERROR_UNKNOWN
            else:
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_HOST: self._discovered_host,
                        CONF_PORT: self._discovered_port,
                    }
                )
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: self._discovered_host,
                        CONF_PORT: self._discovered_port,
                        CONF_NAME: info["title"],
                        CONF_DEVICE_ID: info["device_id"],
                    },
                )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "name": self._discovered_name or DEFAULT_NAME,
                "host": self._discovered_host,
            },
            errors=errors,
        )
