"""
Diagnostic script — tests MQTT broker connectivity and ESP32 response.
Run this while Wokwi simulation is running.
"""
import json
import os
import threading
import time
import uuid

from config_env import load_env_file

load_env_file()

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("ERROR: paho-mqtt not installed. Run: pip install paho-mqtt")
    raise SystemExit(1)

BROKER = os.environ.get("MQTT_HOST", "broker.emqx.io")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
COMMANDS_TOPIC = "robocompagnon/home/commands"
RESPONSES_TOPIC = "robocompagnon/home/responses"
LISTEN_ALL = "robocompagnon/#"

received = []
connected = threading.Event()
response_received = threading.Event()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[OK] Connected to {BROKER}:{PORT}")
        client.subscribe(LISTEN_ALL)
        print(f"[OK] Subscribed to {LISTEN_ALL}")
        connected.set()
    else:
        print(f"[FAIL] Connection refused, rc={rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        payload = msg.payload.decode(errors="replace")
    received.append((msg.topic, payload))
    print(f"[MSG] {msg.topic} → {json.dumps(payload)[:120]}")
    if msg.topic == RESPONSES_TOPIC:
        response_received.set()

client_id = f"diag-{uuid.uuid4().hex[:8]}"
client = mqtt.Client(client_id=client_id)
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to {BROKER}:{PORT} ...")
client.connect(BROKER, PORT, keepalive=60)
client.loop_start()

if not connected.wait(timeout=8):
    print("[FAIL] Could not connect to broker within 8s. Check internet / broker.")
    raise SystemExit(1)

print("\nListening for 5s — any existing ESP32 publishes will appear above ...")
time.sleep(5)

print("\nSending light turn_on command ...")
correlation_id = str(uuid.uuid4())
payload = {
    "correlation_id": correlation_id,
    "command": {
        "action": "turn_on",
        "room": "living_room",
        "target_type": "device",
        "device_type": "light",
        "device_id": None,
        "parameters": {},
        "source": "diagnose",
        "raw_text": "turn on the light",
    },
}
client.publish(COMMANDS_TOPIC, json.dumps(payload))
print(f"[SENT] {COMMANDS_TOPIC}")

print("Waiting up to 15s for ESP32 response ...")
if response_received.wait(timeout=15):
    print("\n[SUCCESS] ESP32 responded! MQTT pipeline works.")
else:
    print("\n[FAIL] No response in 15s.")
    print("  Possible causes:")
    print("  1. Wokwi simulation not running")
    print("  2. ESP32 not connected to broker.emqx.io (check config.h)")
    print("  3. ESP32 connected to different broker")
    print("  4. Firmware not rebuilt after config.h change")
    if received:
        print(f"\n  NOTE: {len(received)} message(s) seen on broker (sensor publishes from ESP32?):")
        for t, p in received:
            print(f"    {t}")
    else:
        print("\n  NOTE: Zero messages seen — ESP32 is NOT publishing to this broker at all.")

client.loop_stop()
client.disconnect()
