# RoboCompagnon

IoT smart home assistant. Natural language commands control simulated (or real) home devices over MQTT.

---

## Features

- Control lights, AC, doors, buzzers per room
- Gas leak detection with automatic alerts
- Temperature/humidity physics simulation
- Streamlit dashboard, CLI chat, Telegram bot
- Two modes: Python simulator or real ESP32 hardware

---

## Architecture

```
User (Streamlit / CLI / Telegram)
        │
    agent.py  ──  iot_parser.py (NL → command JSON)
        │
    iot_controller.py
        │  MQTT
    IoTMQTTSimulatorService          ← swap for ESP32 to go real
        │
    iot_simulator.py  +  iot_store.py
    (physics, edge rules)   (iot_state.json, iot_events.json)
```

**Key rule:** UI and assistant only read state. Only the simulator service or hardware bridge writes state.

---

## Rooms and Devices

| Room | Devices | Sensors |
|---|---|---|
| living_room | light, AC, door, buzzer | temp, humidity, occupancy, light\_level, gas\_ppm |
| kitchen | light, buzzer | temp, humidity, occupancy, light\_level, gas\_ppm |
| bedroom | light, AC, door, buzzer | temp, humidity, occupancy, light\_level |
| toilet | light, door, buzzer | temp, humidity, occupancy, light\_level |
| garage | light, door, buzzer | temp, humidity, occupancy, light\_level |

---

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start MQTT broker (Mosquitto)

```bash
mosquitto
```

### 3. Configure environment

```bash
cp .env.example .env
# edit .env — set GROQ_API_KEY and IOT_MODE
```

### 4. Run

```bash
# Streamlit dashboard
streamlit run app_complet.py

# CLI chat
python chat.py
```

---

## Modes

| `IOT_MODE` | Behavior |
|---|---|
| `simulator` | Python physics simulation owns device state |
| `hardware` | ESP32 (Wokwi or real) owns device state; `iot_hardware_bridge.py` syncs back to JSON |

Set in `.env`:

```
IOT_MODE=simulator
```

---

## MQTT Topics (summary)

| Topic | Direction | Purpose |
|---|---|---|
| `robocompagnon/home/commands` | publish | Send device commands |
| `robocompagnon/home/responses` | subscribe | Command results |
| `robocompagnon/home/events` | subscribe | Event log |
| `robocompagnon/home/snapshot` | subscribe | Full state dump |
| `robocompagnon/home/rooms/{room}/devices/{device}/state` | subscribe | Per-device state |
| `robocompagnon/home/rooms/{room}/sensors/{sensor}` | subscribe | Per-sensor readings |
| `robocompagnon/home/alerts/gas` | subscribe | Gas leak alert (>400 ppm) |

Full topic list: [`docs/mqtt-topics.md`](docs/mqtt-topics.md)

---

## Edge Computing Rules

All safety logic runs inside `iot_simulator.py` — no cloud dependency.

| Trigger | Action |
|---|---|
| `gas_ppm > 400` | Set gas alert, publish alert topic |
| AC ON + temp > target | Cool room each simulation step |
| 08:00–18:00, sun exposure | Increase room temperature |
| Occupancy = true | Small constant heat gain |

---

## ESP32 / Wokwi Simulation

Firmware lives in `firmware/wokwi/esp32-home-node/`.

See [`firmware/wokwi/esp32-home-node/README.md`](firmware/wokwi/esp32-home-node/README.md) for pin mapping, setup, and VS Code workflow.

> Wokwi cloud cannot reach `localhost`. Use a public MQTT broker (e.g. `broker.emqx.io`) when running in Wokwi cloud.

---

## Project Structure

```
robot_assistant/
├── agent.py                  # Intent routing
├── iot_parser.py             # NL → command JSON
├── iot_controller.py         # MQTT publish/subscribe
├── iot_simulator.py          # Physics + edge rules
├── iot_store.py              # State persistence
├── mqtt_client.py            # Paho-MQTT client
├── iot_hardware_bridge.py    # Hardware-mode state sync
├── app_complet.py            # Streamlit dashboard
├── chat.py                   # CLI entry point
├── telegram_bot.py           # Telegram alerts
├── meteo.py                  # Weather API
├── firmware/
│   └── wokwi/esp32-home-node/
├── docs/
│   ├── architecture.md
│   ├── mqtt-topics.md
│   ├── hardware.md
│   ├── task-log.md
│   └── ...
└── .env.example
```

---

## Security

Never commit real credentials. Use `.env` (gitignored) and `config.example.h` for ESP32 config.

---

## Docs

- [Architecture](docs/architecture.md)
- [MQTT Topics](docs/mqtt-topics.md)
- [Hardware](docs/hardware.md)
- [Task Log](docs/task-log.md)
