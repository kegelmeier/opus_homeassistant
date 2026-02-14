"""The Opus GreenNet Bridge integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import CONF_EAG_ID, DOMAIN
from .coordinator import OpusGreenNetCoordinator

_LOGGER = logging.getLogger(__name__)

# Platforms to set up
PLATFORMS_LIST: list[Platform] = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.COVER,
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.EVENT,
]

# Service constants
SERVICE_GET_DEVICE_CONFIG = "get_device_configuration"
SERVICE_SET_DEVICE_CONFIG = "set_device_configuration"
SERVICE_GET_DEVICE_PARAMS = "get_device_parameters"
SERVICE_RELOAD_ENTRY = "reload_entry"
ATTR_DEVICE_ID = "device_id"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_CONFIGURATION = "configuration"

# Service schemas
SERVICE_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)

SERVICE_SET_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_CONFIGURATION): dict,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)


def _get_coordinator(
    hass: HomeAssistant, config_entry_id: str | None = None
) -> OpusGreenNetCoordinator:
    """Get coordinator, optionally by config entry ID."""
    if config_entry_id and config_entry_id in hass.data.get(DOMAIN, {}):
        return hass.data[DOMAIN][config_entry_id]
    # Return the first (and usually only) coordinator
    coordinators = hass.data.get(DOMAIN, {})
    if not coordinators:
        raise ValueError("No Opus GreenNet integration configured")
    return next(iter(coordinators.values()))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Opus GreenNet Bridge from a config entry."""
    eag_id = entry.data[CONF_EAG_ID]
    _LOGGER.info("Setting up Opus GreenNet Bridge: %s", eag_id)

    # Create coordinator
    coordinator = OpusGreenNetCoordinator(hass, eag_id)

    # Set up MQTT subscriptions
    try:
        if not await coordinator.async_setup():
            raise ConfigEntryNotReady("Failed to set up MQTT subscriptions")
    except Exception as err:
        _LOGGER.error("Failed to set up coordinator: %s", err)
        raise ConfigEntryNotReady from err

    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_LIST)

    # Register services (only once for the domain)
    if not hass.services.has_service(DOMAIN, SERVICE_GET_DEVICE_CONFIG):
        _register_services(hass)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _LOGGER.info("Opus GreenNet Bridge setup complete: %s", eag_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Opus GreenNet Bridge: %s", entry.data[CONF_EAG_ID])

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_LIST)

    if unload_ok:
        # Clean up coordinator
        coordinator: OpusGreenNetCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_unload()

        # Remove services if no more entries
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_GET_DEVICE_CONFIG)
            hass.services.async_remove(DOMAIN, SERVICE_SET_DEVICE_CONFIG)
            hass.services.async_remove(DOMAIN, SERVICE_GET_DEVICE_PARAMS)
            hass.services.async_remove(DOMAIN, SERVICE_RELOAD_ENTRY)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


def _register_services(hass: HomeAssistant) -> None:
    """Register Opus GreenNet services."""

    async def handle_get_device_configuration(call: ServiceCall) -> dict[str, Any] | None:
        """Handle get_device_configuration service call."""
        device_id = call.data[ATTR_DEVICE_ID]
        config_entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        coordinator = _get_coordinator(hass, config_entry_id)
        result = await coordinator.async_get_device_configuration(device_id)
        if result is not None:
            _LOGGER.info(
                "Device configuration for %s: %s", device_id, result
            )
        return result

    async def handle_set_device_configuration(call: ServiceCall) -> None:
        """Handle set_device_configuration service call."""
        device_id = call.data[ATTR_DEVICE_ID]
        configuration = call.data[ATTR_CONFIGURATION]
        config_entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        coordinator = _get_coordinator(hass, config_entry_id)
        success = await coordinator.async_set_device_configuration(
            device_id, configuration
        )
        if success:
            _LOGGER.info("Device configuration set for %s", device_id)
        else:
            _LOGGER.error("Failed to set device configuration for %s", device_id)

    async def handle_get_device_parameters(call: ServiceCall) -> dict[str, Any] | None:
        """Handle get_device_parameters service call."""
        device_id = call.data[ATTR_DEVICE_ID]
        config_entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        coordinator = _get_coordinator(hass, config_entry_id)
        result = await coordinator.async_get_device_parameters(device_id)
        if result is not None:
            _LOGGER.info("Device parameters for %s: %s", device_id, result)
        return result

    async def handle_reload_entry(call: ServiceCall) -> None:
        """Handle reload_entry service call — re-runs setup/teardown."""
        config_entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
        if config_entry_id:
            await hass.config_entries.async_reload(config_entry_id)
        else:
            for eid in list(hass.data.get(DOMAIN, {}).keys()):
                await hass.config_entries.async_reload(eid)

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_DEVICE_CONFIG,
        handle_get_device_configuration,
        schema=SERVICE_DEVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_DEVICE_CONFIG,
        handle_set_device_configuration,
        schema=SERVICE_SET_CONFIG_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_DEVICE_PARAMS,
        handle_get_device_parameters,
        schema=SERVICE_DEVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RELOAD_ENTRY,
        handle_reload_entry,
        schema=vol.Schema(
            {vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string}
        ),
    )
