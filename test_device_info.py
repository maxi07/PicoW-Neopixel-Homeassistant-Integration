"""Host-side tests for PicoW firmware version metadata without Home Assistant installed."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).parent / "custom_components" / "picow_neopixel"


def load_device_info():
    """Load only the metadata module with minimal HA import stubs."""
    ha = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = type("ConfigEntry", (), {})
    const = types.ModuleType("homeassistant.const")
    const.CONF_NAME = "name"
    helpers = types.ModuleType("homeassistant.helpers")
    entity = types.ModuleType("homeassistant.helpers.entity")
    entity.DeviceInfo = dict
    package = types.ModuleType("custom_components")
    integration = types.ModuleType("custom_components.picow_neopixel")
    integration.__path__ = [str(ROOT)]
    stub_modules = {
        "homeassistant": ha,
        "homeassistant.config_entries": config_entries,
        "homeassistant.const": const,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.entity": entity,
        "custom_components": package,
        "custom_components.picow_neopixel": integration,
    }
    with patch.dict(sys.modules, stub_modules):
        name = "custom_components.picow_neopixel.device_info"
        spec = importlib.util.spec_from_file_location(name, ROOT / "device_info.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class DeviceInfoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_device_info()
        cls.entry = types.SimpleNamespace(data={"device_id": "pico-001", "name": "Strip"})

    def test_device_version_from_firmware_info(self):
        device = self.module.build_device_info(self.entry, {"version": "1.2"})
        self.assertEqual(device["sw_version"], "1.2")
        self.assertEqual(device["name"], "Strip")
        self.assertEqual(device["identifiers"], {("picow_neopixel", "pico-001")})

    def test_version_reflects_new_info_after_reconnect(self):
        old = self.module.build_device_info(self.entry, {"version": "1.2"})
        new = self.module.build_device_info(self.entry, {"version": "1.3"})
        self.assertEqual(old["sw_version"], "1.2")
        self.assertEqual(new["sw_version"], "1.3")

    def test_missing_or_invalid_version_does_not_claim_1_1(self):
        for info in (None, {}, {"version": ""}, {"version": 12}):
            with self.subTest(info=info):
                device = self.module.build_device_info(self.entry, info)
                self.assertNotIn("sw_version", device)


if __name__ == "__main__":
    unittest.main()
