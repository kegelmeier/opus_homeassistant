# Changelog

All notable changes to this project will be documented in this file.

## [0.0.10] - 2024-11-24

### Fixed
- **Device availability restored**: Fixed device lookup in telegram handler. Devices are keyed by friendly_id but telegrams only contain device_id, causing a lookup mismatch that made all devices unavailable.
- **Thread safety fix**: Fixed `async_dispatcher_send` being called from wrong thread in `_finalize_telegram`. The `async_call_later` callback now uses proper `@callback` decorator.

## [0.0.9] - 2024-11-24

### Added
- **Initial state on startup**: Devices now load their current state during discovery from `stream/devices` data. Previously, entities would show unknown state until a physical change occurred.

## [0.0.8] - 2024-11-24

### Fixed
- **State updates now work correctly**: Fixed telegram topic regex pattern to match actual bridge structure (`EnOcean/{EAG}/stream/telegram/{DeviceID}/{property}`) instead of expecting a `from/to` direction segment.

## [0.0.7] - 2024-11-24

### Fixed
- **Simplified command functions**: Removed unnecessary `channel` function from commands. Commands now only send the required function (e.g., `{"key": "switch", "value": "on"}`).

## [0.0.6] - 2024-11-24

### Fixed
- **Commands now use correct JSON format**: Fixed command payload to use `{"state": {"functions": [...]}}` format instead of `{"telegram": {...}}`. The bridge's `put` endpoint expects a `state` object, not a `telegram` wrapper.

## [0.0.5] - 2024-11-24

### Fixed
- **State updates now work with flattened MQTT structure**: Rewrote telegram handler to parse flattened MQTT topics (like device discovery) instead of expecting JSON payloads. State changes from physical switches now properly update entity states in Home Assistant.

## [0.0.4] - 2024-11-24

### Fixed
- **Commands now use correct device ID**: Fixed critical bug where commands were sent using the friendly name (e.g., `KG_Vorrat-1K-1`) instead of the actual EnOcean device ID (e.g., `01A02F6C`). This prevented lights, switches, and covers from responding to commands.
- **Updated repository URLs**: Fixed documentation and issue tracker URLs in manifest to point to the correct repository (`opus_homeassistant`).

## [0.0.3] - 2024-11-24

### Fixed
- **Icon display in Home Assistant**: Moved `icon.png` and `logo.png` to integration root folder for proper display in the UI.

## [0.0.2] - 2024-11-24

### Fixed
- **Device discovery with flattened MQTT structure**: Rewrote coordinator to handle Opus GreenNet's flattened MQTT topic structure (one topic per property) instead of JSON payloads.

### Changed
- Subscribe to `EnOcean/{EAG}/stream/devices/#` wildcard topic
- Aggregate device properties from individual MQTT messages
- Discovery timer waits for all properties before creating entities

## [0.0.1] - 2024-11-24

### Added
- Initial release
- Auto-discovery of EnOcean devices via MQTT
- Support for lights (dimmable and on/off)
- Support for switches
- Support for covers (blinds/shades) with position and tilt
- UI-based configuration via Config Flow
- Real-time state updates via MQTT push
- Multi-channel device support
