"""Select platform for PicoW NeoPixel integration (One-Shot Effect Selector)."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_ID,
    DOMAIN,
    ONE_SHOT_EFFECT_LIST,
    TRANSITION_MODE_LIST,
)
from .coordinator import PicoWNeoPixelCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PicoW NeoPixel select entities from a config entry."""
    coordinator: PicoWNeoPixelCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            PicoWNeoPixelOneShotEffectSelect(coordinator, entry),
            PicoWNeoPixelTransitionModeSelect(coordinator, entry),
        ],
        update_before_add=True,
    )


class PicoWNeoPixelOneShotEffectSelect(
    CoordinatorEntity[PicoWNeoPixelCoordinator], SelectEntity
):
    """Select entity for choosing which effect to play once."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:animation-play"
    _attr_translation_key = "one_shot_effect"

    def __init__(
        self,
        coordinator: PicoWNeoPixelCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the one-shot effect select."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_one_shot_effect"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data.get(CONF_NAME, "PicoW NeoPixel"),
            manufacturer="Maximilian Krause",
            model="PicoW NeoPixel Controller",
            sw_version="1.0",
        )
        self._attr_options = ONE_SHOT_EFFECT_LIST
        self._attr_current_option = coordinator.one_shot_effect

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and super().available

    @property
    def current_option(self) -> str:
        """Return the currently selected one-shot effect."""
        return self.coordinator.one_shot_effect

    async def async_select_option(self, option: str) -> None:
        """Change the selected one-shot effect."""
        self.coordinator.one_shot_effect = option
        self.async_write_ha_state()
        _LOGGER.debug("One-shot effect selected: %s", option)


class PicoWNeoPixelTransitionModeSelect(
    CoordinatorEntity[PicoWNeoPixelCoordinator], SelectEntity
):
    """Select entity for choosing the transition mode for color changes."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:transition-masked"
    _attr_translation_key = "transition_mode"

    def __init__(
        self,
        coordinator: PicoWNeoPixelCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the transition mode select."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_transition_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data.get(CONF_NAME, "PicoW NeoPixel"),
            manufacturer="Maximilian Krause",
            model="PicoW NeoPixel Controller",
            sw_version="1.0",
        )
        self._attr_options = TRANSITION_MODE_LIST
        self._attr_current_option = coordinator.transition_mode

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and super().available

    @property
    def current_option(self) -> str:
        """Return the currently selected transition mode."""
        return self.coordinator.transition_mode

    async def async_select_option(self, option: str) -> None:
        """Change the selected transition mode."""
        self.coordinator.transition_mode = option
        self.async_write_ha_state()
        _LOGGER.debug("Transition mode selected: %s", option)
