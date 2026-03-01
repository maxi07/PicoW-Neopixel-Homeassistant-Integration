"""Number platform for PicoW NeoPixel integration (Animation Speed)."""
from __future__ import annotations

import logging

from homeassistant.components.number import (
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_ID,
    DEFAULT_SPEED,
    DOMAIN,
)
from .coordinator import PicoWNeoPixelCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PicoW NeoPixel animation speed number from a config entry."""
    coordinator: PicoWNeoPixelCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [PicoWNeoPixelSpeedNumber(coordinator, entry)],
        update_before_add=True,
    )


class PicoWNeoPixelSpeedNumber(
    CoordinatorEntity[PicoWNeoPixelCoordinator], NumberEntity
):
    """Representation of the animation speed slider for PicoW NeoPixel."""

    _attr_has_entity_name = True
    _attr_name = "Animationsgeschwindigkeit"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = 1
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: PicoWNeoPixelCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the animation speed number."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_animation_speed"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data.get(CONF_NAME, "PicoW NeoPixel"),
            manufacturer="Maximilian Krause",
            model="PicoW NeoPixel Controller",
            sw_version="1.0",
        )

        # Optimistic local state
        self._state_speed: float = DEFAULT_SPEED

        if coordinator.data:
            try:
                self._state_speed = coordinator.data["state"]["speed"]
            except (KeyError, TypeError):
                pass

    @callback
    def _handle_coordinator_update(self) -> None:
        """Sync local state from coordinator (device polling)."""
        try:
            self._state_speed = self.coordinator.data["state"]["speed"]
        except (KeyError, TypeError):
            pass
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and super().available

    @property
    def native_value(self) -> float:
        """Return the current animation speed."""
        return self._state_speed

    async def async_set_native_value(self, value: float) -> None:
        """Set the animation speed."""
        speed = int(value)

        # Optimistic update
        self._state_speed = speed
        self.async_write_ha_state()

        try:
            await self.coordinator.async_send_command({"speed": speed})
            _LOGGER.debug("Animation speed set to %s%%", speed)
        except Exception as err:
            _LOGGER.error("Failed to set animation speed: %s", err)
            raise
