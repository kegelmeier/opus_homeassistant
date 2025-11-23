# Opus GreenNet Bridge - Home Assistant Integration

![OPUS Logo](custom_components/opus_greennet/brands/logo.png)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/kegelmeier/opus_greennet.svg)](https://github.com/kegelmeier/opus_greennet/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A custom Home Assistant integration for the Opus GreenNet Bridge, enabling control of EnOcean devices via MQTT following the EnOcean over IP specification.

## Features

- **Auto-discovery**: Automatically discovers EnOcean devices connected to your Opus GreenNet Bridge
- **Real-time updates**: Receives state changes via MQTT push notifications
- **Bidirectional control**: Send commands to actuators (lights, switches, covers)
- **UI Configuration**: Set up via Home Assistant's Integrations page

## Supported Device Types

| Entity Type | EEP Profiles | Description |
|-------------|--------------|-------------|
| **Light** | D2-01-02, D2-01-03, D2-01-06, D2-01-07, D2-01-0A, D2-01-0B, D2-01-0F, D2-01-10, D2-01-12, A5-38-08 | Dimmable lights |
| **Switch** | D2-01-00, D2-01-01, D2-01-04, D2-01-05, D2-01-08, D2-01-09, D2-01-0C, D2-01-0D, D2-01-0E, D2-01-11 | On/Off switches and actuators |
| **Cover** | D2-05-00, D2-05-01, D2-05-02 | Blinds, shades, and shutters |

## Prerequisites

1. **Home Assistant** with MQTT integration configured (e.g., Mosquitto add-on)
2. **Opus GreenNet Bridge** with its built-in MQTT broker
3. **EnOcean devices** paired with your bridge
4. **MQTT Bridge** configured between your HA broker and the Opus GreenNet broker (see below)

## MQTT Bridge Setup (Required)

The Opus GreenNet Bridge runs its own MQTT broker. To connect it to Home Assistant, you need to configure an MQTT bridge on your Home Assistant MQTT broker (e.g., Mosquitto).

### For Mosquitto Add-on

1. In Home Assistant, go to **Settings** → **Add-ons** → **Mosquitto broker** → **Configuration**

2. Add the following to the **Customize** section (or edit the Mosquitto config directly):

   Create a file `/share/mosquitto/opus_bridge.conf` with:

   ```
   connection opus_greennet
   address <OPUS_BRIDGE_IP>:1883
   topic EnOcean/# both 1
   remote_username <username>
   remote_password <password>
   ```

   Replace:
   - `<OPUS_BRIDGE_IP>` with your Opus GreenNet Bridge's IP address
   - `<username>`: `admin`
   - `<password>`: Your gateway's EURID in uppercase (e.g., `050B4DFA`)

3. Reference this config file in the Mosquitto add-on configuration:

   ```yaml
   customize:
     active: true
     folder: mosquitto
   ```

4. Restart the Mosquitto add-on

### For Standalone Mosquitto

Add to your `mosquitto.conf`:

```
connection opus_greennet
address <OPUS_BRIDGE_IP>:1883
topic EnOcean/# both 1
bridge_protocol_version mqttv311
```

### Verify the Bridge

Use an MQTT client (like MQTT Explorer) connected to your HA broker to verify you can see topics like:
```
EnOcean/<EAG-ID>/stream/telegram/#
```

If you see messages when triggering EnOcean devices, the bridge is working.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the menu (three dots) → "Custom repositories"
4. Add this repository URL and select "Integration"
5. Install "Opus GreenNet Bridge"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/opus_greennet` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click **Add Integration**
3. Search for "Opus GreenNet Bridge"
4. Enter your **EAG Identifier** (Bridge ID, e.g., `050B4DFA`)
5. Click **Submit**

## MQTT Topic Structure

The integration follows the EnOcean over IP MQTT specification:

```
EnOcean/{EAG-Identifier}/stream/telegram/{Device-Identifier}/from  # Device → Gateway
EnOcean/{EAG-Identifier}/stream/telegram/{Device-Identifier}/to    # Gateway → Device
EnOcean/{EAG-Identifier}/put/devices/{Device-Identifier}/state     # Commands
EnOcean/{EAG-Identifier}/get/devices                               # Device discovery
EnOcean/{EAG-Identifier}/getAnswer/devices/{Device-Identifier}     # Discovery response
```

## Telegram Payload Format

```json
{
  "telegram": {
    "deviceId": "01843197",
    "friendlyId": "LivingRoom_Light",
    "timestamp": "2024-01-15T10:30:00.000+0100",
    "direction": "from",
    "functions": [
      {"key": "switch", "value": "on"},
      {"key": "dimValue", "value": "75"}
    ],
    "telegramInfo": {
      "data": "0000000A",
      "dbm": -65,
      "rorg": "A5"
    }
  }
}
```

## Troubleshooting

### Devices not appearing

1. Check that MQTT integration is connected
2. Verify your EAG Identifier is correct
3. Check Home Assistant logs for MQTT subscription errors
4. Ensure your Opus GreenNet Bridge is publishing to the expected topics

### Enable debug logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.opus_greennet: debug
```

## Development

### Project Structure

```
custom_components/opus_greennet/
├── __init__.py           # Integration setup
├── manifest.json         # Integration metadata
├── config_flow.py        # UI configuration
├── const.py              # Constants and EEP mappings
├── coordinator.py        # MQTT communication handler
├── enocean_device.py     # Device data model
├── light.py              # Light entity platform
├── switch.py             # Switch entity platform
├── cover.py              # Cover entity platform
├── strings.json          # UI strings
└── translations/
    └── en.json           # English translations
```

## License

MIT License

## References

- [EnOcean over IP MQTT Specification](https://www.enocean-alliance.org/ip/)
- [EnOcean Equipment Profiles (EEP)](https://www.enocean-alliance.org/eep/)
- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
