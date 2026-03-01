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
3. Run `pytest -v` — all tests must pass before proceeding
4. Update version in `manifest.json` according to semver rules
5. Update CHANGELOG.md
6. Update README.md if the change affects supported devices, features, services, or project structure
7. Verify version consistency: `manifest.json` version = CHANGELOG heading = branch name suffix
8. Push branch → create PR (see PR Guidelines below)
9. Merge to main
10. Create GitHub Release (required for HACS): `gh release create v<version> --title "v<version>" --notes-file -` with release notes from CHANGELOG

### Version Rules

- **PATCH (0.0.x → 0.0.x+1)**: Bug fixes only
- **MINOR (0.x.0)**: New features, platforms, device support
- **MAJOR (x.0.0)**: Breaking changes

## PR Guidelines (MANDATORY)

### PR Title Format
```
v<version> — <Short summary of change>
```
Examples:
- `v0.1.12 — Fix cover position inversion`
- `v0.2.0 — Add number platform for dimmer speed`

### PR Body Structure
```markdown
## Summary
- Brief description of what changed and why

## Changes
- List of specific changes (copy or summarize from CHANGELOG entry)

## Testing
- [ ] `pytest -v` passes (all tests)
- [ ] Manual testing done (if applicable): describe what was tested
- [ ] Version consistent across manifest.json, CHANGELOG, and branch name
```

## Release Checklist (MANDATORY for every feature/fix)

Every change MUST complete ALL of the following before pushing the branch:

1. **Tests pass** — Run `pytest -v`. All tests must pass. If you added new functionality, add tests too.

2. **Version bump** — Update `"version"` in `manifest.json`. Use semver:
   - Patch (0.0.x → 0.0.x+1): bug fixes only
   - Minor (0.x.0): new features, new platforms, new device support
   - Major (x.0.0): breaking changes

3. **CHANGELOG.md** — Add a new section at the top with:
   - Version number and date
   - `### Added` / `### Fixed` / `### Changed` / `### Removed` subsections as needed
   - Clear, user-facing descriptions of what changed

4. **README.md** — Update if the change affects:
   - Supported device types table (new EEPs or platforms)
   - Features list
   - Project structure (new files)
   - Configuration or setup instructions
   - Services or API
   - Test count in the Development / Testing section

5. **Translation files** — If new entity types or UI strings are added:
   - `strings.json` — add entity names under `"entity"` block
   - `translations/en.json` — mirror the same entries

6. **services.yaml** — If new HA services are added, add descriptions here

7. **Version consistency check** — Before pushing, verify ALL of these match:
   - `manifest.json` `"version"` field
   - CHANGELOG.md top section heading `[x.y.z]`
   - Branch name suffix (e.g., `fix/v0.1.12`)
   - PR title prefix (e.g., `v0.1.12 — ...`)

## HACS Release (after PR is merged to main)

HACS discovers new versions via **GitHub Releases**, not just git tags.

1. Create a GitHub Release (not just a tag):
   ```bash
   gh release create v<version> --title "v<version>" --notes "<paste CHANGELOG section for this version>"
   ```
2. Verify the release appears at: `https://github.com/kegelmeier/opus_homeassistant/releases`
3. HACS will automatically pick up the new release within ~1 hour

## Coding Patterns

- All platforms follow the dispatcher signal pattern (see `light.py` as reference)
- Device state is held in `EnOceanChannel` dataclass fields
- Coordinator handles ALL MQTT communication; entities never touch MQTT directly
- Use `KNOWN_STATE_KEYS` in const.py when adding new function keys
- Multi-channel devices require the `channel` key in command functions

## Testing

- Run `pytest -v` before every push — all tests must pass
- Manual testing: trigger physical devices, verify HA entity states update
- Check HA logs at debug level: `custom_components.opus_greennet: debug`
- When adding new functionality, add corresponding tests in `tests/`

## Reference

- MQTT protocol spec: `opus_mqtt_services_reference.md` in repo root
- EEP profiles: https://www.enocean-alliance.org/eep/
