# 🌈 PicoW NeoPixel Home Assistant Integration

<img src="picow_neopixel.png" alt="picow_neopixel icon" width="200"/>

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate with hassfest](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Integration/actions/workflows/hassfest.yml/badge.svg)](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Integration/actions/workflows/hassfest.yml)
[![HACS Validation](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Integration/actions/workflows/hacs.yml/badge.svg)](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Integration/actions/workflows/hacs.yml)

A custom Home Assistant integration for controlling NeoPixel LED strips connected to Raspberry Pi Pico W devices via a REST API.

> **✅ Now available in HACS by default!** This integration is part of the official [HACS default repositories](https://github.com/hacs/default) — no need to add a custom repository anymore. Just search for **PicoW NeoPixel** in HACS.

## 🧩 Part of a two-repository project

This integration is the **Home Assistant side** of the project. It talks to a Raspberry Pi Pico W that runs the matching firmware:

| Repository | Role | Language |
|---|---|---|
| **PicoW-Neopixel-Homeassistant-Integration** (this repo) | Home Assistant custom integration — discovers the device and exposes it as a light entity | Python |
| [**PicoW-Neopixel-Homeassistant-Client**](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Client) | MicroPython firmware for the Pico W — drives the LEDs and serves the REST API | MicroPython |

👉 **You need both:** flash the [client firmware](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Client) onto your Pico W first, then install this integration in Home Assistant.

## ✨ Features

- **Automatic Discovery via Zeroconf/mDNS**: Devices announce themselves on the network and are picked up by Home Assistant's built-in Zeroconf component — no LAN scanning required
- **Full LED Control**: Control color (RGB), brightness, and power state
- **8 Built-in Effects**: Rainbow, fade, chase, breathing, twinkle, scanner, strobe, and static
- **Real-time Updates**: Integration polls device state and updates immediately after commands
- **Reliable Connection**: Automatic reconnection handling and error recovery
- **Device Information**: View device details including IP, MAC address, and LED count
- **Easy Setup**: One-click setup for discovered devices, with manual IP fallback

## 📋 Requirements

- Home Assistant 2024.1 or newer
- A Raspberry Pi Pico W running the [PicoW NeoPixel Client firmware](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Client)
- Device and Home Assistant on the same network / VLAN (mDNS does not cross subnets by default)

## 🛠️ Installation

### Part 1: Flash the Pico W

Install the [PicoW NeoPixel Client firmware](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Client) onto your Raspberry Pi Pico W and configure its `config.json` (WiFi, LED pin, LED count). See that repository's README for wiring and flashing instructions.

### Part 2: Install this integration

#### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. Open HACS and search for **PicoW NeoPixel** — it is included in the HACS default repositories, so it shows up directly.

   Alternatively, click the button below to jump straight to it:

   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=maxi07&repository=PicoW-Neopixel-Homeassistant-Integration&category=integration)

3. Install it and **restart Home Assistant**.

#### Manual Installation

1. Copy the `picow_neopixel` folder to your Home Assistant `custom_components` directory:

   ```bash
   mkdir -p /config/custom_components
   cp -r custom_components/picow_neopixel /config/custom_components/
   ```

2. Restart Home Assistant: **Settings** → **System** → **Restart**.

## ⚙️ Setup

### Automatic Setup (Recommended)

The Pico W firmware advertises itself over mDNS (`_picow-neopixel._tcp.local.`). Home Assistant's Zeroconf component picks the announcement up automatically:

1. Power on the device and wait until it has connected to Wi-Fi.
2. In Home Assistant, the device appears under **Settings** → **Devices & Services** as a discovered integration.
3. Click **Configure**, confirm the device, and you're done.

No network scanning is performed — the integration never probes hosts that don't belong to it.

### Manual Setup

If the device isn't picked up automatically (for example because mDNS traffic is blocked between VLANs):

1. Go to **Settings** → **Devices & Services**.
2. Click **+ Add Integration**.
3. Search for **PicoW NeoPixel**.
4. Enter the device information:
   - **Host**: IP address of your Pico W device
   - **Port**: Default is 80
5. Click **Submit**.

The integration verifies the connection and adds the device.

## 💡 Usage

### Basic Control

Once configured, the device appears as a light entity in Home Assistant. You can control:

- **Power**: Turn on/off
- **Brightness**: Adjust from 0–255
- **Color**: Pick any RGB color

### Effects

The integration supports 8 built-in effects:

- **Static**: Solid color (default)
- **Rainbow**: Animated rainbow cycle
- **Fade**: Smooth color transitions
- **Chase**: Running light effect
- **Breathing**: Pulsing brightness
- **Twinkle**: Random sparkle effect
- **Scanner**: Knight Rider style
- **Strobe**: Strobe light effect

### Automations

Automations can be configured, and the device exposes actions such as setting the brightness, color, or starting an effect.

## 🔧 Troubleshooting

### 🔍 Device Not Discovered

1. ✅ Ensure the Pico W device is powered on and connected to WiFi.
2. 🌐 Check that Home Assistant and the Pico W are on the same network / VLAN — mDNS traffic doesn't cross subnets by default.
3. 🛡️ If you run Home Assistant in Docker, make sure the container is on the `host` network (or has mDNS reflection configured) so it can see multicast traffic on the LAN.
4. 📝 Try manual setup using the device's IP address.
5. 📋 Check the Pico W logs for errors.

### 🔌 Connection Issues

1. 📍 Verify the IP address hasn't changed (consider setting a static IP / DHCP reservation).
2. 🔥 Check firewall settings.
3. 🏓 Test connectivity: `ping <device_ip>`.
4. 🌐 Try accessing `http://<device_ip>/info` in a browser.

### 💫 Effects Not Working

1. ⚡ The device must be turned on for effects to work.
2. 🎨 Effects override color settings.
3. 📋 Check Home Assistant logs for error messages.
4. 🔋 Verify the Pico W has sufficient power for all LEDs.

### ❌ Integration Shows Unavailable

1. 🌐 Check network connectivity.
2. 🔄 Restart the Pico W device.
3. 📋 Check logs: **Settings** → **System** → **Logs**.
4. 🗑️ Try removing and re-adding the integration.

## 📊 Device Information

The integration exposes the following information as entity attributes:

- `device_id`: Unique device identifier
- `ip_address`: Current IP address
- `mac_address`: MAC address
- `num_leds`: Number of LEDs configured

Access these in Developer Tools → States or use in templates:

```yaml
{{ state_attr('light.picow_neopixel', 'ip_address') }}
```

## 🔗 API Endpoints

The integration communicates with the Pico W using these REST API endpoints (served by the [client firmware](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Client)):

- `GET /info` — Device information and capabilities
- `GET /state` — Current LED state
- `POST /control` — Send commands (power, color, brightness, effects)

## ⚙️ Configuration

No additional configuration is needed after setup. All hardware settings are configured on the Pico W device itself via its `config.json` file (see the [client repository](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Client)).

### 🔢 Multiple Devices

To use multiple PicoW NeoPixel devices:

1. Give each device a unique `device.id` in its `config.json`.
2. Use a different `device.name` for easy identification.
3. Add each device separately in Home Assistant.

### 📌 Static IP Address

Recommended for reliability:

1. In your router, reserve an IP for the Pico W's MAC address.
2. This prevents connection issues after device restarts.

## 🗑️ Uninstalling

1. Go to **Settings** → **Devices & Services**.
2. Find the PicoW NeoPixel integration.
3. Click the three-dots menu → **Delete**.
4. Remove the `custom_components/picow_neopixel` folder.
5. Restart Home Assistant.

## 🔒 Security & Privacy

**Privacy:**

- ✅ Only communicates locally on your network
- ✅ No data sent to external services
- ✅ No analytics or telemetry

**Security Note:**
The integration uses HTTP (not HTTPS) for simplicity. Since it operates on your local network, this is generally acceptable. For enhanced security:

- 🔐 Keep devices on an isolated VLAN
- 🚫 Don't expose them to the internet
- 🔑 Use strong WiFi passwords

## 🛠️ Technical Details

- **Platform**: Light (plus select, button, number and sensor entities)
- **Communication**: HTTP REST API
- **Discovery Method**: Zeroconf / mDNS (`_picow-neopixel._tcp.local.`)
- **Update Interval**: 10 seconds
- **Command Timeout**: 10 seconds

## 🤝 Related Project

- 🔌 **Firmware / device side:** [PicoW-Neopixel-Homeassistant-Client](https://github.com/maxi07/PicoW-Neopixel-Homeassistant-Client) — the MicroPython code that runs on the Pico W.

## 📝 Credits

**Author**: Maximilian Krause
**License**: MIT
