# System Architecture

## Overview

RoboCompagnon is a simulation-first IoT smart home assistant. All logic runs locally. No cloud dependency. The simulation layer is designed to be swapped for real ESP32 hardware without touching the layers above it.

---

## Layer Diagram

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

**Key rule**: UI and assistant only READ state. Only the virtual device service or hardware bridge WRITES state.

---

## Files and Responsibilities

| File | Role |
|---|---|
| `agent.py` | Routes user messages: IoT commands, weather, reminders, Pomodoro, robot movement |
| `iot_parser.py` | Converts natural language → structured command JSON |
| `iot_controller.py` | MQTT topic contract, publishes commands, receives responses, publishes alerts |
| `iot_simulator.py` | Physics simulation (temperature drift, AC cooling), edge rules (gas alert), apply_command |
| `iot_store.py` | Load/save `iot_state.json` and `iot_events.json` |
| `mqtt_bus.py` | Legacy in-process loopback MQTT broker (kept for reference) |
| `mqtt_client.py` | Real MQTT client used for Mosquitto-backed transport |
| `iot_hardware_bridge.py` | Hardware-mode state sync from MQTT device/sensor topics into `iot_state.json` |
| `app_complet.py` | Streamlit dashboard, reads digital twin state |
| `chat.py` | CLI entry point |
| `telegram_bot.py` | Telegram alert sender (Phase 5) |
| `meteo.py` | External weather API feed |

---

## Data Flow: Command Execution

```
User: "lock the door"
  1. agent.py → gerer_commande_maison()
  2. iot_controller.try_handle_text()
  3. iot_parser.parse_iot_command() → { action: "lock", device_type: "door", room: "living_room" }
  4. controller publishes to robocompagnon/home/commands
  5. IoTMQTTSimulatorService._handle_command() receives it
  6. iot_simulator.apply_command() → sets door_main.state = "locked"
  7. iot_store.save_state() → persists to iot_state.json
  8. iot_store.append_event() → logs to iot_events.json
  9. controller publishes to robocompagnon/home/rooms/living_room/devices/door_main/state
  10. controller publishes to robocompagnon/home/responses
  11. agent.py returns: "Living Room Front Door locked."
```

## Data Flow: Gas Alert (Edge Trigger)

```
Any command executes → apply_command() calls advance_state()
  → advance_state() checks gas_ppm in each room
  → if gas_ppm > 400: state["alerts"]["gas"] = True
  → controller._handle_command() sees alerts.gas == True
  → publishes to robocompagnon/home/alerts/gas: { alert: true, message: "Gas leak detected!" }
  (Phase 5: Telegram bot subscriber receives this and sends notification)
```

---

## Edge Computing Rules

All rules run inside `iot_simulator.py`. The assistant and UI make no safety decisions.

| Rule | Trigger | Action |
|---|---|---|
| Gas alert | gas_ppm > 400 | Set `alerts.gas = True`, publish alert topic |
| AC cooling | ac ON and temp > target | Reduce temperature each simulation step |
| AC humidity | ac ON | Reduce humidity 0.08% per minute |
| Solar gain | 8h–18h, sun_exposure > 0 | Increase temperature |
| Occupancy heat | occupancy = true | Small constant heat gain |

---

## Simulation → Real Hardware Swap

Replace only `IoTMQTTSimulatorService`. Everything above it (parser, controller, agent, UI) is unchanged.

```
TODAY                           FUTURE
─────────────────────           ──────────────────────
mqtt_bus.py loopback      →     Mosquitto broker TCP 1883
IoTMQTTSimulatorService   →     ESP32 firmware (paho-mqtt)
iot_simulator.py physics  →     Real ADC sensor readings
iot_state.json            →     ESP32 NVS flash
```

See `docs/hardware.md` for pin mapping and `docs/execution-plan.md` Phase 3 for migration steps.

---

## Current State (real-simulation branch)

- One room: `living_room`
- Devices: `light_main`, `ac_main`, `door_main`
- Sensors: `temperature`, `humidity`, `occupancy`, `light_level`, `gas_ppm`
- Alerts: `gas`
- Transport: Mosquitto via `mqtt_client.py`
- Modes:
- `IOT_MODE=simulator`: Python simulator service owns device behavior
- In simulator mode, the simulator also publishes periodic snapshot/device/sensor updates so the UI stays driven by simulation output
- `IOT_MODE=hardware`: external MQTT node (for example Wokwi ESP32) owns device behavior and `iot_hardware_bridge.py` syncs state back into JSON
- No physical hardware connected yet
