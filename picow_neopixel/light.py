"""Light platform for PicoW NeoPixel integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_ID,
    DOMAIN,
    EFFECT_LIST,
    EFFECT_STATIC,
)
from .coordinator import PicoWNeoPixelCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PicoW NeoPixel light from a config entry."""
    coordinator: PicoWNeoPixelCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [PicoWNeoPixelLight(coordinator, entry)],
        update_before_add=True,
    )


class PicoWNeoPixelLight(CoordinatorEntity[PicoWNeoPixelCoordinator], LightEntity):
    """Representation of a PicoW NeoPixel light."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(
        self,
        coordinator: PicoWNeoPixelCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        
        self._attr_unique_id = entry.data[CONF_DEVICE_ID]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data.get(CONF_NAME, "PicoW NeoPixel"),
            manufacturer="Maximilian Krause",
            model="PicoW NeoPixel Controller",
            sw_version="1.0",
        )
        
        self._attr_effect_list = EFFECT_LIST.copy()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and super().available

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        try:
            return self.coordinator.data["state"]["is_on"]
        except (KeyError, TypeError):
            return False

    @property
    def brightness(self) -> int:
        """Return the brightness of the light (0-255)."""
        try:
            # Convert from 0-100 to 0-255
            brightness_percent = self.coordinator.data["state"]["brightness"]
            return int((brightness_percent / 100) * 255)
        except (KeyError, TypeError, ValueError):
            return 255

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the rgb color value."""
        try:
            color = self.coordinator.data["state"]["color"]
            return (color["r"], color["g"], color["b"])
        except (KeyError, TypeError):
            return (255, 255, 255)

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        try:
            effect = self.coordinator.data["state"]["effect"]
            return effect if effect != EFFECT_STATIC else None
        except (KeyError, TypeError):
            return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        command: dict[str, Any] = {"power": "on"}

        # Handle brightness
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            # Convert from 0-255 to 0-100
            brightness_percent = int((brightness / 255) * 100)
            command["brightness"] = max(1, brightness_percent)

        # Handle color
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            command["color"] = {
                "r": rgb[0],
                "g": rgb[1],
                "b": rgb[2],
            }

        # Handle effect
        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            command["effect"] = effect
            # Default speed for effects
            command["speed"] = 50

        try:
            await self.coordinator.async_send_command(command)
            _LOGGER.debug("Turn on command sent: %s", command)
        except Exception as err:
            _LOGGER.error("Failed to turn on light: %s", err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        command = {"power": "off"}

        try:
            await self.coordinator.async_send_command(command)
            _LOGGER.debug("Turn off command sent")
        except Exception as err:
            _LOGGER.error("Failed to turn off light: %s", err)
            raise

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        try:
            info = self.coordinator.data.get("info", {})
            capabilities = info.get("capabilities", {})
            device = info.get("device", {})
            
            attributes = {
                "device_id": device.get("id"),
                "ip_address": device.get("ip"),
                "mac_address": device.get("mac"),
                "num_leds": capabilities.get("num_leds"),
            }
            
            return {k: v for k, v in attributes.items() if v is not None}
        except (KeyError, TypeError):
            return {}
