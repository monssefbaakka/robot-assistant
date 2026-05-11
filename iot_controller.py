import os
import threading
import time
import uuid
from copy import deepcopy
from datetime import datetime, timezone

from config_env import load_env_file
from iot_hardware_bridge import get_hardware_bridge
from iot_parser import parse_iot_command
from iot_simulator import advance_state, apply_command, apply_weather_update
from iot_store import append_event, load_events, load_state, reset_state, save_state
from mqtt_bus import get_loopback_broker
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


def _room_label(room_id):
    return str(room_id or "living_room").replace("_", " ").title()


def _hardware_expected_device_update(command):
    room_id = command.get("room") or "living_room"
    room_label = _room_label(room_id)
    device_type = command.get("device_type")
    sensor_type = command.get("sensor_type")
    action = command.get("action")

    if device_type == "light":
        if action == "turn_on":
            return {
                "topic_kind": "device",
                "target_id": "light_main",
                "matcher": lambda payload: payload.get("state") == "on",
                "result": {
                    "ok": True,
                    "action": action,
                    "room": room_id,
                    "device_type": device_type,
                    "message": f"{room_label} Main Light turned on.",
                },
            }
        if action == "set_brightness":
            brightness = command.get("parameters", {}).get("brightness")
            expected_state = "on" if int(brightness or 0) > 0 else "off"
            return {
                "topic_kind": "device",
                "target_id": "light_main",
                "matcher": lambda payload: payload.get("brightness") == brightness and payload.get("state") == expected_state,
                "result": {
                    "ok": True,
                    "action": action,
                    "room": room_id,
                    "device_type": device_type,
                    "message": f"{room_label} light brightness set to {brightness}%.",
                },
            }
        if action == "turn_off":
            return {
                "topic_kind": "device",
                "target_id": "light_main",
                "matcher": lambda payload: payload.get("state") == "off",
                "result": {
                    "ok": True,
                    "action": action,
                    "room": room_id,
                    "device_type": device_type,
                    "message": f"{room_label} Main Light turned off.",
                },
            }

    if device_type == "ac":
        if action == "turn_on":
            return {
                "topic_kind": "device",
                "target_id": "ac_main",
                "matcher": lambda payload: payload.get("state") == "on",
                "result": {
                    "ok": True,
                    "action": action,
                    "room": room_id,
                    "device_type": device_type,
                    "message": f"{room_label} Main AC turned on.",
                },
            }
        if action == "turn_off":
            return {
                "topic_kind": "device",
                "target_id": "ac_main",
                "matcher": lambda payload: payload.get("state") == "off",
                "result": {
                    "ok": True,
                    "action": action,
                    "room": room_id,
                    "device_type": device_type,
                    "message": f"{room_label} Main AC turned off.",
                },
            }
        if action == "set_temperature":
            target_temp = command.get("parameters", {}).get("target_temp")
            return {
                "topic_kind": "device",
                "target_id": "ac_main",
                "matcher": lambda payload: payload.get("target_temp") == target_temp,
                "result": {
                    "ok": True,
                    "action": action,
                    "room": room_id,
                    "device_type": device_type,
                    "message": f"{room_label} AC target temperature updated.",
                },
            }

    if device_type == "door":
        if action == "lock":
            return {
                "topic_kind": "device",
                "target_id": "door_main",
                "matcher": lambda payload: payload.get("state") == "locked",
                "result": {
                    "ok": True,
                    "action": action,
                    "room": room_id,
                    "device_type": device_type,
                    "message": f"{room_label} Front Door locked.",
                },
            }
        if action == "unlock":
            return {
                "topic_kind": "device",
                "target_id": "door_main",
                "matcher": lambda payload: payload.get("state") == "unlocked",
                "result": {
                    "ok": True,
                    "action": action,
                    "room": room_id,
                    "device_type": device_type,
                    "message": f"{room_label} Front Door unlocked.",
                },
            }

    if sensor_type == "gas_ppm":
        if action == "set_gas_state":
            enabled = bool(command.get("parameters", {}).get("enabled"))
            return {
                "topic_kind": "sensor",
                "target_id": "gas_ppm",
                "matcher": lambda payload: (
                    payload.get("value", payload) > 0 if enabled else payload.get("value", payload) == 0
                ),
                "result": {
                    "ok": True,
                    "action": action,
                    "room": room_id,
                    "sensor_type": sensor_type,
                    "message": f"{room_label} gas simulation turned {'on' if enabled else 'off'}.",
                },
            }
        if action == "set_gas_level":
            gas_ppm = command.get("parameters", {}).get("gas_ppm")
            return {
                "topic_kind": "sensor",
                "target_id": "gas_ppm",
                "matcher": lambda payload: payload.get("value", payload) == gas_ppm,
                "result": {
                    "ok": True,
                    "action": action,
                    "room": room_id,
                    "sensor_type": sensor_type,
                    "message": f"{room_label} gas level set to {gas_ppm} ppm.",
                },
            }

    return None


def _hardware_result_from_persisted_state(command, expected_device_update):
    if not expected_device_update:
        return None

    room_id = command.get("room") or "living_room"
    target_id = expected_device_update.get("target_id")
    topic_kind = expected_device_update.get("topic_kind", "device")
    if not target_id:
        return None

    try:
        state = load_state()
    except Exception:
        return None

    room = state.get("rooms", {}).get(room_id, {})
    if topic_kind == "sensor":
        payload = {"value": room.get("sensors", {}).get(target_id)}
    else:
        payload = room.get("devices", {}).get(target_id, {})
        if not isinstance(payload, dict):
            return None

    if expected_device_update["matcher"](payload):
        return deepcopy(expected_device_update["result"])
    return None


def _publish_room_state_via_broker(broker, state, room_id):
    room = state.get("rooms", {}).get(room_id)
    if not room:
        return

    for device_id, device in room.get("devices", {}).items():
        broker.publish(MQTTTopics.room_device_state(room_id, device_id), deepcopy(device))

    for sensor_name, value in room.get("sensors", {}).items():
        broker.publish(
            MQTTTopics.room_sensor_state(room_id, sensor_name),
            {"name": sensor_name, "value": value},
        )

    broker.publish(MQTTTopics.SNAPSHOT, deepcopy(state))


class IoTMQTTSimulatorService:
    """Virtual device service subscribed to MQTT topics."""

    def __init__(self, broker):
        self.broker = broker
        self._state_lock = threading.Lock()
        self._publish_interval_s = float(os.environ.get("IOT_SIM_PUBLISH_INTERVAL_S", "2.0"))
        self._subscription_id = self.broker.subscribe(MQTTTopics.COMMANDS, self._handle_command)
        self._publisher_thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._publisher_thread.start()
        self.publish_current_state()

    def _handle_command(self, envelope):
        payload = envelope["payload"]
        correlation_id = payload["correlation_id"]
        command = payload["command"]

        with self._state_lock:
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

    def _publish_loop(self):
        while True:
            try:
                self.publish_current_state()
            except Exception:
                pass
            time.sleep(max(self._publish_interval_s, 0.5))

    def publish_current_state(self):
        with self._state_lock:
            state = load_state()
            advance_state(state)
            save_state(state)
        for room_id in state.get("rooms", {}):
            self._publish_room_state(state, room_id)
        if state.get("alerts", {}).get("gas"):
            self.broker.publish(MQTTTopics.ALERT_GAS, {"alert": True, "message": "Gas leak detected!"})

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

    def _execute_local_room_fallback(self, command):
        state = load_state()
        advance_state(state)
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
        _publish_room_state_via_broker(self.broker, state, command.get("room"))
        self.broker.publish(MQTTTopics.EVENTS, event)
        return result

    def execute_command(self, command):
        correlation_id = str(uuid.uuid4())
        response_event = threading.Event()
        response_holder = {}
        state_event = threading.Event()
        state_holder = {}

        def on_response(envelope):
            payload = envelope["payload"]
            if payload.get("correlation_id") == correlation_id:
                response_holder["result"] = payload["result"]
                response_event.set()

        expected_device_update = None
        state_subscription_id = None
        if self.mode == "hardware":
            expected_device_update = _hardware_expected_device_update(command)
            if expected_device_update:
                room_id = command.get("room") or "living_room"
                if expected_device_update.get("topic_kind") == "sensor":
                    state_topic = MQTTTopics.room_sensor_state(room_id, expected_device_update["target_id"])
                else:
                    state_topic = MQTTTopics.room_device_state(room_id, expected_device_update["target_id"])

                def on_device_state(envelope):
                    payload = envelope.get("payload", {})
                    if not isinstance(payload, dict):
                        return
                    if expected_device_update["matcher"](payload):
                        state_holder["result"] = deepcopy(expected_device_update["result"])
                        state_event.set()

                state_subscription_id = self.broker.subscribe(state_topic, on_device_state)

        subscription_id = self.broker.subscribe(MQTTTopics.RESPONSES, on_response)
        try:
            self.broker.publish(
                MQTTTopics.COMMANDS,
                {
                    "correlation_id": correlation_id,
                    "command": deepcopy(command),
                },
            )
            deadline = time.time() + 10.0
            while time.time() < deadline:
                if response_event.wait(timeout=0.1):
                    break
                if state_event.is_set():
                    break
        finally:
            self.broker.unsubscribe(subscription_id)
            if state_subscription_id is not None:
                self.broker.unsubscribe(state_subscription_id)

        if "result" not in response_holder and "result" in state_holder:
            return state_holder["result"]

        if "result" not in response_holder and self.mode == "hardware":
            persisted_result = _hardware_result_from_persisted_state(command, expected_device_update)
            if persisted_result:
                return persisted_result

        if "result" not in response_holder:
            host = os.environ.get("MQTT_HOST", "localhost")
            port = os.environ.get("MQTT_PORT", "1883")
            callback_hint = ""
            if hasattr(self.broker, "get_callback_errors"):
                callback_errors = self.broker.get_callback_errors(limit=1)
                if callback_errors:
                    callback_hint = f" Last Python MQTT callback error: {callback_errors[0]['error']} on {callback_errors[0]['topic']}."
            if self.mode == "hardware":
                return {
                    "ok": False,
                    "error_code": "timeout",
                    "message": (
                        "No MQTT response came back from the hardware node. "
                        f"Check that Wokwi is running, subscribed to {MQTTTopics.COMMANDS}, "
                        f"and using the same broker as Python ({host}:{port}). "
                        "If you changed firmware config or diagram wiring, rebuild the ESP32 project from "
                        "firmware/wokwi/esp32-home-node/src/main.cpp and confirm the serial monitor shows "
                        "'MQTT connected' and 'Subscribed to: robocompagnon/home/commands'."
                        f"{callback_hint}"
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
        return load_state()

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
