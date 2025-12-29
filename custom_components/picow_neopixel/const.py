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

EFFECT_LIST: Final = [
    EFFECT_STATIC,
    EFFECT_RAINBOW,
    EFFECT_FADE,
    EFFECT_CHASE,
    EFFECT_BREATHING,
    EFFECT_TWINKLE,
    EFFECT_SCANNER,
    EFFECT_STROBE,
]

# Error messages
ERROR_CANNOT_CONNECT: Final = "cannot_connect"
ERROR_UNKNOWN: Final = "unknown"
ERROR_TIMEOUT: Final = "timeout"
