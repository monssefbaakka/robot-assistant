# RoboCompagnon IoT Simulation Architecture and Engineering Plan

## 1. Purpose

This document defines how to transform the current `RoboCompagnon` project from a robot-themed assistant into a simulation-first IoT project.

The goal is to simulate the exact workflow of a smart-home robot assistant before any real hardware exists. The software must behave as if real devices and sensors were connected, so that the hardware can later replace only the device adapter layer.

Primary target scenarios:

- "Turn off the lights of the living room"
- "Turn on the AC"
- "Tell me the current temperature of the room"

The system must support:

- natural language commands
- deterministic device control
- room-based device addressing
- sensor reading queries
- state persistence
- event logging
- realistic environment simulation over time

## 2. Current Project Context

The current repository already contains useful building blocks:

- `agent.py`: conversational assistant and command routing
- `robot.py`: virtual robot state and movement
- `app.py`: simple Streamlit UI
- `app_complet.py`: larger Streamlit UI with chat, weather, virtual sensors, Pomodoro, reminders, and voice output
- `meteo.py`: external weather retrieval
- `tts.py` and `voix.py`: voice output and speech input support
- `telegram_bot.py`: notification helper

The current "IoT" behavior is not yet modeled as a real smart-home system. Sensor values are mostly generated directly in the UI layer. Device control is not represented as a room/device architecture.

## 3. Target Positioning

The project should become:

- a smart-home IoT simulator
- with a conversational interface
- backed by a digital twin of a home
- with realistic device state transitions
- and a path to future hardware integration

This is the correct engineering direction because it preserves the full workflow:

- user speaks or types a command
- assistant extracts structured intent
- system validates the target device
- device state changes
- environment evolves over time
- sensors reflect the new environment
- assistant responds with deterministic feedback

## 4. Engineering Principle

The project must simulate the architecture of a real IoT system, not only fake outputs.

That means separating:

- user interaction
- intent parsing
- command execution
- device models
- environment simulation
- persistence
- visualization

This separation allows hardware integration later with minimal redesign.

## 5. Scope

### In scope

- digital twin of rooms, devices, and sensors
- smart-home command routing
- device actuation logic
- sensor query logic
- environment simulation loop
- event and state persistence
- Streamlit visualization
- support for deterministic command execution from chat

### Out of scope for the first version

- external production MQTT broker operations
- real ESP32/Arduino/Raspberry Pi integration
- camera vision
- autonomous navigation
- SLAM
- full voice pipeline integration
- advanced home automation scheduling

## 6. Product Vision

The system should behave like a local assistant connected to a simulated home.

Example interaction:

1. User says: "Turn off the lights of the living room."
2. The assistant parses the command.
3. The controller resolves the room and device.
4. The light state changes to `off`.
5. The event is logged.
6. The dashboard updates.
7. The assistant replies: "The living room lights are now off."

Example environment feedback:

1. User says: "Turn on the AC in the living room."
2. The AC state changes to `on`.
3. The room temperature gradually decreases over simulation ticks.
4. User later asks for room temperature.
5. The reported value is lower than before.

## 7. Target System Architecture

The recommended architecture has seven layers:

### Layer 1: Interaction Layer

Inputs:

- chat input from `chat.py`
- chat input from Streamlit
- future voice input

Outputs:

- human-readable response
- UI feedback

### Layer 2: Intent Layer

Responsibilities:

- detect whether a message is conversational or an IoT command
- convert user text into structured commands
- reject ambiguous or invalid commands

### Layer 3: MQTT Transport Layer

Responsibilities:

- publish commands on MQTT topics
- subscribe virtual devices to command topics
- publish state, response, and event topics
- preserve the same message flow expected by real IoT nodes

### Layer 4: IoT Controller Layer

Responsibilities:

- validate targets
- execute commands
- read sensor values
- update digital twin state
- generate execution results

### Layer 5: Device Layer

Responsibilities:

- represent devices such as lights and AC units
- maintain device-specific state
- expose actions such as `turn_on`, `turn_off`, `set_target_temperature`

### Layer 6: Environment Simulation Layer

Responsibilities:

- simulate room conditions over time
- update temperature, humidity, and occupancy impacts
- propagate device effects to sensor values

### Layer 7: Persistence and Observability Layer

Responsibilities:

- persist home state
- persist event log
- provide history for UI and debugging

## 8. Recommended New Modules

The next implementation phase should add the following files:

- `mqtt_bus.py`
- `iot_models.py`
- `iot_controller.py`
- `iot_simulator.py`
- `iot_parser.py`
- `iot_store.py`
- `iot_state.json`
- `iot_events.json`

Optional later additions:

- `iot_api.py`
- `iot_rules.py`
- `iot_scheduler.py`

## 9. Recommended Domain Model

The digital twin should model the home explicitly.

### Core entities

- `House`
- `Room`
- `Device`
- `Sensor`
- `Command`
- `Event`

### Room examples

- `living_room`
- `bedroom`
- `kitchen`

### Device examples

- `light_main`
- `ac_main`
- `heater_main`
- `fan_main`

### Sensor examples

- `temperature`
- `humidity`
- `occupancy`
- `light_level`

## 10. Suggested State Schema

Example `iot_state.json`:

```json
{
  "house": {
    "name": "Demo Home",
    "rooms": {
      "living_room": {
        "devices": {
          "light_main": {
            "id": "light_main",
            "type": "light",
            "state": "on",
            "brightness": 80,
            "power_w": 12
          },
          "ac_main": {
            "id": "ac_main",
            "type": "ac",
            "state": "off",
            "mode": "cool",
            "target_temp": 22,
            "fan_speed": 2,
            "power_w": 0
          }
        },
        "sensors": {
          "temperature": 27.4,
          "humidity": 48,
          "occupancy": true,
          "light_level": 540
        },
        "environment": {
          "thermal_mass": 0.85,
          "insulation_factor": 0.72,
          "sun_exposure": 0.65
        }
      }
    },
    "outside": {
      "temperature": 31.0,
      "humidity": 41,
      "weather_source": "wttr.in"
    }
  }
}
```

## 11. Command Model

The assistant must not directly control devices through free-form text. It should always convert text to a structured command.

### Example command schema

```json
{
  "action": "turn_off",
  "room": "living_room",
  "target_type": "device",
  "device_type": "light",
  "device_id": null,
  "parameters": {},
  "source": "chat",
  "raw_text": "turn off the lights of the living room"
}
```

### Supported action types for phase 1

- `turn_on`
- `turn_off`
- `get_sensor`
- `get_device_state`
- `set_temperature`

### Sensor query example

```json
{
  "action": "get_sensor",
  "room": "living_room",
  "target_type": "sensor",
  "sensor_type": "temperature",
  "parameters": {},
  "source": "chat",
  "raw_text": "tell me the current temperature of the room"
}
```

## 12. Core Workflow

### 12.1 User Command Workflow

1. User sends a text or voice command.
2. `agent.py` routes the message to the IoT intent parser.
3. The parser returns a structured command or `None`.
4. The controller validates the room and device/sensor.
5. The controller executes the action against the digital twin.
6. The controller writes an event entry.
7. The simulator updates the environment if needed.
8. The assistant returns a natural-language result.
9. The UI refreshes from persisted state.

### 12.2 Sensor Query Workflow

1. User requests a sensor value.
2. Intent parser returns `get_sensor`.
3. Controller reads the room sensor value from the twin.
4. Controller formats a deterministic result.
5. Assistant speaks or displays the answer.

### 12.3 Device Actuation Workflow

1. User requests a device change.
2. Intent parser identifies action, room, and device type.
3. Controller locates the target device.
4. Controller checks whether the command is valid.
5. Device state is updated.
6. Event is stored with previous and new state.
7. Environment simulation reflects the new state over time.

## 13. Parsing Strategy

The parser should be deterministic first and LLM-assisted second.

### Recommendation

Use keyword and pattern matching for phase 1:

- "turn on"
- "turn off"
- "lights"
- "AC"
- "temperature"
- "living room"
- "bedroom"

This is better than using the LLM directly for execution because:

- it is safer
- it is testable
- it avoids hallucinated actions
- it is easy to map to hardware later

### Parsing output contract

The parser must return:

- `action`
- `room`
- `target`
- optional parameters
- confidence or parse status

If parsing fails, the assistant should ask a clarification question.

## 14. Controller Logic

The controller should be the single owner of home-state mutations.

Responsibilities:

- resolve room aliases
- resolve device aliases
- validate action compatibility
- apply state changes
- save state
- log events
- return machine result plus message

### Example execution result

```json
{
  "ok": true,
  "action": "turn_off",
  "room": "living_room",
  "device_id": "light_main",
  "old_state": { "state": "on", "brightness": 80 },
  "new_state": { "state": "off", "brightness": 0 },
  "message": "Living room lights turned off."
}
```

## 15. Device Behavior Design

### Light device

State fields:

- `state`: `on` or `off`
- `brightness`: `0` to `100`
- `power_w`

Rules:

- `turn_on` sets `state=on`
- `turn_off` sets `state=off` and `brightness=0`
- brightness affects room light level

### AC device

State fields:

- `state`
- `mode`
- `target_temp`
- `fan_speed`
- `power_w`

Rules:

- `turn_on` enables AC operation
- `turn_off` disables climate effect
- `set_temperature` updates target temperature
- when active, the AC affects room temperature gradually

## 16. Environment Simulation Design

The environment must evolve logically, not randomly.

### Principles

- sensor values must depend on room state
- device actions must have delayed physical effect
- outside weather should influence indoor conditions
- occupancy can affect heat and energy usage

### Temperature simulation inputs

- outside temperature
- room temperature
- AC state
- AC target temperature
- room insulation factor
- occupancy heat contribution
- time of day

### Simplified temperature update algorithm

For each simulation tick:

```text
room_temp_next =
    room_temp_current
    + outside_drift
    + occupancy_heat
    + solar_gain
    - ac_cooling_effect
```

Where:

- `outside_drift` moves indoor temperature slowly toward outdoor temperature
- `occupancy_heat` adds a small positive increment if the room is occupied
- `solar_gain` adds heat during bright daytime periods
- `ac_cooling_effect` reduces temperature until the target is approached

### Example formulas

```text
outside_drift = (outside_temp - room_temp) * 0.02 * (1 - insulation_factor)
occupancy_heat = 0.03 if occupancy else 0.0
solar_gain = 0.04 * sun_exposure during daytime else 0.0
ac_cooling_effect = 0.18 if ac_on and room_temp > target_temp else 0.0
```

This is simple, explainable, and sufficient for a phase-1 simulator.

### Humidity simulation inputs

- outside humidity
- AC state
- time evolution

Example rule:

- indoor humidity drifts slowly toward outside humidity
- AC slightly reduces humidity over time

### Light level simulation inputs

- natural daylight
- room lights state
- time of day

Example rule:

- daytime baseline increases light level
- light device adds a fixed artificial-light contribution when on

## 17. Simulation Execution Strategy

There are two valid approaches:

### Option A: Compute on demand

Each time a command or UI refresh happens:

- compare current time with last update time
- compute elapsed duration
- advance the simulation for the elapsed period

Advantages:

- simple
- no background thread required
- stable inside Streamlit

### Option B: Background tick loop

Run a simulator thread that updates state every second.

Advantages:

- more "live"

Disadvantages:

- more complexity
- more concurrency risk in Streamlit

### Recommendation

Use **Option A** for phase 1.  
It is easier to keep deterministic and easier to debug.

## 18. Event Logging

Every command should produce an event log entry.

Example `iot_events.json` entry:

```json
{
  "timestamp": "2026-05-04T22:10:00",
  "source": "chat",
  "room": "living_room",
  "action": "turn_off",
  "target": "light_main",
  "status": "success",
  "raw_text": "turn off the lights of the living room",
  "details": {
    "old_state": { "state": "on", "brightness": 80 },
    "new_state": { "state": "off", "brightness": 0 }
  }
}
```

The log serves four purposes:

- debugging
- UI history
- future analytics
- traceability for hardware migration

## 19. Failure Handling

The simulator must support realistic failure paths.

Examples:

- room not found
- device not found
- sensor offline
- command ambiguous
- device already in requested state

Recommended behavior:

- controller returns structured error
- assistant converts it into a user-friendly message

Example:

```json
{
  "ok": false,
  "error_code": "device_not_found",
  "message": "No AC device found in the kitchen."
}
```

## 20. Suggested Implementation Plan

### Phase 1: Minimal Smart-Home Twin

Deliverables:

- one room: `living_room`
- one light
- one AC
- one temperature sensor
- parser for simple commands
- controller execution
- state persistence
- event log

User stories:

- turn light on/off
- turn AC on/off
- ask for room temperature

### Phase 2: Better Environment Model

Deliverables:

- humidity
- light level
- occupancy
- outside weather integration from `meteo.py`
- time-based evolution

### Phase 3: Dashboard Upgrade

Deliverables:

- room cards
- device status panels
- sensor panels
- event history panel
- manual device toggles
- charts for temperature evolution

### Phase 4: Assistant Integration

Deliverables:

- route IoT commands through `agent.py`
- keep reminders/Pomodoro/chat features intact
- ensure deterministic IoT execution before LLM fallback

### Phase 5: Hardware Migration Prep

Deliverables:

- define hardware adapter interface
- replace virtual device implementation with real adapter stubs
- prepare MQTT or REST abstraction

## 21. Integration Into Existing Files

### `agent.py`

Add:

- IoT intent detection
- parser invocation
- controller invocation
- response formatting

Rule:

- if an IoT command is detected, run deterministic execution first
- only use the LLM for normal conversation or clarification

### `app_complet.py`

Refactor:

- move sensor generation out of the UI layer
- read from the IoT simulator state instead
- display rooms, devices, and sensors directly from the digital twin

### `chat.py`

No major redesign required.

It should remain a lightweight entry point that:

- builds the agent
- sends messages
- prints the response

## 22. Data Persistence Strategy

Use JSON initially for simplicity:

- `iot_state.json` for current twin state
- `iot_events.json` for event history

Later migration options:

- SQLite
- TinyDB
- Postgres

JSON is acceptable for phase 1 because:

- the project is local
- the state volume is small
- it is easy to inspect manually

## 23. Algorithmic Reference

### 23.1 Parse command

```text
function parse_iot_command(text):
    normalize text
    detect room alias
    detect device or sensor target
    detect action
    detect optional parameters
    if action or target missing:
        return parse_failure
    return structured_command
```

### 23.2 Execute command

```text
function execute_command(command):
    load current state
    advance simulation to current time
    validate room
    validate target
    apply action to device or sensor request
    persist new state
    append event log
    return result
```

### 23.3 Advance simulation

```text
function advance_simulation(state, now):
    elapsed = now - last_update_time
    if elapsed <= 0:
        return state
    for each room:
        compute outside drift
        compute occupancy effect
        compute solar effect
        compute AC effect
        update temperature
        update humidity
        update light level
    set last_update_time = now
    return state
```

### 23.4 Reply formatting

```text
function format_result(result):
    if result.ok:
        return success message
    return error or clarification message
```

## 24. Testing Strategy

### Unit tests

Test:

- room resolution
- device lookup
- command parsing
- device actuation
- sensor reads
- simulation tick logic

### Scenario tests

Test full flows:

1. turn off living-room light
2. turn on AC
3. ask for temperature immediately
4. advance simulation
5. ask for temperature again

### Regression tests

Ensure:

- non-IoT chat still works
- reminders still work
- Pomodoro still works

## 25. Acceptance Criteria

The first IoT simulation milestone is complete when:

- the living room exists in state storage
- light and AC can be controlled by text commands
- room temperature is readable
- AC changes the temperature over time
- every command is logged
- the Streamlit UI reflects actual twin state
- command execution is deterministic and not based solely on the LLM

## 26. Future Hardware Migration

The architecture should support replacing virtual devices with real adapters.

### Current model

```text
Controller -> Virtual Device Object -> JSON State
```

### Future model

```text
Controller -> Hardware Adapter -> MQTT / REST / GPIO / Serial -> Real Device
```

The command schema must remain stable across both models.

This is the central engineering design rule of the project.

## 27. Risks and Mitigations

### Risk: Overusing the LLM for execution

Mitigation:

- use the LLM only for conversation and fallback clarification
- keep IoT execution rule-based

### Risk: UI owns the simulation logic

Mitigation:

- move simulation into dedicated modules
- let the UI only render state

### Risk: Random outputs feel unrealistic

Mitigation:

- use explicit physical rules
- use time-based drift instead of pure randomness

### Risk: Tight coupling makes hardware migration hard

Mitigation:

- enforce controller and adapter boundaries early

## 28. Recommended First Build Order

1. Create `iot_models.py`
2. Create `iot_store.py`
3. Create `iot_simulator.py`
4. Create `iot_controller.py`
5. Create `iot_parser.py`
6. Add IoT routing into `agent.py`
7. Refactor `app_complet.py` to visualize the twin
8. Add tests

## 29. Final Recommendation

Do not evolve the project as "chatbot + random smart-home numbers."

Evolve it as:

- a digital twin of a home
- with deterministic command execution
- with realistic device behavior
- with lightweight environment physics
- and a clear hardware adapter boundary

That will give the project real engineering value now and make it credible as an IoT project later.

## 30. Immediate Next Step

The next coding step should implement a phase-1 digital twin for:

- `living_room`
- `light_main`
- `ac_main`
- `temperature` sensor

and connect it to:

- `agent.py`
- `chat.py`
- `app_complet.py`

This is the smallest useful vertical slice of the future IoT architecture.
