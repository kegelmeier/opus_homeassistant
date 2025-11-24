# Changelog

All notable changes to this project will be documented in this file.

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
