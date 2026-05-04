# Complete IoT Smart Home Robot — Execution Plan

## Current State Summary

Already implemented (do not rebuild):
- `mqtt_bus.py` — loopback MQTT broker with topic wildcards
- `iot_store.py` — JSON persistence (state + events)
- `iot_parser.py` — NL → structured command
- `iot_simulator.py` — physics simulation (temp, humidity, light)
- `iot_controller.py` — MQTT topic routing + virtual device service
- `agent.py` — assistant routing with IoT intent detection
- `app_complet.py` — Streamlit dashboard reading from digital twin

---

## 1. System Architecture

```
┌─────────────────────────────────────────────┐
│              USER INTERFACES                │
│   Streamlit UI │ CLI chat │ Telegram Bot    │
└──────────────────────┬──────────────────────┘
                       │ text / button press
┌──────────────────────▼──────────────────────┐
│              ASSISTANT LAYER                │
│      agent.py — route intent               │
│      iot_parser.py — NL → command          │
└──────────────────────┬──────────────────────┘
                       │ structured command JSON
┌──────────────────────▼──────────────────────┐
│           MQTT TRANSPORT LAYER              │
│   mqtt_bus.py (loopback) → later: paho     │
│   topics: commands / responses / events    │
└──────────────────────┬──────────────────────┘
                       │ MQTT publish/subscribe
┌──────────────────────▼──────────────────────┐
│         VIRTUAL DEVICE SERVICE              │
│   IoTMQTTSimulatorService in controller    │
│   - validates command                      │
│   - mutates digital twin                   │
│   - publishes state + event topics         │
└────────────┬──────────────────┬────────────┘
             │                  │
┌────────────▼───┐    ┌─────────▼──────────┐
│  iot_simulator │    │    iot_store.py    │
│  (physics sim) │    │  iot_state.json    │
│  temp/humidity │    │  iot_events.json   │
└────────────────┘    └────────────────────┘
```

**Key rule**: UI and assistant only READ state. Only the virtual device service WRITES state. This mirrors real hardware behavior where the device itself is the authority.

---

## 2. Simulation-First Architecture

Every simulated component maps to a future real component. Swap only the device adapter layer — nothing above it changes.

```
TODAY (simulation)              LATER (real hardware)
─────────────────────           ──────────────────────
IoTMQTTSimulatorService   →     ESP32 firmware + paho-mqtt
iot_simulator.py physics  →     Real sensor readings (ADC)
JSON state file           →     ESP32 NVS or local state
loopback mqtt_bus.py      →     Mosquitto broker (localhost)
python float temperature  →     DHT22 sensor via GPIO
python random gas value   →     MQ-2 analog sensor
python bool door state    →     Servo + GPIO pin
python bool light state   →     Relay module + GPIO
```

**Swap boundary**: Replace only `IoTMQTTSimulatorService`. The controller, parser, assistant, and UI change nothing.

---

## 3. Real Hardware Mapping Table

| Simulated Component | Real Hardware | Interface | ESP32 Pin |
|---|---|---|---|
| Temperature sensor | DHT22 | Digital GPIO | GPIO4 |
| Humidity sensor | DHT22 (same chip) | Digital GPIO | GPIO4 |
| Gas sensor | MQ-2 | Analog ADC | GPIO34 |
| Motion sensor | HC-SR501 PIR | Digital GPIO | GPIO5 |
| Light sensor | LDR + resistor divider | Analog ADC | GPIO35 |
| Light actuator | 5V Relay module | Digital GPIO | GPIO26 |
| AC actuator | 5V Relay module | Digital GPIO | GPIO27 |
| Door lock | SG90 Servo motor | PWM | GPIO18 |
| Communication | ESP32 WiFi | MQTT over TCP | — |
| Local broker | Mosquitto on PC | TCP 1883 | — |

---

## 4. MQTT Topic Map

```
robocompagnon/home/commands              ← controller publishes commands here
robocompagnon/home/responses             ← device service publishes results here
robocompagnon/home/events                ← device service logs every action
robocompagnon/home/snapshot              ← full state on demand

robocompagnon/home/rooms/{room}/devices/{device_id}/state
robocompagnon/home/rooms/{room}/sensors/{sensor_name}

robocompagnon/home/alerts/gas            ← gas leak alert (edge trigger)
robocompagnon/home/alerts/temperature    ← temperature threshold breach
```

**Rule**: Every new topic must be added to `docs/mqtt-topics.md`.

---

## 5. Data Flow Examples

### Light ON command

```
User: "turn on the lights"
  → agent.py detects IoT intent
  → iot_parser.py returns:
      { action: "turn_on", room: "living_room", device_type: "light" }
  → iot_controller publishes to robocompagnon/home/commands:
      { correlation_id: "abc123", command: {...} }
  → IoTMQTTSimulatorService receives it
  → apply_command() updates light_main.state = "on"
  → save_state() persists to iot_state.json
  → append_event() logs to iot_events.json
  → publishes to robocompagnon/home/rooms/living_room/devices/light_main/state
  → publishes to robocompagnon/home/responses: { ok: true, message: "..." }
  → agent.py returns: "Living room lights are now on."
```

### Gas alert (edge trigger)

```
Simulation tick runs:
  → gas sensor value crosses threshold (> 400 ppm simulated)
  → iot_simulator raises alert flag in state
  → iot_controller publishes to robocompagnon/home/alerts/gas
  → alert subscriber notifies Telegram bot
  → Telegram sends: "⚠ Gas leak detected in kitchen"
  (This logic runs locally — no cloud dependency)
```

---

## 6. Edge Computing Logic

All rules run **inside the simulated device service**, not in the assistant or UI.

```python
# In iot_simulator.py — advance_state() or apply_command()

# Rule 1: Auto AC
if temp > ac_target + 1.5 and ac_device["state"] == "off":
    ac_device["state"] = "on"   # local edge decision

# Rule 2: Night motion light
if not occupancy_light_on and hour >= 22 and motion_detected:
    light_device["state"] = "on"

# Rule 3: Gas alert (immediate, no MQTT roundtrip)
if gas_ppm > GAS_THRESHOLD:
    state["alerts"]["gas"] = True
    # publish alert topic immediately

# Rule 4: MQTT disconnect safety
# Device service keeps running local rules even if UI disconnects
# State is persisted — on reconnect, controller reads current state
```

**Rule**: Edge logic lives in `iot_simulator.py`. The assistant does NOT make device safety decisions.

---

## 7. Project Folder Structure

```
robot-assistant/
├── agent.py                  # assistant routing + IoT intent
├── app_complet.py            # Streamlit dashboard
├── chat.py                   # CLI entry point
├── mqtt_bus.py               # loopback MQTT broker
├── iot_parser.py             # NL → structured command
├── iot_simulator.py          # physics simulation + edge rules
├── iot_controller.py         # MQTT topic contract + device service
├── iot_store.py              # JSON persistence
├── iot_state.json            # digital twin state
├── iot_events.json           # event log
├── meteo.py                  # external weather feed
├── telegram_bot.py           # alert notifications
├── tts.py / voix.py          # voice I/O
├── rappels.py / pomodoro.py  # non-IoT assistant features
│
├── docs/
│   ├── task-log.md           # MANDATORY — task documentation
│   ├── mqtt-topics.md        # topic registry (CREATE)
│   ├── hardware.md           # hardware reference (CREATE)
│   ├── architecture.md       # system overview (UPDATE)
│   ├── execution-plan.md     # this file
│   └── iot-simulation-architecture.md
│
├── tests/
│   ├── test_parser.py        # CREATE
│   ├── test_simulator.py     # CREATE
│   └── test_controller.py   # CREATE
│
├── .env.example              # WiFi/MQTT/API keys template
└── AGENTS.md
```

---

## 8. Step-by-Step Implementation Roadmap

### Phase 1 — Stabilize & Document (current state) `[NOW]`

**Goal**: Verify end-to-end system works. Create missing docs.

1. Run `python chat.py` → test "turn on the lights" → verify response
2. Run `streamlit run app_complet.py` → verify device cards update
3. Create `docs/mqtt-topics.md` — register all existing topics
4. Create `docs/hardware.md` — document hardware mapping table
5. Update `docs/task-log.md` — document what was built
6. Verify `iot_state.json` and `iot_events.json` exist and are valid JSON

Commit: `docs: add mqtt-topics, hardware, and task-log for phase 1`

---

### Phase 2 — Gas Sensor + Door Lock + Edge Rules `[NEXT]`

**Goal**: Add missing sensors and local safety logic.

1. Add `gas` sensor to `iot_state.json` (ppm value + bool alert field)
2. Add `door` device to `iot_state.json` (state: locked/unlocked)
3. In `iot_simulator.py`: add gas threshold edge rule → sets alert flag in state
4. In `iot_controller.py`: publish to `robocompagnon/home/alerts/gas` when triggered
5. In `iot_parser.py`: add "lock door", "unlock door", "gas status" commands
6. In `agent.py`: handle gas alert response message
7. Test: set gas ppm > 400 in state → run chat.py → verify alert fires
8. Document in `docs/task-log.md`

Commit: `feat: add gas detection and door lock with edge alert logic`

---

### Phase 3 — Real Mosquitto MQTT `[INTERMEDIATE]`

**Goal**: Replace loopback bus with real local broker.

1. Install Mosquitto: `winget install mosquitto`
2. Install paho-mqtt: `pip install paho-mqtt`
3. Create `mqtt_client.py` — same interface as `mqtt_bus.py` but uses paho
4. In `iot_controller.py`: swap `get_loopback_broker()` → `get_mqtt_client()`
5. Test: `mosquitto_sub -t "robocompagnon/#"` in terminal → verify messages appear
6. Document broker config in `docs/architecture.md`

Commit: `feat: connect to real Mosquitto broker via paho-mqtt`

---

### Phase 4 — Multi-Room + Status Queries `[INTERMEDIATE]`

**Goal**: Add bedroom and kitchen. Full device status check.

1. Add rooms to `iot_state.json`: `bedroom`, `kitchen`
2. Extend `iot_parser.py` room aliases for new rooms
3. Add "check lights status", "is the door locked?" to parser
4. Add `get_device_state` execution in `iot_simulator.py`
5. Update dashboard — show all rooms in Streamlit
6. Document in `docs/task-log.md`

Commit: `feat: add bedroom and kitchen rooms with full status queries`

---

### Phase 5 — Telegram Alerts + Notifications

**Goal**: Route gas + temperature alerts to Telegram.

1. In `iot_controller.py`: subscribe to alert topics
2. On alert message: call `telegram_bot.py` send function
3. Test: trigger gas alert → Telegram message arrives
4. Add Telegram token to `.env.example` (NOT `.env`)

Commit: `feat: route gas and temperature alerts to Telegram notifications`

---

### Phase 6 — Formal Tests

**Goal**: Basic automated test coverage for critical logic.

Create `tests/test_parser.py`:
```python
def test_turn_on_light():
    cmd = parse_iot_command("turn on the lights")
    assert cmd["action"] == "turn_on"
    assert cmd["device_type"] == "light"

def test_set_temperature():
    cmd = parse_iot_command("set the ac to 20 degrees")
    assert cmd["action"] == "set_temperature"
    assert cmd["parameters"]["target_temp"] == 20
```

Create `tests/test_simulator.py`:
```python
def test_ac_cools_room():
    state = default_state()
    state["rooms"]["living_room"]["sensors"]["temperature"] = 30.0
    state["rooms"]["living_room"]["devices"]["ac_main"]["state"] = "on"
    state["rooms"]["living_room"]["devices"]["ac_main"]["target_temp"] = 22
    advanced = advance_state(state, now=now + timedelta(minutes=30))
    assert advanced["rooms"]["living_room"]["sensors"]["temperature"] < 30.0
```

Commit: `test: add parser and simulator unit tests`

---

### Phase 7 — Hardware Migration Prep (Future)

**Goal**: Define adapter boundary so swapping to real ESP32 is clean.

1. Create `device_adapter.py` with abstract interface:
```python
class DeviceAdapter:
    def turn_on(self, device_id): ...
    def turn_off(self, device_id): ...
    def read_sensor(self, sensor_id): ...
```
2. Create `SimulatedAdapter` (wraps existing simulator)
3. Create stub `ESP32MQTTAdapter` (empty, ready for real firmware)
4. In `iot_controller.py`: inject adapter via constructor
5. Document in `docs/architecture.md`

---

## 9. Documentation Plan

Every phase produces one entry in `docs/task-log.md` using the CLAUDE.md template.

Minimum per task:
- What was built
- Why
- Files changed
- MQTT topics added
- How to test
- Limitations

Missing docs to create now:
- `docs/mqtt-topics.md` — full topic registry
- `docs/hardware.md` — component + pin table
- `docs/architecture.md` — system diagram + layer description

---

## 10. Git Workflow

One branch per phase:
```
main
├── feat/phase-2-gas-door
├── feat/phase-3-real-mqtt
├── feat/phase-4-multi-room
└── feat/phase-5-telegram-alerts
```

Commit format (from CLAUDE.md):
```
feat: add gas detection with edge alert
fix: correct temperature drift formula
docs: update task-log for phase 2
test: add parser unit tests
refactor: extract device adapter boundary
```

Push rule: only push when task complete + tests pass + docs updated.

---

## 11. Testing Plan

### Manual smoke tests (per phase)

```
1. python chat.py
   > "turn on the lights"
   Expected: "Living room lights are now on."

2. python chat.py
   > "what is the temperature?"
   Expected: "Room temperature is 26.3°C"

3. python chat.py
   > "lock the door"
   Expected: "Door locked."

4. Manually set gas ppm > 400 in iot_state.json
   → run python chat.py
   → verify alert fires and Telegram message arrives
```

### Automated tests (Phase 6)

- `pytest tests/` — parser, simulator, controller
- Target: all core paths covered, no randomness in tests

### Regression check after each phase

- Non-IoT chat still works (reminders, Pomodoro, weather)
- Dashboard still loads
- State file still valid JSON

---

## 12. Final Demo Scenario

Run this sequence to demo the full system:

```
1. Start: streamlit run app_complet.py

2. Dashboard shows:
   - Living room: light OFF, AC OFF
   - Temperature: 28°C (from real weather via meteo.py)

3. User types: "turn on the lights"
   → Light card switches to ON

4. User types: "turn on the AC and set it to 21 degrees"
   → AC card shows ON, target 21°C

5. Wait 30 seconds → refresh dashboard
   → Temperature drops toward 21°C (simulation tick)

6. User types: "is the door locked?"
   → "Yes, the front door is locked."

7. User types: "unlock the door"
   → Door status updates

8. Trigger gas alert (edit iot_state.json gas ppm > 400)
   → Telegram message arrives
   → Dashboard shows alert banner

9. User types: "what is the humidity?"
   → Reads current sensor value from digital twin
```

Total demo time: ~5 minutes. No hardware needed.

---

## 13. Migration Plan: Simulation → Real ESP32

When ready for real hardware, follow these steps only.

### Step 1 — Broker already running (Phase 3 done)
No change needed.

### Step 2 — Flash ESP32 with same topic contract
- ESP32 subscribes to: `robocompagnon/home/commands`
- ESP32 publishes to: `robocompagnon/home/rooms/+/devices/+/state`
- Same JSON payload format — no changes to topics or schema

### Step 3 — Swap adapter in controller
```python
# Change one line in iot_controller.py
adapter = ESP32MQTTAdapter(broker_host="localhost")
# instead of
adapter = SimulatedAdapter()
```

### Step 4 — Disable simulator service
Comment out `IoTMQTTSimulatorService` initialization. Real ESP32 takes its place on the topic bus.

### Step 5 — Wire hardware

| Sensor/Actuator | ESP32 Pin | Firmware Call |
|---|---|---|
| DHT22 temperature | GPIO4 | `dht.readTemperature()` |
| MQ-2 gas | GPIO34 | `analogRead(34)` |
| HC-SR501 motion | GPIO5 | `digitalRead(5)` |
| Relay light | GPIO26 | `digitalWrite(26, HIGH)` |
| Relay AC | GPIO27 | `digitalWrite(27, HIGH)` |
| Servo door | GPIO18 | `servo.write(90)` |

**Nothing above the adapter layer changes.** Parser, controller, assistant, dashboard, Telegram — all identical.

---

## Immediate Next Actions (in order)

1. Verify Phase 1 works end-to-end — run `chat.py` and `app_complet.py`
2. Create `docs/mqtt-topics.md` — register all existing topics
3. Create `docs/hardware.md` — hardware mapping table
4. Add `docs/task-log.md` entry — document the MQTT migration already done
5. Start Phase 2 — gas sensor + door lock + edge rules
