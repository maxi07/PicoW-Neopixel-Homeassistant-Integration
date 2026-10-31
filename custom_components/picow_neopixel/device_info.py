"""Shared device metadata for PicoW NeoPixel entities."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import DeviceInfo

from .const import CONF_DEVICE_ID, DEFAULT_NAME, DOMAIN

DEVICE_MANUFACTURER = "Maximilian Krause"
DEVICE_MODEL = "PicoW NeoPixel Controller"
def build_device_info(entry: ConfigEntry, info: dict[str, Any] | None = None) -> DeviceInfo:
    """Build device metadata using the version reported by the firmware."""
    version = info.get("version") if isinstance(info, dict) else None
    device = DeviceInfo(
        identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
        name=entry.data.get(CONF_NAME, DEFAULT_NAME),
        manufacturer=DEVICE_MANUFACTURER,
        model=DEVICE_MODEL,
    )
    if isinstance(version, str) and version.strip():
        device["sw_version"] = version
    return device
