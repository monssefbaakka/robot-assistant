import json
import os
from copy import deepcopy
from datetime import datetime, timezone


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "iot_state.json")
EVENTS_PATH = os.path.join(BASE_DIR, "iot_events.json")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def default_state():
    now = _now_iso()
    return {
        "meta": {
            "last_update": now,
            "transport": "mqtt-loopback",
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
                },
                "sensors": {
                    "temperature": 27.4,
                    "humidity": 48,
                    "occupancy": True,
                    "light_level": 760,
                },
                "environment": {
                    "insulation_factor": 0.72,
                    "sun_exposure": 0.65,
                },
            }
        },
    }


def _atomic_write(path, payload):
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    os.replace(temp_path, path)


def ensure_files():
    if not os.path.exists(STATE_PATH):
        _atomic_write(STATE_PATH, default_state())
    if not os.path.exists(EVENTS_PATH):
        _atomic_write(EVENTS_PATH, {"events": []})


def load_state():
    ensure_files()
    with open(STATE_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_state(state):
    _atomic_write(STATE_PATH, state)


def reset_state():
    state = default_state()
    save_state(state)
    _atomic_write(EVENTS_PATH, {"events": []})
    return deepcopy(state)


def append_event(event):
    ensure_files()
    with open(EVENTS_PATH, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    payload.setdefault("events", []).append(event)
    payload["events"] = payload["events"][-200:]
    _atomic_write(EVENTS_PATH, payload)


def load_events(limit=None):
    ensure_files()
    with open(EVENTS_PATH, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    events = payload.get("events", [])
    if limit is not None:
        return events[-limit:]
    return events
