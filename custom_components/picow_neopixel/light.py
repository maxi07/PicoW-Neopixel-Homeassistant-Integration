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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_ID,
    DEFAULT_SPEED,
    DOMAIN,
    EFFECT_LIST,
    EFFECT_PROGRESS_BAR,
    EFFECT_STATIC,
    TRANSITION_NONE,
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
    _attr_icon = "mdi:led-strip-variant"
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

        # Optimistic local state — UI reads from here for instant feedback
        # Initialize from coordinator data if already available (update_before_add=True)
        self._state_is_on: bool = False
        self._state_brightness: int = 255
        self._state_rgb_color: tuple[int, int, int] = (255, 255, 255)
        self._state_effect: str | None = None

        if coordinator.data:
            try:
                state = coordinator.data["state"]
                self._state_is_on = state["is_on"]
                self._state_brightness = int((state["brightness"] / 100) * 255)
                color = state["color"]
                self._state_rgb_color = (color["r"], color["g"], color["b"])
                effect = state.get("effect")
                self._state_effect = effect if effect != EFFECT_STATIC else None
            except (KeyError, TypeError, ValueError):
                pass

    @callback
    def _handle_coordinator_update(self) -> None:
        """Sync local state from coordinator (device polling)."""
        try:
            state = self.coordinator.data["state"]
            self._state_is_on = state["is_on"]
            self._state_brightness = int((state["brightness"] / 100) * 255)
            color = state["color"]
            self._state_rgb_color = (color["r"], color["g"], color["b"])
            effect = state.get("effect")
            self._state_effect = effect if effect != EFFECT_STATIC else None
        except (KeyError, TypeError, ValueError):
            pass
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and super().available

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._state_is_on

    @property
    def brightness(self) -> int:
        """Return the brightness of the light (0-255)."""
        return self._state_brightness

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the rgb color value."""
        return self._state_rgb_color

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        return self._state_effect

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        command: dict[str, Any] = {"power": "on"}

        # --- Optimistic state update (immediate UI feedback) ---
        self._state_is_on = True

        # Handle brightness
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            # Convert from 0-255 to 0-100
            brightness_percent = int((brightness / 255) * 100)
            command["brightness"] = max(1, brightness_percent)
            self._state_brightness = brightness

        # Handle color
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            color_dict = {
                "r": rgb[0],
                "g": rgb[1],
                "b": rgb[2],
            }
            self._state_rgb_color = (rgb[0], rgb[1], rgb[2])

            # Check if a transition mode is active and this is a color-only change
            transition_mode = self.coordinator.transition_mode
            if (
                transition_mode != TRANSITION_NONE
                and ATTR_EFFECT not in kwargs
            ):
                # Play transition animation instead of immediate color change
                # First apply brightness if also provided
                if "brightness" in command:
                    await self.coordinator.async_send_command(
                        {"power": "on", "brightness": command["brightness"]}
                    )

                self._state_effect = None
                self.async_write_ha_state()

                try:
                    await self.coordinator.async_play_once(
                        effect=transition_mode,
                        color=color_dict,
                    )
                    # The device response contains the mid-transition state
                    # (old color). Patch coordinator data so the UI shows the
                    # target color immediately.
                    if self.coordinator.data and "state" in self.coordinator.data:
                        self.coordinator.data["state"]["color"] = color_dict
                        self.coordinator.data["state"]["effect"] = "static"
                    self.async_write_ha_state()
                    _LOGGER.debug(
                        "Transition color change: %s with %s",
                        color_dict, transition_mode,
                    )
                except Exception as err:
                    _LOGGER.error("Failed transition color change: %s", err)
                    raise
                return

            command["color"] = color_dict

        # Handle effect
        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            command["effect"] = effect
            # Use current speed from device state
            try:
                command["speed"] = self.coordinator.data["state"]["speed"]
            except (KeyError, TypeError):
                command["speed"] = DEFAULT_SPEED
            self._state_effect = effect if effect != EFFECT_STATIC else None

            # When switching to progress bar, include the current progress value
            # so the device can display it immediately
            if effect == EFFECT_PROGRESS_BAR:
                try:
                    command["progress"] = self.coordinator.data["state"].get(
                        "progress", 0
                    )
                except (KeyError, TypeError):
                    command["progress"] = 0

        # Push state to HA immediately — before the network round-trip
        self.async_write_ha_state()

        try:
            await self.coordinator.async_send_command(command)
            _LOGGER.debug("Turn on command sent: %s", command)
        except Exception as err:
            _LOGGER.error("Failed to turn on light: %s", err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        command = {"power": "off"}

        # Optimistic update
        self._state_is_on = False
        self.async_write_ha_state()

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
