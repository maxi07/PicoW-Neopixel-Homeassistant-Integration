"""Host-side tests for PicoW firmware version metadata without Home Assistant installed."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


ROOT = pathlib.Path(__file__).parent / "custom_components" / "picow_neopixel"


def load_device_info():
    """Load only the metadata module with minimal HA import stubs."""
    ha = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = type("ConfigEntry", (), {})
    const = types.ModuleType("homeassistant.const")
    const.CONF_NAME = "name"
    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = type("HomeAssistant", (), {})
    core.callback = lambda func: func
    helpers = types.ModuleType("homeassistant.helpers")
    device_registry = types.ModuleType("homeassistant.helpers.device_registry")
    device_registry.async_get = Mock()
    helpers.device_registry = device_registry
    entity = types.ModuleType("homeassistant.helpers.entity")
    entity.DeviceInfo = dict
    package = types.ModuleType("custom_components")
    integration = types.ModuleType("custom_components.picow_neopixel")
    integration.__path__ = [str(ROOT)]
    stub_modules = {
        "homeassistant": ha,
        "homeassistant.config_entries": config_entries,
        "homeassistant.const": const,
        "homeassistant.core": core,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.device_registry": device_registry,
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
        for info in (None, {}, {"version": None}, {"version": ""}, {"version": " "}, {"version": 12}):
            with self.subTest(info=info):
                device = self.module.build_device_info(self.entry, info)
                self.assertNotIn("sw_version", device)

    def test_missing_or_invalid_version_clears_existing_registry_value(self):
        for previous in ("1.1", "1.3"):
            for info in (None, {}, {"version": None}, {"version": ""}, {"version": " "}, {"version": 12}):
                with self.subTest(previous=previous, info=info):
                    registry = Mock()
                    device = types.SimpleNamespace(id="device-001", sw_version=previous)
                    registry.async_get_device.return_value = device
                    registry.async_update_device.side_effect = (
                        lambda device_id, **changes: setattr(device, "sw_version", changes["sw_version"])
                    )
                    with patch.object(self.module.dr, "async_get", return_value=registry):
                        self.module.async_update_device_firmware_version(Mock(), self.entry, info)
                    registry.async_get_device.assert_called_once_with(
                        identifiers={("picow_neopixel", "pico-001")}
                    )
                    registry.async_update_device.assert_called_once_with(
                        "device-001", sw_version=None
                    )
                    self.assertIsNone(device.sw_version)

    def test_valid_version_updates_existing_registry_value(self):
        registry = Mock()
        registry.async_get_device.return_value = types.SimpleNamespace(
            id="device-001", sw_version="1.1"
        )
        with patch.object(self.module.dr, "async_get", return_value=registry):
            self.module.async_update_device_firmware_version(
                Mock(), self.entry, {"version": "1.3"}
            )
        registry.async_update_device.assert_called_once_with(
            "device-001", sw_version="1.3"
        )

    def test_new_device_does_not_require_registry_update(self):
        registry = Mock()
        registry.async_get_device.return_value = None
        with patch.object(self.module.dr, "async_get", return_value=registry):
            self.module.async_update_device_firmware_version(Mock(), self.entry, {})
        registry.async_update_device.assert_not_called()

    def test_unchanged_version_does_not_require_registry_update(self):
        for version in (None, "1.3"):
            with self.subTest(version=version):
                registry = Mock()
                registry.async_get_device.return_value = types.SimpleNamespace(
                    id="device-001", sw_version=version
                )
                with patch.object(self.module.dr, "async_get", return_value=registry):
                    self.module.async_update_device_firmware_version(
                        Mock(), self.entry, {"version": version}
                    )
                registry.async_update_device.assert_not_called()


if __name__ == "__main__":
    unittest.main()
