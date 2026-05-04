import threading
from datetime import datetime, timezone


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


class LoopbackMQTTBroker:
    """Small in-process broker for local MQTT-style simulation."""

    def __init__(self):
        self._lock = threading.Lock()
        self._subscriptions = {}
        self._next_id = 1

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
        with self._lock:
            subscriptions = list(self._subscriptions.items())

        envelope = {
            "topic": topic,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for _, (topic_filter, callback) in subscriptions:
            if _topic_matches(topic_filter, topic):
                callback(envelope)


_BROKER = None
_BROKER_LOCK = threading.Lock()


def get_loopback_broker():
    global _BROKER
    with _BROKER_LOCK:
        if _BROKER is None:
            _BROKER = LoopbackMQTTBroker()
    return _BROKER
