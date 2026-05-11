import re
import unicodedata


ROOM_ALIASES = {
    "living_room": [
        "living room",
        "livingroom",
        "salon",
        "sejour",
        "main room",
    ],
    "kitchen": [
        "kitchen",
        "cuisine",
    ],
    "bedroom": [
        "bedroom",
        "bed room",
        "chambre",
    ],
    "toilet": [
        "toilet",
        "bathroom",
        "restroom",
        "wc",
        "washroom",
        "toilets",
        "salle de bain",
    ],
    "garage": [
        "garage",
        "car garage",
        "parking",
        "garrage",
        "garaj",
        "garadge",
        "garash",
    ],
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
    "door": ["door", "porte", "front door", "garage door", "gate", "shutter"],
}

SENSOR_ALIASES = {
    "temperature": ["temperature", "temp", "degrees", "degres"],
    "humidity": ["humidity", "humidite"],
    "light_level": ["light level", "brightness", "luminosite"],
    "gas_ppm": ["gas", "gaz", "gas level", "gas leak", "fuite de gaz"],
}

SET_PATTERNS = [
    r"\bset\b",
    r"\bmettre\b",
    r"\bregle\b",
    r"\bregler\b",
    r"\bchange\b",
    r"\badjust\b",
]

TURN_ON_PATTERNS = [
    r"\bturn on\b",
    r"\bswitch on\b",
    r"\bpower on\b",
    r"\ballume\b",
    r"\bactive\b",
    r"\bstart\b",
]

TURN_OFF_PATTERNS = [
    r"\bturn off\b",
    r"\bswitch off\b",
    r"\bpower off\b",
    r"\beteins\b",
    r"\beteint\b",
    r"\bdesactive\b",
    r"\bshutdown\b",
]

LOCK_PATTERNS = [
    r"\block\b",
    r"\bclose\b",
    r"\bverrouille\b",
    r"\bferme\b",
]

UNLOCK_PATTERNS = [
    r"\bunlock\b",
    r"\bopen\b",
    r"\bdeverrouille\b",
    r"\bouvre\b",
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

CONFIRM_GAS_PATTERNS = [
    r"\bit'?s me\b",
    r"\bit is me\b",
    r"\bi did it\b",
    r"\bi confirm\b",
    r"\bconfirm gas\b",
    r"\bc'?est moi\b",
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


def _matches_gas_state(text, enabled):
    return (
        (enabled and ("turn gas on" in text or "gas on" in text or "turn gaz on" in text or "gaz on" in text))
        or ((not enabled) and ("turn gas off" in text or "gas off" in text or "turn gaz off" in text or "gaz off" in text))
    )


def _gas_level_keyword(text):
    if any(term in text for term in ["maximum", "max", "highest", "full", "au maximum"]):
        return 1000
    if any(term in text for term in ["minimum", "min", "lowest", "zero", "au minimum"]):
        return 0
    return None


def parse_iot_command(message, source="chat"):
    text = normalize_text(message)

    if any(term in text for term in WEATHER_TERMS):
        return None

    room = resolve_room(text)
    device_type = resolve_device_type(text)
    sensor_type = resolve_sensor_type(text)
    percent_match = re.search(r"(\d{1,3})\s*%", text)
    number_match = re.search(r"(\d{1,4})\s*(?:ppm|percent|pourcent)?", text)
    gas_keyword_level = _gas_level_keyword(text)

    if "gas" in text or "gaz" in text or _matches_any(text, CONFIRM_GAS_PATTERNS):
        if _matches_any(text, CONFIRM_GAS_PATTERNS):
            return {
                "action": "confirm_gas_owner",
                "room": room,
                "target_type": "sensor",
                "sensor_type": "gas_ppm",
                "parameters": {},
                "source": source,
                "raw_text": message,
            }

    if room == "garage" and device_type is None:
        if _matches_any(text, TURN_ON_PATTERNS) or text.endswith(" on"):
            device_type = "light"
        elif _matches_any(text, TURN_OFF_PATTERNS) or text.endswith(" off"):
            device_type = "light"
        elif _matches_any(text, LOCK_PATTERNS) or _matches_any(text, UNLOCK_PATTERNS):
            device_type = "door"

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

    if device_type and (
        text.endswith(" on")
        or re.search(r"\bon please\b", text)
        or re.search(r"\bon now\b", text)
    ):
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

    if device_type and (
        text.endswith(" off")
        or re.search(r"\boff please\b", text)
        or re.search(r"\boff now\b", text)
    ):
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

    if device_type == "door" and _matches_any(text, LOCK_PATTERNS):
        return {
            "action": "lock",
            "room": room,
            "target_type": "device",
            "device_type": "door",
            "device_id": None,
            "parameters": {},
            "source": source,
            "raw_text": message,
        }

    if device_type == "door" and _matches_any(text, UNLOCK_PATTERNS):
        return {
            "action": "unlock",
            "room": room,
            "target_type": "device",
            "device_type": "door",
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

    if device_type == "light" and percent_match and (
        "brightness" in text
        or "luminosite" in text
        or "light level" in text
        or _matches_any(text, SET_PATTERNS)
    ):
        brightness = max(0, min(100, int(percent_match.group(1))))
        return {
            "action": "set_brightness",
            "room": room,
            "target_type": "device",
            "device_type": "light",
            "device_id": None,
            "parameters": {"brightness": brightness},
            "source": source,
            "raw_text": message,
        }

    if sensor_type == "gas_ppm" and gas_keyword_level is not None and (
        "level" in text
        or "niveau" in text
        or "gas" in text
        or "gaz" in text
        or _matches_any(text, SET_PATTERNS)
    ):
        return {
            "action": "set_gas_level",
            "room": room,
            "target_type": "sensor",
            "sensor_type": "gas_ppm",
            "parameters": {"gas_ppm": gas_keyword_level},
            "source": source,
            "raw_text": message,
        }

    if sensor_type == "gas_ppm" and (_matches_any(text, TURN_ON_PATTERNS) or _matches_gas_state(text, True)):
        return {
            "action": "set_gas_state",
            "room": room,
            "target_type": "sensor",
            "sensor_type": "gas_ppm",
            "parameters": {"enabled": True},
            "source": source,
            "raw_text": message,
        }

    if sensor_type == "gas_ppm" and (_matches_any(text, TURN_OFF_PATTERNS) or _matches_gas_state(text, False)):
        return {
            "action": "set_gas_state",
            "room": room,
            "target_type": "sensor",
            "sensor_type": "gas_ppm",
            "parameters": {"enabled": False},
            "source": source,
            "raw_text": message,
        }

    if sensor_type == "gas_ppm" and number_match and (
        "ppm" in text
        or "level" in text
        or "niveau" in text
        or _matches_any(text, SET_PATTERNS)
    ):
        gas_ppm = max(0, min(1000, int(number_match.group(1))))
        return {
            "action": "set_gas_level",
            "room": room,
            "target_type": "sensor",
            "sensor_type": "gas_ppm",
            "parameters": {"gas_ppm": gas_ppm},
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
        or _matches_any(text, STATUS_PATTERNS)
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
