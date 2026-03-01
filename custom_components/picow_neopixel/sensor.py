"""Sensor platform for PicoW NeoPixel integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, DOMAIN
from .coordinator import PicoWNeoPixelCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get a nested dict value."""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key, default)
    return data


class PicoWNeoPixelSensorBase(
    CoordinatorEntity[PicoWNeoPixelCoordinator], SensorEntity
):
    """Base class for PicoW NeoPixel sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PicoWNeoPixelCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data.get(CONF_NAME, "PicoW NeoPixel"),
            manufacturer="Maximilian Krause",
            model="PicoW NeoPixel Controller",
            sw_version="1.0",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and super().available


# ---------- Estimated Current ----------

class EstimatedCurrentSensor(PicoWNeoPixelSensorBase):
    """Estimated current draw in mA."""

    _attr_name = "Estimated Current"
    _attr_icon = "mdi:flash"
    _attr_native_unit_of_measurement = "mA"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "estimated_current")

    @property
    def native_value(self) -> int | None:
        return _get_nested(self.coordinator.data, "info", "diagnostics", "estimated_current_ma")


# ---------- LED Count ----------

class LedCountSensor(PicoWNeoPixelSensorBase):
    """Number of LEDs on the strip."""

    _attr_name = "LED Count"
    _attr_icon = "mdi:led-strip"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "led_count")

    @property
    def native_value(self) -> int | None:
        return _get_nested(self.coordinator.data, "info", "capabilities", "num_leds")


# ---------- Free Memory ----------

class FreeMemorySensor(PicoWNeoPixelSensorBase):
    """Free memory on the device."""

    _attr_name = "Free Memory"
    _attr_icon = "mdi:memory"
    _attr_native_unit_of_measurement = "B"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "free_memory")

    @property
    def native_value(self) -> int | None:
        return _get_nested(self.coordinator.data, "info", "diagnostics", "free_memory")


# ---------- Wi-Fi Signal Strength (%) ----------

class WifiSignalPercentSensor(PicoWNeoPixelSensorBase):
    """Wi-Fi signal strength in percent."""

    _attr_name = "Wi-Fi Signal Strength"
    _attr_icon = "mdi:wifi"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "wifi_signal_percent")

    @property
    def native_value(self) -> int | None:
        return _get_nested(self.coordinator.data, "info", "diagnostics", "wifi_signal_percent")


# ---------- Wi-Fi Signal Strength (RSSI) ----------

class WifiRssiSensor(PicoWNeoPixelSensorBase):
    """Wi-Fi signal strength in dBm."""

    _attr_name = "Wi-Fi RSSI"
    _attr_icon = "mdi:wifi"
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "wifi_rssi")

    @property
    def native_value(self) -> int | None:
        return _get_nested(self.coordinator.data, "info", "diagnostics", "wifi_rssi")


# ---------- Wi-Fi Channel ----------

class WifiChannelSensor(PicoWNeoPixelSensorBase):
    """Wi-Fi channel."""

    _attr_name = "Wi-Fi Channel"
    _attr_icon = "mdi:wifi-cog"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "wifi_channel")

    @property
    def native_value(self) -> int | None:
        return _get_nested(self.coordinator.data, "info", "diagnostics", "wifi_channel")


# ---------- Wi-Fi BSSID ----------

class WifiBssidSensor(PicoWNeoPixelSensorBase):
    """Wi-Fi BSSID of connected access point."""

    _attr_name = "Wi-Fi BSSID"
    _attr_icon = "mdi:access-point-network"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "wifi_bssid")

    @property
    def native_value(self) -> str | None:
        return _get_nested(self.coordinator.data, "info", "diagnostics", "wifi_bssid")


# ---------- IP Address ----------

class IpAddressSensor(PicoWNeoPixelSensorBase):
    """IP address of the device."""

    _attr_name = "IP Address"
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "ip_address")

    @property
    def native_value(self) -> str | None:
        return _get_nested(self.coordinator.data, "info", "device", "ip")


# ---------- Platform setup ----------

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PicoW NeoPixel sensors from a config entry."""
    coordinator: PicoWNeoPixelCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            EstimatedCurrentSensor(coordinator, entry),
            LedCountSensor(coordinator, entry),
            FreeMemorySensor(coordinator, entry),
            WifiSignalPercentSensor(coordinator, entry),
            WifiRssiSensor(coordinator, entry),
            WifiChannelSensor(coordinator, entry),
            WifiBssidSensor(coordinator, entry),
            IpAddressSensor(coordinator, entry),
        ],
        update_before_add=True,
    )
