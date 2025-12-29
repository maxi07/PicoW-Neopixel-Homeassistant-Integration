"""Provides device actions for PicoW NeoPixel."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_TYPE,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import selector

from .const import DOMAIN

# Action types
ACTION_TURN_ON = "turn_on"
ACTION_TURN_OFF = "turn_off"
ACTION_SET_BRIGHTNESS = "set_brightness"
ACTION_SET_COLOR = "set_color"
ACTION_SET_EFFECT = "set_effect"

# Action schemas
ACTION_TURN_ON_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): ACTION_TURN_ON,
        vol.Required(ATTR_ENTITY_ID): cv.entity_id_or_uuid,
    }
)

ACTION_TURN_OFF_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): ACTION_TURN_OFF,
        vol.Required(ATTR_ENTITY_ID): cv.entity_id_or_uuid,
    }
)

ACTION_SET_BRIGHTNESS_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): ACTION_SET_BRIGHTNESS,
        vol.Required(ATTR_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required("brightness"): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    }
)

ACTION_SET_COLOR_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): ACTION_SET_COLOR,
        vol.Required(ATTR_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required("rgb_color"): vol.All(
            vol.ExactSequence([cv.byte, cv.byte, cv.byte]),
            vol.Coerce(tuple),
        ),
    }
)

ACTION_SET_EFFECT_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): ACTION_SET_EFFECT,
        vol.Required(ATTR_ENTITY_ID): cv.entity_id_or_uuid,
        vol.Required("effect"): cv.string,
    }
)

ACTION_SCHEMA = vol.Any(
    ACTION_TURN_ON_SCHEMA,
    ACTION_TURN_OFF_SCHEMA,
    ACTION_SET_BRIGHTNESS_SCHEMA,
    ACTION_SET_COLOR_SCHEMA,
    ACTION_SET_EFFECT_SCHEMA,
)


async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device actions for PicoW NeoPixel devices."""
    registry = er.async_get(hass)
    actions = []

    # Get all entities for this device
    entities = er.async_entries_for_device(registry, device_id)

    for entry in entities:
        if entry.domain != LIGHT_DOMAIN:
            continue

        base_action = {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            ATTR_ENTITY_ID: entry.entity_id,
        }

        # Add turn on action
        actions.append({**base_action, CONF_TYPE: ACTION_TURN_ON})

        # Add turn off action
        actions.append({**base_action, CONF_TYPE: ACTION_TURN_OFF})

        # Add set brightness action
        actions.append({**base_action, CONF_TYPE: ACTION_SET_BRIGHTNESS})

        # Add set color action
        actions.append({**base_action, CONF_TYPE: ACTION_SET_COLOR})

        # Add set effect action
        actions.append({**base_action, CONF_TYPE: ACTION_SET_EFFECT})

    return actions


async def async_call_action_from_config(
    hass: HomeAssistant, config: ConfigType, variables: dict, context: Context | None
) -> None:
    """Execute a device action."""
    action_type = config[CONF_TYPE]
    entity_id = config[ATTR_ENTITY_ID]

    service_data = {ATTR_ENTITY_ID: entity_id}

    if action_type == ACTION_TURN_ON:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            service_data,
            blocking=True,
            context=context,
        )
    elif action_type == ACTION_TURN_OFF:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_off",
            service_data,
            blocking=True,
            context=context,
        )
    elif action_type == ACTION_SET_BRIGHTNESS:
        service_data["brightness"] = config["brightness"]
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            service_data,
            blocking=True,
            context=context,
        )
    elif action_type == ACTION_SET_COLOR:
        service_data["rgb_color"] = config["rgb_color"]
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            service_data,
            blocking=True,
            context=context,
        )
    elif action_type == ACTION_SET_EFFECT:
        service_data["effect"] = config["effect"]
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            service_data,
            blocking=True,
            context=context,
        )


async def async_get_action_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """List action capabilities."""
    action_type = config[CONF_TYPE]

    if action_type == ACTION_SET_BRIGHTNESS:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required("brightness", default=255): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=255)
                    ),
                }
            )
        }

    if action_type == ACTION_SET_COLOR:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required("rgb_color", default=[255, 255, 255]): selector.ColorRGBSelector(),
                }
            )
        }

    if action_type == ACTION_SET_EFFECT:
        # Get the entity to read its effect list dynamically
        entity_id = config.get(ATTR_ENTITY_ID)
        if entity_id:
            state = hass.states.get(entity_id)
            if state and state.attributes.get("effect_list"):
                effect_list = state.attributes["effect_list"]
                return {
                    "extra_fields": vol.Schema(
                        {
                            vol.Required("effect"): vol.In(effect_list),
                        }
                    )
                }

        # Fallback if entity not found or no effect list
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required("effect"): cv.string,
                }
            )
        }

    return {}
