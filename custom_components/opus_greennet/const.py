"""Constants for the Opus GreenNet Bridge integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "opus_greennet"

# Configuration keys
CONF_EAG_ID: Final = "eag_id"

# MQTT Topic patterns (EnOcean over IP specification)
TOPIC_BASE: Final = "EnOcean"
TOPIC_STREAM_TELEGRAM: Final = "{base}/{eag_id}/stream/telegram/{device_id}/from"
TOPIC_STREAM_TELEGRAM_TO: Final = "{base}/{eag_id}/stream/telegram/{device_id}/to"
TOPIC_STREAM_DEVICE: Final = "{base}/{eag_id}/stream/device/{device_id}"
TOPIC_PUT_STATE: Final = "{base}/{eag_id}/put/devices/{device_id}/state"
TOPIC_GET_DEVICES: Final = "{base}/{eag_id}/get/devices"
TOPIC_GET_ANSWER_DEVICES: Final = "{base}/{eag_id}/getAnswer/devices/#"

# Subscription patterns (with wildcards)
TOPIC_SUB_TELEGRAM_FROM: Final = "{base}/{eag_id}/stream/telegram/+/from"
TOPIC_SUB_TELEGRAM_FROM_ALL: Final = "{base}/{eag_id}/stream/telegram/#"
TOPIC_SUB_TELEGRAM_TO: Final = "{base}/{eag_id}/stream/telegram/+/to"
TOPIC_SUB_DEVICE: Final = "{base}/{eag_id}/stream/device/+"
TOPIC_SUB_DEVICES: Final = "{base}/{eag_id}/stream/devices/+"
TOPIC_SUB_DEVICES_ALL: Final = "{base}/{eag_id}/stream/devices/#"
TOPIC_SUB_GET_ANSWER: Final = "{base}/{eag_id}/getAnswer/devices/+"

# EEP (EnOcean Equipment Profile) to entity type mappings
# Format: EEP prefix -> (entity_type, description)
EEP_MAPPINGS: Final = {
    # Electronic Switch Actuators (D2-01-xx)
    "D2-01-00": ("switch", "Electronic Switch Actuator, 1 Channel"),
    "D2-01-01": ("switch", "Electronic Switch Actuator, 1 Channel with Energy"),
    "D2-01-02": ("light", "Dimmer, 1 Channel"),
    "D2-01-03": ("light", "Dimmer, 1 Channel with Energy"),
    "D2-01-04": ("switch", "Electronic Switch Actuator, 2 Channels"),
    "D2-01-05": ("switch", "Electronic Switch Actuator, 2 Channels with Energy"),
    "D2-01-06": ("light", "Dimmer, 2 Channels"),
    "D2-01-07": ("light", "Dimmer, 2 Channels with Energy"),
    "D2-01-08": ("switch", "Electronic Switch Actuator, 4 Channels"),
    "D2-01-09": ("switch", "Electronic Switch Actuator, 4 Channels with Energy"),
    "D2-01-0A": ("light", "Dimmer, 4 Channels"),
    "D2-01-0B": ("light", "Dimmer, 4 Channels with Energy"),
    "D2-01-0C": ("switch", "Pilot Wire Controller"),
    "D2-01-0D": ("switch", "Electronic Switch Actuator, 8 Channels"),
    "D2-01-0E": ("switch", "Electronic Switch Actuator, 8 Channels with Energy"),
    "D2-01-0F": ("light", "Dimmer, 8 Channels"),
    "D2-01-10": ("light", "Dimmer, 8 Channels with Energy"),
    "D2-01-11": ("switch", "Electronic Switch Actuator with Local Control"),
    "D2-01-12": ("light", "Dimmer with Local Control"),

    # Blinds Control (D2-05-xx)
    "D2-05-00": ("cover", "Blinds Control for Position and Angle"),
    "D2-05-01": ("cover", "Blinds Control for Position"),
    "D2-05-02": ("cover", "Blinds Control for Position and Angle, Lock"),

    # Lighting Control (A5-38-xx)
    "A5-38-08": ("light", "Gateway Dimming"),
    "A5-38-09": ("light", "Gateway Switching"),

    # Rocker Switch (F6-02-xx) - typically used as triggers
    "F6-02-01": ("event", "Rocker Switch, 2 Rocker"),
    "F6-02-02": ("event", "Rocker Switch, 2 Rocker"),
    "F6-02-03": ("event", "Rocker Switch, 2 Rocker"),

    # 4-Button Switch (F6-03-xx)
    "F6-03-01": ("event", "Rocker Switch, 4 Rocker"),
    "F6-03-02": ("event", "Rocker Switch, 4 Rocker"),
}

# Entity type to platform mapping
ENTITY_PLATFORMS: Final = {
    "light": "light",
    "switch": "switch",
    "cover": "cover",
    "event": "event",
}

# Supported platforms for this integration
PLATFORMS: Final = ["light", "switch", "cover"]

# Function keys used in EnOcean telegrams
KEY_SWITCH: Final = "switch"
KEY_DIMMER: Final = "dimValue"
KEY_POSITION: Final = "position"
KEY_ANGLE: Final = "angle"
KEY_CHANNEL: Final = "channel"
KEY_LOCAL_CONTROL: Final = "localControl"
KEY_ENERGY: Final = "energy"
KEY_POWER: Final = "power"

# Switch/Light states
STATE_ON: Final = "on"
STATE_OFF: Final = "off"

# Cover states
COVER_OPEN: Final = "open"
COVER_CLOSED: Final = "closed"
COVER_STOP: Final = "stop"

# Default values
DEFAULT_CHANNEL: Final = 0
