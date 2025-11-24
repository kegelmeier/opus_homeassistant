"""Data coordinator for Opus GreenNet Bridge integration."""
from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.mqtt import ReceiveMessage
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later

from .const import (
    DOMAIN,
    TOPIC_BASE,
    TOPIC_PUT_STATE,
    TOPIC_SUB_DEVICES_ALL,
    TOPIC_SUB_TELEGRAM_FROM_ALL,
)
from .enocean_device import EnOceanDevice

_LOGGER = logging.getLogger(__name__)

# Dispatcher signals
SIGNAL_DEVICE_DISCOVERED = f"{DOMAIN}_device_discovered"
SIGNAL_DEVICE_STATE_UPDATE = f"{DOMAIN}_device_state_update"

# Regex to parse device topics
# EnOcean/{EAG}/stream/devices/{DeviceID}/{property}
DEVICE_TOPIC_PATTERN = re.compile(
    r"EnOcean/([^/]+)/stream/devices/([^/]+)/(.+)"
)

# Regex to parse telegram topics
# EnOcean/{EAG}/stream/telegram/{DeviceID}/{property}
TELEGRAM_TOPIC_PATTERN = re.compile(
    r"EnOcean/([^/]+)/stream/telegram/([^/]+)/(.+)"
)


class OpusGreenNetCoordinator:
    """Coordinator for managing MQTT communication with Opus GreenNet Bridge."""

    def __init__(self, hass: HomeAssistant, eag_id: str) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.eag_id = eag_id
        self.devices: dict[str, EnOceanDevice] = {}
        self._device_data: dict[str, dict[str, Any]] = {}  # Raw device properties
        self._telegram_data: dict[str, dict[str, Any]] = {}  # Raw telegram properties
        self._subscriptions: list[Callable[[], None]] = []
        self._discovery_complete = False
        self._pending_devices: set[str] = set()
        self._pending_telegrams: dict[str, Callable | None] = {}  # Timers per device
        self._discovery_timer: Callable | None = None

    async def async_setup(self) -> bool:
        """Set up the coordinator and start MQTT subscriptions."""
        _LOGGER.debug("Setting up Opus GreenNet coordinator for EAG %s", self.eag_id)

        # Subscribe to telegram stream with # wildcard (flattened structure)
        topic_telegram = TOPIC_SUB_TELEGRAM_FROM_ALL.format(
            base=TOPIC_BASE, eag_id=self.eag_id
        )
        self._subscriptions.append(
            await mqtt.async_subscribe(
                self.hass, topic_telegram, self._handle_telegram_property_message, qos=1
            )
        )
        _LOGGER.info("Subscribed to telegram topic: %s", topic_telegram)

        # Subscribe to ALL device properties with # wildcard
        topic_devices_all = TOPIC_SUB_DEVICES_ALL.format(
            base=TOPIC_BASE, eag_id=self.eag_id
        )
        self._subscriptions.append(
            await mqtt.async_subscribe(
                self.hass, topic_devices_all, self._handle_device_property_message, qos=1
            )
        )
        _LOGGER.info("Subscribed to devices topic: %s", topic_devices_all)

        # Schedule device discovery finalization after 5 seconds
        self._discovery_timer = async_call_later(
            self.hass, 5, self._finalize_discovery
        )

        return True

    async def async_unload(self) -> None:
        """Unload the coordinator and unsubscribe from MQTT."""
        _LOGGER.debug("Unloading Opus GreenNet coordinator for EAG %s", self.eag_id)
        if self._discovery_timer:
            self._discovery_timer()
        for unsubscribe in self._subscriptions:
            unsubscribe()
        self._subscriptions.clear()

    @callback
    def _handle_device_property_message(self, msg: ReceiveMessage) -> None:
        """Handle incoming device property messages from flattened MQTT structure."""
        try:
            # Parse topic: EnOcean/{EAG}/stream/devices/{DeviceID}/{property_path}
            match = DEVICE_TOPIC_PATTERN.match(msg.topic)
            if not match:
                return

            eag_id, device_id, property_path = match.groups()

            if eag_id != self.eag_id:
                return

            # Get or create device data dict
            if device_id not in self._device_data:
                self._device_data[device_id] = {"deviceId": device_id}
                self._pending_devices.add(device_id)

            # Parse the property path and value
            payload = msg.payload.decode() if isinstance(msg.payload, bytes) else str(msg.payload)

            # Handle nested properties like eeps/0/eep or states/switch
            self._set_nested_property(self._device_data[device_id], property_path, payload)

            # Reset discovery timer on each message
            if self._discovery_timer:
                self._discovery_timer()
            self._discovery_timer = async_call_later(
                self.hass, 2, self._finalize_discovery
            )

        except Exception as err:
            _LOGGER.exception("Error handling device property message: %s", err)

    def _set_nested_property(self, data: dict, path: str, value: str) -> None:
        """Set a nested property in a dict using a path like 'eeps/0/eep'."""
        parts = path.split("/")
        current = data

        for i, part in enumerate(parts[:-1]):
            # Check if next part is a number (array index)
            if parts[i + 1].isdigit():
                if part not in current:
                    current[part] = []
                current = current[part]
            elif part.isdigit():
                # This is an array index
                idx = int(part)
                while len(current) <= idx:
                    current.append({})
                current = current[idx]
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]

        # Set the final value
        final_key = parts[-1]
        if final_key.isdigit():
            idx = int(final_key)
            while len(current) <= idx:
                current.append(None)
            current[idx] = self._parse_value(value)
        else:
            current[final_key] = self._parse_value(value)

    def _parse_value(self, value: str) -> Any:
        """Parse a string value to appropriate type."""
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    @callback
    def _finalize_discovery(self, *args) -> None:
        """Finalize device discovery after receiving all properties."""
        _LOGGER.info("Finalizing device discovery, found %d devices", len(self._device_data))

        for device_id, data in self._device_data.items():
            if device_id in self._pending_devices:
                self._pending_devices.discard(device_id)
                self._create_device_from_data(device_id, data)

        self._discovery_complete = True

    def _create_device_from_data(self, device_id: str, data: dict) -> None:
        """Create an EnOceanDevice from collected property data."""
        try:
            friendly_id = data.get("friendlyId", device_id)
            device_key = friendly_id

            # Build EEPs list
            eeps = []
            eeps_data = data.get("eeps", {})
            if isinstance(eeps_data, list):
                eeps = eeps_data
            elif isinstance(eeps_data, dict):
                for idx in sorted(eeps_data.keys(), key=lambda x: int(x) if x.isdigit() else x):
                    eep_entry = eeps_data[idx]
                    if isinstance(eep_entry, dict):
                        eeps.append(eep_entry)
                    elif isinstance(eep_entry, str):
                        eeps.append({"eep": eep_entry})

            is_new = device_key not in self.devices

            device = EnOceanDevice(
                device_id=device_id,
                friendly_id=friendly_id,
                eeps=eeps,
                manufacturer=data.get("manufacturer", ""),
                physical_device=data.get("physicalDevice", ""),
                first_seen=str(data.get("firstSeen", "")),
                last_seen=str(data.get("lastSeen", "")),
                dbm=data.get("dbm", 0),
            )

            # Preserve existing channel state or apply initial state from discovery
            if device_key in self.devices:
                device.channels = self.devices[device_key].channels
            else:
                # Apply initial state from discovery data (states/switch, states/dimValue, etc.)
                self._apply_initial_state(device, data)

            self.devices[device_key] = device

            _LOGGER.info(
                "Device %s: %s (%s) - EEPs: %s - Type: %s",
                "discovered" if is_new else "updated",
                friendly_id,
                device_id,
                [eep.get("eep") if isinstance(eep, dict) else eep for eep in eeps],
                device.entity_type,
            )

            if is_new:
                async_dispatcher_send(
                    self.hass,
                    f"{SIGNAL_DEVICE_DISCOVERED}_{self.eag_id}",
                    device,
                )

        except Exception as err:
            _LOGGER.exception("Error creating device from data: %s", err)

    def _apply_initial_state(self, device: EnOceanDevice, data: dict) -> None:
        """Apply initial state from device discovery data."""
        _LOGGER.info("INITIAL STATE: device=%s data_keys=%s", device.friendly_id, list(data.keys()))
        states = data.get("states", {})
        if not states:
            _LOGGER.info("INITIAL STATE: No 'states' in data for %s", device.friendly_id)
            return
        _LOGGER.info("INITIAL STATE: Found states=%s", states)

        # Build a telegram-like structure from states data
        functions = []

        # Handle states that might be nested (states/switch, states/dimValue, etc.)
        if isinstance(states, dict):
            for key, value in states.items():
                if key in ("switch", "dimValue", "position", "angle", "localControl"):
                    functions.append({"key": key, "value": value})

        if functions:
            telegram = {"functions": functions}
            device.update_from_telegram(telegram)
            _LOGGER.debug(
                "Applied initial state to device %s: %s",
                device.friendly_id,
                functions,
            )

    @callback
    def _handle_telegram_property_message(self, msg: ReceiveMessage) -> None:
        """Handle incoming telegram property messages from flattened MQTT structure."""
        try:
            # Log every telegram message at INFO level for debugging
            _LOGGER.info("TELEGRAM MSG: %s = %s", msg.topic, msg.payload)

            # Parse topic: EnOcean/{EAG}/stream/telegram/{DeviceID}/{property_path}
            match = TELEGRAM_TOPIC_PATTERN.match(msg.topic)
            if not match:
                _LOGGER.warning("TELEGRAM: No regex match for topic: %s", msg.topic)
                return

            eag_id, device_id, property_path = match.groups()
            _LOGGER.info("TELEGRAM PARSED: eag=%s dev=%s path=%s", eag_id, device_id, property_path)

            if eag_id != self.eag_id:
                _LOGGER.warning("TELEGRAM: EAG mismatch %s != %s", eag_id, self.eag_id)
                return

            # Get or create telegram data dict for this device
            if device_id not in self._telegram_data:
                self._telegram_data[device_id] = {"deviceId": device_id}

            # Parse the property path and value
            payload = msg.payload.decode() if isinstance(msg.payload, bytes) else str(msg.payload)

            # Handle nested properties like functions/0/key or telegramInfo/dbm
            self._set_nested_property(self._telegram_data[device_id], property_path, payload)

            # Reset telegram timer for this device - finalize after short delay
            if device_id in self._pending_telegrams and self._pending_telegrams[device_id]:
                self._pending_telegrams[device_id]()

            @callback
            def finalize_callback(_now, did=device_id):
                self._finalize_telegram(did)

            self._pending_telegrams[device_id] = async_call_later(
                self.hass, 0.5, finalize_callback
            )

        except Exception as err:
            _LOGGER.exception("Error handling telegram property message: %s", err)

    @callback
    def _finalize_telegram(self, device_id: str) -> None:
        """Finalize telegram processing after receiving all properties."""
        _LOGGER.info("FINALIZE called for device_id=%s", device_id)

        if device_id not in self._telegram_data:
            _LOGGER.warning("FINALIZE: No telegram data for %s", device_id)
            return

        telegram_data = self._telegram_data.pop(device_id)
        self._pending_telegrams.pop(device_id, None)

        friendly_id = telegram_data.get("friendlyId", device_id)

        _LOGGER.info("FINALIZE telegram_data: %s", telegram_data)

        # Build functions list from the telegram data
        functions = []
        functions_data = telegram_data.get("functions", {})
        if isinstance(functions_data, dict):
            for idx in sorted(functions_data.keys(), key=lambda x: int(x) if str(x).isdigit() else x):
                func_entry = functions_data[idx]
                if isinstance(func_entry, dict):
                    functions.append(func_entry)

        # Create telegram dict in the format expected by update_from_telegram
        telegram = {
            "deviceId": device_id,
            "friendlyId": friendly_id,
            "functions": functions,
            "timestamp": telegram_data.get("timestamp"),
            "telegramInfo": telegram_data.get("telegramInfo", {}),
        }

        _LOGGER.info("FINALIZE functions built: %s", functions)

        # Find device by device_id (devices are keyed by friendly_id)
        device = None
        device_key = None
        _LOGGER.info("FINALIZE: Looking for device_id=%s in devices: %s",
                     device_id, [(k, v.device_id) for k, v in self.devices.items()])
        for key, dev in self.devices.items():
            if dev.device_id == device_id:
                device = dev
                device_key = key
                _LOGGER.info("FINALIZE: Found device key=%s", key)
                break

        if device is None:
            _LOGGER.info("FINALIZE: Device NOT found, creating new")
            # Create a basic device entry if we haven't discovered it yet
            device_key = device_id
            device = EnOceanDevice(
                device_id=device_id,
                friendly_id=device_id,
            )
            self.devices[device_key] = device
            _LOGGER.info(
                "Auto-discovered device from telegram: %s",
                device_id,
            )
            async_dispatcher_send(
                self.hass,
                f"{SIGNAL_DEVICE_DISCOVERED}_{self.eag_id}",
                device,
            )

        # Update device state
        device.update_from_telegram(telegram)

        channel_state = device.channels.get(0)
        _LOGGER.info(
            "FINALIZE: Updated device %s state: is_on=%s, brightness=%s, position=%s",
            device_key,
            channel_state.is_on if channel_state else "no channel",
            channel_state.brightness if channel_state else None,
            channel_state.position if channel_state else None,
        )

        # Notify listeners of state update
        signal = f"{SIGNAL_DEVICE_STATE_UPDATE}_{self.eag_id}_{device_key}"
        _LOGGER.info("FINALIZE: Sending signal %s", signal)
        async_dispatcher_send(self.hass, signal, device)

    async def async_send_command(
        self,
        device_id: str,
        functions: list[dict[str, Any]],
    ) -> None:
        """Send a command to a device using JSON state message."""
        topic = TOPIC_PUT_STATE.format(
            base=TOPIC_BASE, eag_id=self.eag_id, device_id=device_id
        )

        # Build state object (not telegram!) as expected by the bridge
        state_message = {
            "state": {
                "functions": functions,
            }
        }

        payload = json.dumps(state_message)
        _LOGGER.debug("Sending command to %s: %s", topic, payload)

        await mqtt.async_publish(self.hass, topic, payload, qos=1)

    async def async_turn_on(
        self,
        device_id: str,
        channel: int = 0,
        brightness: int | None = None,
    ) -> None:
        """Turn on a switch or light."""
        if brightness is not None:
            functions = [{"key": "dimValue", "value": str(brightness)}]
        else:
            functions = [{"key": "switch", "value": "on"}]

        await self.async_send_command(device_id, functions)

    async def async_turn_off(self, device_id: str, channel: int = 0) -> None:
        """Turn off a switch or light."""
        functions = [{"key": "switch", "value": "off"}]
        await self.async_send_command(device_id, functions)

    async def async_set_cover_position(
        self,
        device_id: str,
        position: int,
        channel: int = 0,
    ) -> None:
        """Set cover position (0 = closed, 100 = open)."""
        functions = [{"key": "position", "value": str(position)}]
        await self.async_send_command(device_id, functions)

    async def async_set_cover_tilt(
        self,
        device_id: str,
        tilt: int,
        channel: int = 0,
    ) -> None:
        """Set cover tilt angle."""
        functions = [{"key": "angle", "value": str(tilt)}]
        await self.async_send_command(device_id, functions)

    async def async_stop_cover(self, device_id: str, channel: int = 0) -> None:
        """Stop cover movement."""
        functions = [{"key": "position", "value": "stop"}]
        await self.async_send_command(device_id, functions)

    def get_device(self, device_id: str) -> EnOceanDevice | None:
        """Get a device by ID."""
        return self.devices.get(device_id)

    def get_devices_by_type(self, entity_type: str) -> list[EnOceanDevice]:
        """Get all devices of a specific entity type."""
        return [
            device
            for device in self.devices.values()
            if device.entity_type == entity_type
        ]
