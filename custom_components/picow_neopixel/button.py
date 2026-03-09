"""Button platform for PicoW NeoPixel integration (One-Shot Effect Trigger)."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, DOMAIN
from .coordinator import PicoWNeoPixelCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PicoW NeoPixel play-once button from a config entry."""
    coordinator: PicoWNeoPixelCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [PicoWNeoPixelPlayOnceButton(coordinator, entry)],
        update_before_add=True,
    )


class PicoWNeoPixelPlayOnceButton(
    CoordinatorEntity[PicoWNeoPixelCoordinator], ButtonEntity
):
    """Button to trigger a one-shot effect playback."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:play-circle-outline"
    _attr_translation_key = "play_effect_once"

    def __init__(
        self,
        coordinator: PicoWNeoPixelCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the play-once button."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_play_effect_once"
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

    async def async_press(self) -> None:
        """Handle the button press — play the selected one-shot effect."""
        effect = self.coordinator.one_shot_effect
        _LOGGER.debug("Playing one-shot effect: %s", effect)
        try:
            await self.coordinator.async_play_once(effect)
        except Exception as err:
            _LOGGER.error("Failed to play one-shot effect: %s", err)
            raise
