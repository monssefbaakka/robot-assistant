import re
import unicodedata


ROOM_ALIASES = {
    "living_room": [
        "living room",
        "livingroom",
        "salon",
        "sejour",
        "main room",
        "room",
    ]
}

DEVICE_ALIASES = {
    "light": ["light", "lights", "lamp", "lamps", "lumiere", "lumieres"],
    "ac": [
        "ac",
        "a/c",
        "air conditioner",
        "air conditioning",
        "clim",
        "climatiseur",
    ],
}

SENSOR_ALIASES = {
    "temperature": ["temperature", "temp", "degrees", "degres"],
    "humidity": ["humidity", "humidite"],
    "light_level": ["light level", "brightness", "luminosite"],
}

TURN_ON_PATTERNS = [
    r"\bturn on\b",
    r"\bswitch on\b",
    r"\ballume\b",
    r"\bactive\b",
    r"\bstart\b",
]

TURN_OFF_PATTERNS = [
    r"\bturn off\b",
    r"\bswitch off\b",
    r"\beteins\b",
    r"\beteint\b",
    r"\bdesactive\b",
    r"\bshutdown\b",
]

STATUS_PATTERNS = [
    r"\bstatus\b",
    r"\bstate\b",
    r"\best[- ]?ce\b",
    r"\bis the\b",
]

SENSOR_QUERY_PATTERNS = [
    r"\bwhat\b",
    r"\btell me\b",
    r"\bcurrent\b",
    r"\bquelle\b",
    r"\bcombien\b",
    r"\bgive me\b",
]

WEATHER_TERMS = [
    "meteo",
    "weather",
    "outside",
    "outdoor",
    "dehors",
    "exterieur",
    "exterieure",
]


def normalize_text(text):
    lowered = text.lower().strip()
    normalized = unicodedata.normalize("NFKD", lowered)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _contains_alias(text, aliases):
    return any(alias in text for alias in aliases)


def resolve_room(text):
    for room_id, aliases in ROOM_ALIASES.items():
        if _contains_alias(text, aliases):
            return room_id
    return "living_room"


def resolve_device_type(text):
    for device_type, aliases in DEVICE_ALIASES.items():
        if _contains_alias(text, aliases):
            return device_type
    return None


def resolve_sensor_type(text):
    for sensor_type, aliases in SENSOR_ALIASES.items():
        if _contains_alias(text, aliases):
            return sensor_type
    return None


def _matches_any(text, patterns):
    return any(re.search(pattern, text) for pattern in patterns)


def parse_iot_command(message, source="chat"):
    text = normalize_text(message)

    if any(term in text for term in WEATHER_TERMS):
        return None

    room = resolve_room(text)
    device_type = resolve_device_type(text)
    sensor_type = resolve_sensor_type(text)

    if device_type and _matches_any(text, TURN_ON_PATTERNS):
        return {
            "action": "turn_on",
            "room": room,
            "target_type": "device",
            "device_type": device_type,
            "device_id": None,
            "parameters": {},
            "source": source,
            "raw_text": message,
        }

    if device_type and _matches_any(text, TURN_OFF_PATTERNS):
        return {
            "action": "turn_off",
            "room": room,
            "target_type": "device",
            "device_type": device_type,
            "device_id": None,
            "parameters": {},
            "source": source,
            "raw_text": message,
        }

    set_temp_match = re.search(r"(\d{2})\s*(?:c|degrees|degree|degres)?", text)
    if device_type == "ac" and set_temp_match and any(
        token in text for token in ["set", "target", "regle", "regler", "mettre", "temperature"]
    ):
        return {
            "action": "set_temperature",
            "room": room,
            "target_type": "device",
            "device_type": "ac",
            "device_id": None,
            "parameters": {"target_temp": int(set_temp_match.group(1))},
            "source": source,
            "raw_text": message,
        }

    if device_type and _matches_any(text, STATUS_PATTERNS):
        return {
            "action": "get_device_state",
            "room": room,
            "target_type": "device",
            "device_type": device_type,
            "device_id": None,
            "parameters": {},
            "source": source,
            "raw_text": message,
        }

    if sensor_type and (
        _matches_any(text, SENSOR_QUERY_PATTERNS)
        or "temperature of the room" in text
        or "temperature du salon" in text
        or "temperature de la piece" in text
        or "current temperature" in text
    ):
        return {
            "action": "get_sensor",
            "room": room,
            "target_type": "sensor",
            "sensor_type": sensor_type,
            "parameters": {},
            "source": source,
            "raw_text": message,
        }

    return None
