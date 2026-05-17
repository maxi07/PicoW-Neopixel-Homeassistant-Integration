"""Shared device metadata for PicoW NeoPixel entities."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import DeviceInfo

from .const import CONF_DEVICE_ID, DEFAULT_NAME, DOMAIN

DEVICE_MANUFACTURER = "Maximilian Krause"
DEVICE_MODEL = "PicoW NeoPixel Controller"
DEVICE_SW_VERSION = "1.1"


def build_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Build a consistent DeviceInfo object for all entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
        name=entry.data.get(CONF_NAME, DEFAULT_NAME),
        manufacturer=DEVICE_MANUFACTURER,
        model=DEVICE_MODEL,
        sw_version=DEVICE_SW_VERSION,
    )
