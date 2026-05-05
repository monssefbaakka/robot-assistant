import os
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone

from config_env import load_env_file
from iot_hardware_bridge import get_hardware_bridge
from iot_parser import parse_iot_command
from iot_simulator import advance_state, apply_command, apply_weather_update
from iot_store import append_event, load_events, load_state, reset_state, save_state
from mqtt_client import get_mqtt_client as get_loopback_broker
from mqtt_topics import MQTTTopics


class _GasAlertTelegramNotifier:
    """Subscribes to gas alert topic and forwards to Telegram if configured."""

    def __init__(self, broker):
        self._sub_id = broker.subscribe(MQTTTopics.ALERT_GAS, self._on_alert)

    def _on_alert(self, envelope):
        payload = envelope.get("payload", {})
        if not isinstance(payload, dict) or not payload.get("alert"):
            return
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id or "your_token" in token:
            return
        try:
            from telegram_bot import TelegramBot
            bot = TelegramBot(token)
            bot.chat_id = chat_id
            bot.envoyer_alerte_personnalisee(
                "Alerte Gaz",
                payload.get("message", "Gas leak detected!"),
                emoji="⚠️",
            )
        except Exception:
            pass


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


class IoTMQTTSimulatorService:
    """Virtual device service subscribed to MQTT topics."""

    def __init__(self, broker):
        self.broker = broker
        self._subscription_id = self.broker.subscribe(MQTTTopics.COMMANDS, self._handle_command)

    def _handle_command(self, envelope):
        payload = envelope["payload"]
        correlation_id = payload["correlation_id"]
        command = payload["command"]

        state = load_state()
        result = apply_command(state, command)
        save_state(state)

        event = {
            "timestamp": _now_iso(),
            "source": command.get("source", "mqtt"),
            "topic": MQTTTopics.COMMANDS,
            "room": command.get("room"),
            "action": command.get("action"),
            "target": command.get("device_type") or command.get("sensor_type") or command.get("device_id"),
            "status": "success" if result.get("ok") else "error",
            "raw_text": command.get("raw_text"),
            "details": result,
        }
        append_event(event)

        if state.get("alerts", {}).get("gas"):
            self.broker.publish(MQTTTopics.ALERT_GAS, {"alert": True, "message": "Gas leak detected!"})

        self._publish_room_state(state, command.get("room"))
        self.broker.publish(MQTTTopics.EVENTS, event)
        self.broker.publish(
            MQTTTopics.RESPONSES,
            {
                "correlation_id": correlation_id,
                "result": result,
            },
        )

    def _publish_room_state(self, state, room_id):
        room = state.get("rooms", {}).get(room_id)
        if not room:
            return

        for device_id, device in room.get("devices", {}).items():
            self.broker.publish(MQTTTopics.room_device_state(room_id, device_id), deepcopy(device))

        for sensor_name, value in room.get("sensors", {}).items():
            self.broker.publish(
                MQTTTopics.room_sensor_state(room_id, sensor_name),
                {"name": sensor_name, "value": value},
            )

        self.broker.publish(MQTTTopics.SNAPSHOT, deepcopy(state))


class IoTMQTTController:
    def __init__(self, broker=None):
        load_env_file()
        self.broker = broker or get_loopback_broker()
        self.mode = os.environ.get("IOT_MODE", "simulator").strip().lower()
        self._service = get_iot_service(self.broker) if self.mode != "hardware" else None
        self._bridge = get_hardware_bridge(self.broker) if self.mode == "hardware" else None
        self._gas_notifier = _GasAlertTelegramNotifier(self.broker)

    def try_handle_text(self, message, source="chat"):
        command = parse_iot_command(message, source=source)
        if not command:
            return None
        return self.execute_command(command)

    def execute_command(self, command):
        correlation_id = str(uuid.uuid4())
        response_event = threading.Event()
        response_holder = {}

        def on_response(envelope):
            payload = envelope["payload"]
            if payload.get("correlation_id") == correlation_id:
                response_holder["result"] = payload["result"]
                response_event.set()

        subscription_id = self.broker.subscribe(MQTTTopics.RESPONSES, on_response)
        try:
            self.broker.publish(
                MQTTTopics.COMMANDS,
                {
                    "correlation_id": correlation_id,
                    "command": deepcopy(command),
                },
            )
            response_event.wait(10.0)
        finally:
            self.broker.unsubscribe(subscription_id)

        if "result" not in response_holder:
            host = os.environ.get("MQTT_HOST", "localhost")
            port = os.environ.get("MQTT_PORT", "1883")
            if self.mode == "hardware":
                return {
                    "ok": False,
                    "error_code": "timeout",
                    "message": (
                        "No MQTT response came back from the hardware node. "
                        f"Check that Wokwi is running, subscribed to {MQTTTopics.COMMANDS}, "
                        f"and using the same broker as Python ({host}:{port})."
                    ),
                }
            return {
                "ok": False,
                "error_code": "timeout",
                "message": (
                    "MQTT command timed out before the simulator responded. "
                    f"Broker: {host}:{port}."
                ),
            }
        return response_holder["result"]

    def get_snapshot(self):
        state = load_state()
        if self.mode != "hardware":
            advance_state(state)
        state.setdefault("meta", {})["last_update"] = _now_iso()
        save_state(state)
        return state

    def get_recent_events(self, limit=10):
        events = load_events(limit=limit)
        return list(reversed(events))

    def update_outside_weather(self, meteo_data):
        state = load_state()
        advance_state(state)
        apply_weather_update(state, meteo_data)
        save_state(state)
        return state

    def reset(self):
        return reset_state()


_SERVICE = None
_SERVICE_LOCK = threading.Lock()


def get_iot_service(broker=None):
    global _SERVICE
    with _SERVICE_LOCK:
        if _SERVICE is None:
            _SERVICE = IoTMQTTSimulatorService(broker or get_loopback_broker())
    return _SERVICE


_CONTROLLER = None
_CONTROLLER_LOCK = threading.Lock()


def get_iot_controller():
    global _CONTROLLER
    with _CONTROLLER_LOCK:
        if _CONTROLLER is None:
            _CONTROLLER = IoTMQTTController()
    return _CONTROLLER
