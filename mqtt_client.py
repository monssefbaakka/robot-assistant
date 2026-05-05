import json
import os
import threading
import uuid
from datetime import datetime, timezone

from config_env import load_env_file

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None


def _topic_matches(topic_filter, topic):
    filter_parts = topic_filter.split("/")
    topic_parts = topic.split("/")

    for index, filter_part in enumerate(filter_parts):
        if filter_part == "#":
            return True
        if index >= len(topic_parts):
            return False
        if filter_part == "+":
            continue
        if filter_part != topic_parts[index]:
            return False

    return len(filter_parts) == len(topic_parts)


class PahoMQTTClient:
    """Real MQTT client using paho-mqtt. Same interface as LoopbackMQTTBroker."""

    def __init__(self, host="localhost", port=1883):
        if mqtt is None:
            raise RuntimeError("paho-mqtt not installed. Run: pip install paho-mqtt")

        self._lock = threading.Lock()
        self._subscriptions = {}
        self._next_id = 1
        self._connected = threading.Event()

        client_id = f"robocompagnon-{uuid.uuid4().hex[:8]}"
        self._client = mqtt.Client(client_id=client_id)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        self._client.connect(host, port, keepalive=60)
        self._client.loop_start()

        if not self._connected.wait(timeout=5.0):
            raise RuntimeError(f"Could not connect to MQTT broker at {host}:{port}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("#", qos=0)
            self._connected.set()

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            payload = msg.payload.decode("utf-8", errors="replace")

        envelope = {
            "topic": msg.topic,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with self._lock:
            subscriptions = list(self._subscriptions.items())

        for _, (topic_filter, callback) in subscriptions:
            if _topic_matches(topic_filter, msg.topic):
                callback(envelope)

    def subscribe(self, topic_filter, callback):
        with self._lock:
            subscription_id = self._next_id
            self._next_id += 1
            self._subscriptions[subscription_id] = (topic_filter, callback)
        return subscription_id

    def unsubscribe(self, subscription_id):
        with self._lock:
            self._subscriptions.pop(subscription_id, None)

    def publish(self, topic, payload):
        self._client.publish(topic, json.dumps(payload), qos=0)

    def disconnect(self):
        self._client.loop_stop()
        self._client.disconnect()


_CLIENT = None
_CLIENT_LOCK = threading.Lock()


def get_mqtt_client():
    global _CLIENT
    with _CLIENT_LOCK:
        if _CLIENT is None:
            load_env_file()
            host = os.environ.get("MQTT_HOST", "localhost")
            port = int(os.environ.get("MQTT_PORT", "1883"))
            _CLIENT = PahoMQTTClient(host=host, port=port)
    return _CLIENT
