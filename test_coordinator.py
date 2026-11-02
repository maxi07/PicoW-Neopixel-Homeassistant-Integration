"""Host-side polling tests without Home Assistant installed."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

import aiohttp


ROOT = pathlib.Path(__file__).parent / "custom_components" / "picow_neopixel"


def load_coordinator():
    """Load the coordinator with minimal HA import stubs."""
    class CoordinatorStub:
        def __init__(self, *args, **kwargs):
            pass

    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = type("ConfigEntry", (), {})
    const = types.ModuleType("homeassistant.const")
    const.CONF_HOST = "host"
    const.CONF_PORT = "port"
    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = type("HomeAssistant", (), {})
    client = types.ModuleType("homeassistant.helpers.aiohttp_client")
    client.async_get_clientsession = Mock()
    update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")
    update_coordinator.DataUpdateCoordinator = CoordinatorStub
    update_coordinator.UpdateFailed = type("UpdateFailed", (Exception,), {})
    integration = types.ModuleType("custom_components.picow_neopixel")
    integration.__path__ = [str(ROOT)]
    stub_modules = {
        "homeassistant": types.ModuleType("homeassistant"),
        "homeassistant.config_entries": config_entries,
        "homeassistant.const": const,
        "homeassistant.core": core,
        "homeassistant.helpers": types.ModuleType("homeassistant.helpers"),
        "homeassistant.helpers.aiohttp_client": client,
        "homeassistant.helpers.update_coordinator": update_coordinator,
        "custom_components": types.ModuleType("custom_components"),
        "custom_components.picow_neopixel": integration,
    }
    with patch.dict(sys.modules, stub_modules):
        name = "custom_components.picow_neopixel.coordinator"
        spec = importlib.util.spec_from_file_location(name, ROOT / "coordinator.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_coordinator()

    def setUp(self):
        entry = types.SimpleNamespace(data={"host": "192.0.2.1"})
        self.coordinator = self.module.PicoWNeoPixelCoordinator(Mock(), entry)
        self.coordinator.session = Mock()

    def response(self, status=200, data=None):
        response = Mock(status=status)
        response.json = AsyncMock(return_value=data)
        context = AsyncMock()
        context.__aenter__.return_value = response
        return context

    async def test_polling_failures_are_delegated_without_duplicate_logs(self):
        for error in (
            TimeoutError(),
            aiohttp.ClientConnectionError("Connection refused"),
            ValueError("Invalid response"),
        ):
            with self.subTest(error=type(error).__name__):
                self.coordinator.session.get.side_effect = error
                with patch.object(self.module, "_LOGGER") as logger:
                    for _ in range(3):
                        with self.assertRaises(self.module.UpdateFailed):
                            await self.coordinator._async_update_data()
                        self.assertFalse(self.coordinator.available)
                    logger.error.assert_not_called()
                    logger.exception.assert_not_called()

    async def test_info_failures_are_delegated_without_duplicate_logs(self):
        for _ in range(3):
            self.coordinator.session.get.side_effect = [
                self.response(data={"on": True}),
                aiohttp.ClientConnectionError("Connection refused"),
            ]
            with patch.object(self.module, "_LOGGER") as logger:
                with self.assertRaises(self.module.UpdateFailed):
                    await self.coordinator._async_update_data()
                self.assertFalse(self.coordinator.available)
                self.assertIsNone(self.coordinator._device_info)
                logger.error.assert_not_called()
                logger.exception.assert_not_called()

    async def test_http_errors_keep_their_message_without_duplicate_logs(self):
        for endpoint in ("state", "info"):
            with self.subTest(endpoint=endpoint):
                self.coordinator.session.get.side_effect = (
                    [self.response(status=503)]
                    if endpoint == "state"
                    else [
                        self.response(data={"on": True}),
                        self.response(status=503),
                    ]
                )
                with patch.object(self.module, "_LOGGER") as logger:
                    with self.assertRaisesRegex(
                        self.module.UpdateFailed, "^Device returned status 503$"
                    ):
                        await self.coordinator._async_update_data()
                    self.assertFalse(self.coordinator.available)
                    logger.error.assert_not_called()
                    logger.exception.assert_not_called()

    async def test_recovery_restores_availability_and_preserves_info_cache(self):
        self.coordinator.session.get.side_effect = [
            aiohttp.ClientConnectionError("Connection refused"),
            self.response(data={"on": True}),
            self.response(data={"version": "1.3"}),
            aiohttp.ClientConnectionError("Connection refused"),
            self.response(data={"on": False}),
        ]
        with self.assertRaises(self.module.UpdateFailed):
            await self.coordinator._async_update_data()
        self.assertFalse(self.coordinator.available)
        self.assertEqual(
            await self.coordinator._async_update_data(),
            {"state": {"on": True}, "info": {"version": "1.3"}},
        )
        self.assertTrue(self.coordinator.available)
        with self.assertRaises(self.module.UpdateFailed):
            await self.coordinator._async_update_data()
        self.assertFalse(self.coordinator.available)
        self.assertEqual(
            await self.coordinator._async_update_data(),
            {"state": {"on": False}, "info": {"version": "1.3"}},
        )
        self.assertTrue(self.coordinator.available)
        urls = [
            call.args[0] for call in self.coordinator.session.get.call_args_list
        ]
        self.assertEqual(urls.count("http://192.0.2.1:80/info"), 1)


if __name__ == "__main__":
    unittest.main()
