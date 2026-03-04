"""Constants for the PicoW NeoPixel integration."""
from typing import Final

DOMAIN: Final = "picow_neopixel"

# Configuration
CONF_DEVICE_ID: Final = "device_id"

# Defaults
DEFAULT_NAME: Final = "PicoW NeoPixel"
DEFAULT_SCAN_INTERVAL: Final = 10  # seconds
DEFAULT_PORT: Final = 80

# API endpoints
API_STATE: Final = "/state"
API_INFO: Final = "/info"
API_CONTROL: Final = "/control"

# mDNS service type
MDNS_SERVICE_TYPE: Final = "_picow-neopixel._tcp.local."

# Defaults for animation
DEFAULT_SPEED: Final = 50

# Attributes
ATTR_EFFECT: Final = "effect"
ATTR_SPEED: Final = "speed"

# Effects
EFFECT_STATIC: Final = "static"
EFFECT_RAINBOW: Final = "rainbow"
EFFECT_FADE: Final = "fade"
EFFECT_CHASE: Final = "chase"
EFFECT_BREATHING: Final = "breathing"
EFFECT_TWINKLE: Final = "twinkle"
EFFECT_SCANNER: Final = "scanner"
EFFECT_STROBE: Final = "strobe"
EFFECT_COMET: Final = "comet"
EFFECT_CHASE_MIDDLE_OUT: Final = "chase_middle_out"
EFFECT_CHASE_OUTSIDE_IN: Final = "chase_outside_in"
EFFECT_FILL_MIDDLE_OUT: Final = "fill_middle_out"
EFFECT_FILL_OUTSIDE_IN: Final = "fill_outside_in"
EFFECT_UNFILL_MIDDLE_OUT: Final = "unfill_middle_out"
EFFECT_UNFILL_OUTSIDE_IN: Final = "unfill_outside_in"
EFFECT_TRANSITION_MIDDLE_OUT: Final = "transition_middle_out"
EFFECT_TRANSITION_OUTSIDE_IN: Final = "transition_outside_in"
EFFECT_TRANSITION_FADE: Final = "transition_fade"

EFFECT_LIST: Final = [
    EFFECT_STATIC,
    EFFECT_RAINBOW,
    EFFECT_FADE,
    EFFECT_CHASE,
    EFFECT_BREATHING,
    EFFECT_TWINKLE,
    EFFECT_SCANNER,
    EFFECT_STROBE,
    EFFECT_COMET,
    EFFECT_CHASE_MIDDLE_OUT,
    EFFECT_CHASE_OUTSIDE_IN,
    EFFECT_FILL_MIDDLE_OUT,
    EFFECT_FILL_OUTSIDE_IN,
    EFFECT_UNFILL_MIDDLE_OUT,
    EFFECT_UNFILL_OUTSIDE_IN,
    EFFECT_TRANSITION_MIDDLE_OUT,
    EFFECT_TRANSITION_OUTSIDE_IN,
    EFFECT_TRANSITION_FADE,
]

# One-shot effects (all effects that can be played once)
ONE_SHOT_EFFECT_LIST: Final = [
    EFFECT_RAINBOW,
    EFFECT_FADE,
    EFFECT_CHASE,
    EFFECT_BREATHING,
    EFFECT_TWINKLE,
    EFFECT_SCANNER,
    EFFECT_STROBE,
    EFFECT_COMET,
    EFFECT_CHASE_MIDDLE_OUT,
    EFFECT_CHASE_OUTSIDE_IN,
    EFFECT_FILL_MIDDLE_OUT,
    EFFECT_FILL_OUTSIDE_IN,
    EFFECT_UNFILL_MIDDLE_OUT,
    EFFECT_UNFILL_OUTSIDE_IN,
    EFFECT_TRANSITION_MIDDLE_OUT,
    EFFECT_TRANSITION_OUTSIDE_IN,
    EFFECT_TRANSITION_FADE,
]

DEFAULT_ONE_SHOT_EFFECT: Final = EFFECT_CHASE

# Transition modes for color changes
TRANSITION_NONE: Final = "none"
TRANSITION_MIDDLE_OUT: Final = "transition_middle_out"
TRANSITION_OUTSIDE_IN: Final = "transition_outside_in"
TRANSITION_FADE: Final = "transition_fade"

TRANSITION_MODE_LIST: Final = [
    TRANSITION_NONE,
    TRANSITION_MIDDLE_OUT,
    TRANSITION_OUTSIDE_IN,
    TRANSITION_FADE,
]

DEFAULT_TRANSITION_MODE: Final = TRANSITION_NONE

# Error messages
ERROR_CANNOT_CONNECT: Final = "cannot_connect"
ERROR_UNKNOWN: Final = "unknown"
ERROR_TIMEOUT: Final = "timeout"
