import threading
from copy import deepcopy
from datetime import datetime, timezone

from iot_store import append_event, load_state, save_state
from mqtt_topics import MQTTTopics


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


class HardwareStateBridge:
    """Keeps the persisted digital twin in sync with hardware MQTT topics."""

    def __init__(self, broker):
        self.broker = broker
        self._lock = threading.Lock()
        self._subscription_ids = [
            self.broker.subscribe("robocompagnon/home/rooms/+/devices/+/state", self._on_device_state),
            self.broker.subscribe("robocompagnon/home/rooms/+/sensors/+", self._on_sensor_state),
            self.broker.subscribe(MQTTTopics.ALERT_GAS, self._on_gas_alert),
            self.broker.subscribe(MQTTTopics.EVENTS, self._on_event),
        ]

    def _update_state(self, updater):
        with self._lock:
            state = load_state()
            updater(state)
            state.setdefault("meta", {})["last_update"] = _now_iso()
            save_state(state)

    def _on_device_state(self, envelope):
        topic = envelope["topic"]
        payload = envelope["payload"]
        parts = topic.split("/")
        if len(parts) < 7:
            return
        room_id = parts[3]
        device_id = parts[5]
        if not isinstance(payload, dict):
            return

        def updater(state):
            room = state.setdefault("rooms", {}).setdefault(room_id, {"name": room_id, "devices": {}, "sensors": {}, "environment": {}})
            room.setdefault("devices", {})[device_id] = deepcopy(payload)

        self._update_state(updater)

    def _on_sensor_state(self, envelope):
        topic = envelope["topic"]
        payload = envelope["payload"]
        parts = topic.split("/")
        if len(parts) < 6:
            return
        room_id = parts[3]
        sensor_name = parts[5]

        if isinstance(payload, dict) and "value" in payload:
            sensor_value = payload["value"]
        else:
            sensor_value = payload

        def updater(state):
            room = state.setdefault("rooms", {}).setdefault(room_id, {"name": room_id, "devices": {}, "sensors": {}, "environment": {}})
            room.setdefault("sensors", {})[sensor_name] = sensor_value
            if sensor_name == "gas_ppm":
                state.setdefault("alerts", {})["gas"] = bool(sensor_value > 400)

        self._update_state(updater)

    def _on_gas_alert(self, envelope):
        payload = envelope["payload"]
        alert_value = bool(payload.get("alert")) if isinstance(payload, dict) else False

        def updater(state):
            state.setdefault("alerts", {})["gas"] = alert_value

        self._update_state(updater)

    def _on_event(self, envelope):
        payload = envelope["payload"]
        if isinstance(payload, dict):
            append_event(payload)


_BRIDGE = None
_BRIDGE_LOCK = threading.Lock()


def get_hardware_bridge(broker):
    global _BRIDGE
    with _BRIDGE_LOCK:
        if _BRIDGE is None:
            _BRIDGE = HardwareStateBridge(broker)
    return _BRIDGE
