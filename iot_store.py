import json
import os
import threading
from copy import deepcopy
from datetime import datetime, timezone

from config_env import load_env_file


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "iot_state.json")
EVENTS_PATH = os.path.join(BASE_DIR, "iot_events.json")
_STORE_LOCK = threading.RLock()


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def current_transport_label():
    load_env_file()
    mode = os.environ.get("IOT_MODE", "simulator").strip().lower()
    if mode == "hardware":
        return "mqtt-wokwi-hardware"
    return "mqtt-python-simulator"


def default_state():
    now = _now_iso()
    return {
        "meta": {
            "last_update": now,
            "transport": current_transport_label(),
            "version": 1,
        },
        "outside": {
            "temperature": 29.0,
            "humidity": 45,
            "source": "default",
            "updated_at": now,
        },
        "rooms": {
            "living_room": {
                "name": "Living Room",
                "devices": {
                    "light_main": {
                        "id": "light_main",
                        "type": "light",
                        "name": "Main Light",
                        "state": "on",
                        "brightness": 80,
                        "power_w": 12,
                    },
                    "ac_main": {
                        "id": "ac_main",
                        "type": "ac",
                        "name": "Main AC",
                        "state": "off",
                        "mode": "cool",
                        "target_temp": 22,
                        "fan_speed": 2,
                        "power_w": 0,
                    },
                    "door_main": {
                        "id": "door_main",
                        "type": "door",
                        "name": "Front Door",
                        "state": "locked",
                    },
                    "buzzer_main": {
                        "id": "buzzer_main",
                        "type": "buzzer",
                        "name": "Gas Safety Buzzer",
                        "state": "off",
                    },
                },
                "sensors": {
                    "temperature": 27.4,
                    "humidity": 48,
                    "occupancy": True,
                    "light_level": 760,
                    "gas_ppm": 120,
                },
                "environment": {
                    "insulation_factor": 0.72,
                    "sun_exposure": 0.65,
                },
            }
        },
        "alerts": {
            "gas": False,
            "gas_unconfirmed": False,
            "gas_buzzer": False,
        },
        "safety": {
            "gas_confirmation": {
                "pending": False,
                "armed_at": None,
                "confirmed": False,
            }
        },
    }


def _atomic_write(path, payload):
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    os.replace(temp_path, path)


def ensure_files():
    with _STORE_LOCK:
        if not os.path.exists(STATE_PATH):
            _atomic_write(STATE_PATH, default_state())
        if not os.path.exists(EVENTS_PATH):
            _atomic_write(EVENTS_PATH, {"events": []})


def _load_events_payload():
    with _STORE_LOCK:
        ensure_files()
        try:
            with open(EVENTS_PATH, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError):
            payload = {"events": []}
            _atomic_write(EVENTS_PATH, payload)
        payload.setdefault("events", [])
        return payload


def load_state():
    with _STORE_LOCK:
        ensure_files()
        with open(STATE_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)


def save_state(state):
    with _STORE_LOCK:
        state.setdefault("meta", {})["transport"] = current_transport_label()
        _atomic_write(STATE_PATH, state)


def reset_state():
    with _STORE_LOCK:
        state = default_state()
        save_state(state)
        _atomic_write(EVENTS_PATH, {"events": []})
        return deepcopy(state)


def append_event(event):
    with _STORE_LOCK:
        payload = _load_events_payload()
        payload["events"].append(event)
        payload["events"] = payload["events"][-200:]
        _atomic_write(EVENTS_PATH, payload)


def load_events(limit=None):
    with _STORE_LOCK:
        payload = _load_events_payload()
        events = payload.get("events", [])
        if limit is not None:
            return events[-limit:]
        return events
