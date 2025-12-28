"""Config flow for PicoW NeoPixel integration."""
from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import network
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_DEVICE_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_TIMEOUT,
    ERROR_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    port = data.get(CONF_PORT, DEFAULT_PORT)
    
    url = f"http://{host}:{port}/info"
    session = async_get_clientsession(hass)
    _LOGGER.debug("Validating connection to device at %s:%s", host, port)
    _LOGGER.debug("Connecting to URL: %s", url)
    try_count = 1
    while try_count <= 3:
        _LOGGER.debug("Connection attempt %d to %s:%s", try_count, host, port)
        try:
            async with asyncio.timeout(10):
                async with session.get(url) as response:
                    if response.status != 200:
                        _LOGGER.error("Device returned status %s", response.status)
                        raise CannotConnect
                    
                    info = await response.json()
                    
                    # Validate response structure
                    if "device" not in info:
                        _LOGGER.error("Invalid device info response")
                        raise CannotConnect
                    
                    device_info = info["device"]
                    
                    return {
                        "title": device_info.get("name", DEFAULT_NAME),
                        "device_id": device_info.get("id", "unknown"),
                        "capabilities": info.get("capabilities", {}),
                    }
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout connecting to device at %s:%s", host, port)
            raise CannotConnect from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to device at %s:%s: %s", host, port, err)
            raise CannotConnect from err
        except Exception as err:
            _LOGGER.exception("Unexpected error connecting to device: %s", err)
            raise UnknownError from err
        finally:
            try_count += 1


class PicoWNeoPixelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PicoW NeoPixel."""

    VERSION = 1
    SCAN_TIMEOUT = 1.5  # Timeout per IP
    MAX_PARALLEL_SCANS = 30  # Reduced to avoid overwhelming devices
    DISCOVERY_TIMEOUT = 60  # Total discovery timeout in seconds

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovered_devices: dict[str, dict[str, Any]] = {}
        self._discovery_done = False
        self._scan_task = None

    async def _scan_ip(
        self, session: aiohttp.ClientSession, ip: str, port: int
    ) -> dict[str, Any] | None:
        """Scan a single IP address for PicoW device."""
        url = f"http://{ip}:{port}/info"
        try:
            async with asyncio.timeout(self.SCAN_TIMEOUT):
                async with session.get(url) as response:
                    if response.status == 200:
                        info = await response.json()
                        if "device" in info and info["device"].get("id"):
                            _LOGGER.debug("Found device at %s: %s", ip, info["device"].get("name"))
                            return {
                                "ip": ip,
                                "port": port,
                                "device_id": info["device"]["id"],
                                "name": info["device"].get("name", DEFAULT_NAME),
                            }
        except (asyncio.TimeoutError, aiohttp.ClientError):
            pass
        except Exception as err:
            _LOGGER.debug("Error scanning %s: %s", ip, err)
        return None

    async def _discover_devices_http(self) -> None:
        """Discover devices via HTTP network scan."""
        if self._discovery_done:
            return
        
        _LOGGER.info("Starting HTTP network scan for devices...")
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Get Home Assistant's local IP to determine network
            adapters = await network.async_get_adapters(self.hass)
            local_ips = []
            networks_to_scan = set()  # Use set to avoid duplicates
            is_docker = False
            
            # Collect all IPv4 addresses and their networks from adapters
            for adapter in adapters:
                if not adapter.get("enabled", True):
                    continue
                    
                for ip_info in adapter["ipv4"]:
                    address = ip_info.get("address")
                    if not address or address.startswith("127."):
                        continue
                    
                    local_ips.append(address)
                    
                    # Detect Docker bridge network
                    if address.startswith("172."):
                        is_docker = True
                        _LOGGER.info("Docker bridge network detected")
                    
                    # Get network from adapter's IP and prefix
                    try:
                        network_prefix = ip_info.get("network_prefix", 24)
                        network_obj = ipaddress.ip_network(f"{address}/{network_prefix}", strict=False)
                        
                        # Skip Docker bridge networks for scanning
                        if not str(network_obj).startswith("172."):
                            networks_to_scan.add(network_obj)
                            _LOGGER.debug("Added network from adapter: %s", network_obj)
                    except Exception as err:
                        _LOGGER.debug("Could not parse network from %s: %s", address, err)
            
            # If running in Docker (detected by 172.x IP), scan common home networks
            if is_docker and not networks_to_scan:
                _LOGGER.info("Docker detected without local networks. Scanning common home networks.")
                # Scan most common home network ranges
                common_networks = [
                    "192.168.0.0/24",
                    "192.168.1.0/24",
                    "192.168.2.0/24",
                    "192.168.10.0/24",
                    "192.168.100.0/24",
                    "192.168.111.0/24",  # Your network
                    "192.168.178.0/24",
                    "10.0.0.0/24",
                    "10.0.1.0/24",
                ]
                for network_str in common_networks:
                    try:
                        networks_to_scan.add(ipaddress.ip_network(network_str, strict=False))
                    except Exception as err:
                        _LOGGER.debug("Could not add network %s: %s", network_str, err)
            
            if not networks_to_scan:
                _LOGGER.warning("Could not determine any networks to scan")
                return
            
            _LOGGER.info("Scanning %d network(s): %s", len(networks_to_scan), [str(n) for n in networks_to_scan])
            
            # Scan all networks with timeout
            session = async_get_clientsession(self.hass)
            scan_tasks = []
            
            for network_obj in networks_to_scan:
                # Check if we've exceeded total discovery timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > self.DISCOVERY_TIMEOUT:
                    _LOGGER.warning("Discovery timeout reached, stopping scan")
                    break
                
                # Create scan tasks for all IPs in network
                for ip in network_obj.hosts():
                    ip_str = str(ip)
                    # Skip Home Assistant's own IPs
                    if ip_str not in local_ips:
                        scan_tasks.append(self._scan_ip(session, ip_str, DEFAULT_PORT))
                    
                    # Batch scans to avoid overwhelming the network
                    if len(scan_tasks) >= self.MAX_PARALLEL_SCANS:
                        # Check timeout before processing batch
                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed > self.DISCOVERY_TIMEOUT:
                            _LOGGER.warning("Discovery timeout reached during batch processing")
                            break
                        
                        results = await asyncio.gather(*scan_tasks, return_exceptions=True)
                        for result in results:
                            if result and isinstance(result, dict):
                                device_id = result["device_id"]
                                self.discovered_devices[device_id] = {
                                    CONF_HOST: result["ip"],
                                    CONF_PORT: result["port"],
                                    CONF_NAME: result["name"],
                                    "name": result["name"],
                                }
                                _LOGGER.info("Found device: %s at %s", result["name"], result["ip"])
                        scan_tasks = []
            
            # Process remaining tasks
            if scan_tasks:
                elapsed = asyncio.get_event_loop().time() - start_time
                remaining_time = self.DISCOVERY_TIMEOUT - elapsed
                if remaining_time > 0:
                    try:
                        results = await asyncio.wait_for(
                            asyncio.gather(*scan_tasks, return_exceptions=True),
                            timeout=remaining_time
                        )
                        for result in results:
                            if result and isinstance(result, dict):
                                device_id = result["device_id"]
                                self.discovered_devices[device_id] = {
                                    CONF_HOST: result["ip"],
                                    CONF_PORT: result["port"],
                                    CONF_NAME: result["name"],
                                    "name": result["name"],
                                }
                                _LOGGER.info("Found device: %s at %s", result["name"], result["ip"])
                    except asyncio.TimeoutError:
                        _LOGGER.warning("Final batch timed out")
            
            total_time = asyncio.get_event_loop().time() - start_time
            _LOGGER.info("Network scan completed in %.1f seconds. Found %d devices", 
                        total_time, len(self.discovered_devices))
            
        except Exception as err:
            _LOGGER.error("Error during HTTP device discovery: %s", err, exc_info=True)
        finally:
            self._discovery_done = True

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Start discovery scan immediately
        return await self.async_step_scan()

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show progress while scanning for devices."""
        if not self._discovery_done:
            # Show progress screen with task
            return self.async_show_progress(
                step_id="scan",
                progress_action="scan_devices",
                progress_task=self.hass.async_create_task(
                    self._async_scan_task()
                ),
            )
        
        # Discovery done, check results
        if self.discovered_devices:
            return self.async_show_progress_done(next_step_id="discovery")
        
        # No devices found, go to manual input
        return self.async_show_progress_done(next_step_id="manual")
    
    async def _async_scan_task(self) -> None:
        """Background task to scan for devices."""
        _LOGGER.info("Starting device discovery...")
        await self._discover_devices_http()
        
        # Update progress when done
        if self.discovered_devices:
            _LOGGER.info("Devices found, will redirect to discovery step")
        else:
            _LOGGER.info("No devices found, will redirect to manual input")
        
        # Trigger the next step
        self.hass.async_create_task(
            self.hass.config_entries.flow.async_configure(
                flow_id=self.flow_id
            )
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual device input after failed discovery."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = ERROR_CANNOT_CONNECT
            except UnknownError:
                errors["base"] = ERROR_UNKNOWN
            else:
                # Check if already configured
                await self.async_set_unique_id(info["device_id"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                        CONF_NAME: info["title"],
                        CONF_DEVICE_ID: info["device_id"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
            description_placeholders={
                "discovered_count": str(len(self.discovered_devices))
            },
        )

    async def async_step_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle discovery of devices."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # User selected a discovered device
            device_id = user_input["device"]
            device = self.discovered_devices[device_id]
            
            # Give the device a moment to recover from the scan
            await asyncio.sleep(2)
            
            _LOGGER.debug("Validating connection to device at %s:%s", 
                         device[CONF_HOST], device.get(CONF_PORT, DEFAULT_PORT))

            try:
                _LOGGER.debug("Connecting to URL: http://%s:%s/info", 
                             device[CONF_HOST], device.get(CONF_PORT, DEFAULT_PORT))
                info = await validate_input(self.hass, device)
            except CannotConnect:
                _LOGGER.warning("Cannot connect to discovered device at %s:%s. Device may be busy.", 
                               device[CONF_HOST], device.get(CONF_PORT, DEFAULT_PORT))
                errors["base"] = ERROR_CANNOT_CONNECT
            except UnknownError:
                _LOGGER.warning("Unknown error connecting to discovered device at %s:%s",
                               device[CONF_HOST], device.get(CONF_PORT, DEFAULT_PORT))
                errors["base"] = ERROR_UNKNOWN
            else:
                # Successfully connected, create entry
                await self.async_set_unique_id(info["device_id"])
                self._abort_if_unique_id_configured()

                _LOGGER.info("Creating entry for device: %s at %s:%s",
                            info["title"], device[CONF_HOST], device.get(CONF_PORT, DEFAULT_PORT))

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: device[CONF_HOST],
                        CONF_PORT: device.get(CONF_PORT, DEFAULT_PORT),
                        CONF_NAME: info["title"],
                        CONF_DEVICE_ID: info["device_id"],
                    },
                )

        # Show discovered devices
        devices_list = {
            device_id: f"{device['name']} ({device[CONF_HOST]})"
            for device_id, device in self.discovered_devices.items()
        }

        if not devices_list:
            _LOGGER.warning("No devices in discovery list, redirecting to manual input")
            return await self.async_step_user()

        return self.async_show_form(
            step_id="discovery",
            data_schema=vol.Schema(
                {
                    vol.Required("device"): vol.In(devices_list),
                }
            ),
            errors=errors,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class UnknownError(Exception):
    """Error to indicate an unknown error occurred."""
