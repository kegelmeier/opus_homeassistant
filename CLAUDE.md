# CLAUDE.md — Project Guidelines for AI Assistants

## Project Overview

Home Assistant custom integration for OPUS GreenNet Bridge (EnOcean over IP via MQTT).
Repository: https://github.com/kegelmeier/opus_homeassistant

## Tech Stack

- Python 3.11+
- Home Assistant custom component architecture
- MQTT (EnOcean over IP protocol)
- HACS compatible

## Project Structure

- `custom_components/opus_greennet/` — all integration code
- `manifest.json` — version (single source of truth) + metadata
- `const.py` — all constants, EEP mappings, topic patterns
- `coordinator.py` — MQTT communication, device discovery, command dispatch
- `enocean_device.py` — device/channel data model
- Platform files: `light.py`, `switch.py`, `cover.py`, `climate.py`, `sensor.py`, `binary_sensor.py`, `event.py`
- `services.yaml` — HA service definitions (rendered in Developer Tools)
- `strings.json` + `translations/en.json` — UI strings and entity names

## Branch Strategy (MANDATORY for every change)

ALWAYS create a new branch for each feature or fix. NO direct commits to main.

### Branch Naming Convention

For FEATURES: `feature/v<major>.<minor>.0`
For FIXES:    `fix/v<major>.<minor>.<patch>`

Examples:
- New platform (light):     `feature/v0.2.0`
- Bug fix in v0.1.3:      `fix/v0.1.4`
- Breaking change:          `feature/v1.0.0`

### Workflow

1. Create branch from main
2. Make changes
3. Update version (manifest.json) according to semver rules
4. Update CHANGELOG.md
5. Push branch → create PR
6. Merge to main
7. Create git tag: `git tag v<version> && git push origin v<version>`

### Version Rules

- **PATCH (0.0.x → 0.0.x+1)**: Bug fixes only
- **MINOR (0.x.0)**: New features, platforms, device support
- **MAJOR (x.0.0)**: Breaking changes

## Release Checklist (MANDATORY for every feature/fix)

Every change that is merged to `main` MUST complete ALL of the following before pushing:

1. **Version bump** — Update `"version"` in `manifest.json`. Use semver:
   - Patch (0.0.x → 0.0.x+1): bug fixes only
   - Minor (0.x.0): new features, new platforms, new device support
   - Major (x.0.0): breaking changes

2. **CHANGELOG.md** — Add a new section at the top with:
   - Version number and date
   - `### Added` / `### Fixed` / `### Changed` / `### Removed` subsections as needed
   - Clear, user-facing descriptions of what changed

3. **README.md** — Update if the change affects:
   - Supported device types table (new EEPs or platforms)
   - Features list
   - Project structure (new files)
   - Configuration or setup instructions
   - Services or API

4. **Translation files** — If new entity types or UI strings are added:
   - `strings.json` — add entity names under `"entity"` block
   - `translations/en.json` — mirror the same entries

5. **Git tag** — After pushing, create a version tag: `git tag v<version> && git push origin v<version>`

6. **services.yaml** — If new HA services are added, add descriptions here

## Coding Patterns

- All platforms follow the dispatcher signal pattern (see `light.py` as reference)
- Device state is held in `EnOceanChannel` dataclass fields
- Coordinator handles ALL MQTT communication; entities never touch MQTT directly
- Use `KNOWN_STATE_KEYS` in const.py when adding new function keys
- Multi-channel devices require the `channel` key in command functions

## Testing

- No automated tests currently exist
- Manual testing: trigger physical devices, verify HA entity states update
- Check HA logs at debug level: `custom_components.opus_greennet: debug`

## Reference

- MQTT protocol spec: `opus_mqtt_services_reference.md` in repo root
- EEP profiles: https://www.enocean-alliance.org/eep/
