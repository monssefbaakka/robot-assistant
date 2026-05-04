# MQTT Migration Change Audit

## 1. Executive Summary

This document records the changes made to the `RoboCompagnon` project to move it from a UI-level IoT simulation toward an MQTT-driven smart-home architecture.

Before these changes, the project contained:

- a conversational assistant
- a virtual robot
- a Streamlit dashboard
- weather integration
- reminders and Pomodoro logic
- simulated room data generated directly inside the UI

After these changes, the project now contains:

- a dedicated MQTT-style transport layer
- a persisted digital twin of a home
- a structured IoT command parser
- a virtual MQTT device service
- deterministic smart-home command execution
- event logging
- a dashboard driven by persisted IoT state instead of random sensor generation

The system is now architected around this workflow:

```text
User text
-> assistant routing
-> IoT intent parser
-> MQTT command topic
-> virtual device service
-> digital twin state mutation
-> event log + response topic + state topics
-> assistant/UI response
```

This is a real architectural shift. The project is no longer only "chatbot + random sensor values." It now behaves like a local MQTT smart-home simulator.

## 2. Scope of the Change

The scope of the implemented change includes:

- introducing a loopback MQTT transport abstraction
- creating a room/device/sensor digital twin
- storing home state and event history in JSON
- parsing smart-home commands from natural language
- applying those commands deterministically
- exposing MQTT topics for commands, responses, events, and state
- integrating the new IoT stack into `agent.py`
- replacing the old Streamlit IoT simulation logic in `app_complet.py`
- updating the architecture document to reflect the MQTT-based design

The scope does not include:

- external MQTT broker integration
- `paho-mqtt` client integration
- ESP32 / Raspberry Pi / Arduino device integration
- hardware GPIO or serial adapters
- multi-room device fleets beyond the first living-room slice

## 3. Architectural Delta

### Previous architecture

The previous system handled "IoT" behavior mainly in the UI layer:

- `app_complet.py` generated simulated sensor values directly
- those values were not the output of a digital twin
- there was no topic bus
- there was no command transport abstraction
- there was no device service subscribed to actuation commands
- there was no persisted event stream for smart-home actions

### New architecture

The new system introduces a message-driven smart-home flow:

1. Chat or dashboard produces a command.
2. The assistant routes the message to the IoT parser.
3. The parser emits a structured command object.
4. The controller publishes the command to an MQTT topic.
5. The virtual MQTT simulator service receives the message.
6. The simulator updates the persisted home twin.
7. The simulator emits:
   - a response topic message
   - an event topic message
   - room device/sensor state topic messages
8. The assistant and dashboard consume the resulting state.

This gives the project a realistic software architecture for later hardware replacement.

## 4. New Components Added

### 4.1 `mqtt_bus.py`

Purpose:

- provide an in-process MQTT-style broker
- support subscribe/publish semantics
- simulate topic-based messaging without an external broker

Key functions and classes:

- `_topic_matches()`
- `LoopbackMQTTBroker`
- `get_loopback_broker()`

Implemented capabilities:

- topic subscriptions
- wildcard matching with `+` and `#`
- local event dispatch for MQTT-style envelopes

Why it matters:

- this is the transport abstraction that makes the IoT workflow MQTT-shaped today
- it can later be swapped with a real broker client

### 4.2 `iot_store.py`

Purpose:

- persist IoT home state
- persist event history
- define the default smart-home twin

Key functions:

- `default_state()`
- `load_state()`
- `save_state()`
- `reset_state()`
- `append_event()`
- `load_events()`

Implemented capabilities:

- durable JSON persistence
- initial home topology
- reset support
- bounded event-history storage

Why it matters:

- the dashboard and assistant now work against stored state instead of temporary UI variables

### 4.3 `iot_parser.py`

Purpose:

- convert natural language into structured IoT commands

Key functions:

- `normalize_text()`
- `resolve_room()`
- `resolve_device_type()`
- `resolve_sensor_type()`
- `parse_iot_command()`

Implemented capabilities:

- room detection for `living_room`
- device detection for `light` and `ac`
- sensor detection for `temperature`, `humidity`, and `light_level`
- action detection for:
  - `turn_on`
  - `turn_off`
  - `set_temperature`
  - `get_sensor`
  - `get_device_state`

Why it matters:

- command handling is now deterministic and testable
- the LLM no longer needs to decide device state changes

### 4.4 `iot_simulator.py`

Purpose:

- advance room state over time
- apply smart-home commands to the home twin

Key functions:

- `advance_state()`
- `apply_command()`
- `apply_weather_update()`

Implemented capabilities:

- temperature drift toward outdoor conditions
- occupancy heat contribution
- solar gain effect
- AC cooling effect
- humidity drift
- daylight-driven light level
- immediate device state updates for actuation

Why it matters:

- sensor values are now derived from room/device state rather than generated randomly in the UI

### 4.5 `iot_controller.py`

Purpose:

- define the MQTT topic contract
- publish structured commands
- subscribe a virtual device service
- coordinate smart-home execution and retrieval

Key classes:

- `MQTTTopics`
- `IoTMQTTSimulatorService`
- `IoTMQTTController`

Implemented capabilities:

- MQTT-style command topic
- correlated response topic
- event topic
- room device state topics
- room sensor topics
- snapshot retrieval
- weather injection
- home reset support

Why it matters:

- this is the main entry point between assistant/UI and the smart-home simulator

### 4.6 `iot_state.json`

Purpose:

- define the initial digital twin state

Current contents:

- `living_room`
- `light_main`
- `ac_main`
- temperature/humidity/occupancy/light_level sensors
- outside weather section

Why it matters:

- the simulator now has a canonical persisted state

### 4.7 `iot_events.json`

Purpose:

- store the event log of MQTT smart-home actions

Why it matters:

- every command now has a traceable record

## 5. Existing Files Modified

### 5.1 `agent.py`

This file was modified to integrate the new IoT core.

Changes made:

- added safe import fallback for `langchain_community.llms.Ollama`
- instantiated the IoT controller
- forwarded weather updates into the digital twin
- added `gerer_commande_maison()`
- routed smart-home commands before the old generic chat path
- added graceful fallback messaging when the LLM dependency is missing

Effect:

- the assistant can now execute smart-home commands directly through MQTT routing
- the assistant no longer crashes if the LLM package is not installed

Important note:

- the legacy robot/reminder/Pomodoro behavior was preserved

### 5.2 `app_complet.py`

This file was heavily refactored.

Previous behavior:

- generated sensor values directly inside the dashboard
- simulated IoT conditions inside UI code

New behavior:

- initializes the assistant and weather feed
- reads from the persisted digital twin
- sends smart-home commands through the MQTT controller
- displays device cards for:
  - main light
  - main AC
- displays sensor cards for:
  - room temperature
  - room humidity
  - room light level
- displays recent MQTT event history
- preserves chat, reminders, Pomodoro, and voice playback

Effect:

- the dashboard is now a view of the IoT system, not the place where IoT simulation logic lives

### 5.3 `docs/iot-simulation-architecture.md`

This architecture document was updated to align with the implemented system.

Changes made:

- changed the architecture from six layers to seven
- introduced an explicit MQTT transport layer
- updated phase scope wording from "no MQTT" to "no external production MQTT broker operations"
- added `mqtt_bus.py` to the design

Effect:

- the project design documentation now matches the new implementation direction

## 6. MQTT Topic Contract Implemented

The current system defines the following topics:

- `robocompagnon/home/commands`
- `robocompagnon/home/responses`
- `robocompagnon/home/events`
- `robocompagnon/home/snapshot`
- `robocompagnon/home/rooms/living_room/devices/{device_id}/state`
- `robocompagnon/home/rooms/living_room/sensors/{sensor_name}`

These topics are exposed through `MQTTTopics` in `iot_controller.py`.

## 7. Functional Behaviors Added

The following smart-home behaviors are now supported:

### 7.1 Light actuation

Examples:

- "turn off the lights of the living room"
- "turn on the lights"

Effect:

- updates `light_main`
- publishes response and event
- updates room light-level calculation

### 7.2 AC actuation

Examples:

- "turn on the ac"
- "turn off the ac"
- "set the ac to 22"

Effect:

- updates `ac_main`
- changes temperature behavior over time
- publishes response and event

### 7.3 Sensor reads

Examples:

- "tell me the current temperature of the room"

Effect:

- reads the current room sensor state from the twin
- returns a deterministic answer

### 7.4 Weather influence

The external weather feed from `meteo.py` is now injected into the smart-home simulator.

Effect:

- outside temperature and humidity affect the room state evolution

## 8. Verification Performed

The following verification steps were performed during implementation:

### Syntax verification

These modules were compiled successfully:

- `mqtt_bus.py`
- `iot_store.py`
- `iot_parser.py`
- `iot_simulator.py`
- `iot_controller.py`
- `agent.py`
- `app_complet.py`

### Behavioral smoke tests

Executed successfully through the assistant path:

- `turn off the lights of the living room`
- `turn on the ac`
- `tell me the current temperature of the room`

Observed outcomes:

- device state transitions completed correctly
- responses were returned correctly
- room temperature was read from the digital twin

## 9. Constraints and Limitations

The current implementation is intentionally incomplete in several areas.

### 9.1 No external MQTT broker yet

The project uses a local loopback broker abstraction.

Implication:

- the architecture is MQTT-based
- the transport is not yet connected to Mosquitto or another real broker

### 9.2 No `paho-mqtt`

The environment currently does not have the `paho-mqtt` package installed.

Implication:

- external broker connectivity was not implemented in this pass

### 9.3 Single-room scope

The current digital twin includes only:

- one room
- one light
- one AC

Implication:

- the vertical slice is valid
- the home model is not yet scaled out

### 9.4 Legacy encoding artifacts

Some pre-existing files contain encoding issues in strings.

Implication:

- code remains functional
- documentation and UX strings are not fully normalized

### 9.5 `chat.py` was not deeply refactored

The main smart-home UX improvements were made through `agent.py` and `app_complet.py`.

Implication:

- CLI behavior benefits from the assistant routing changes
- the help text and dedicated CLI IoT presentation were not fully redesigned

## 10. Risks Introduced

### Risk: loopback MQTT is not the same as networked MQTT

Status:

- accepted for the current phase

Impact:

- transport behavior is realistic enough for architecture work
- deployment/network concerns are not yet exercised

### Risk: state and events are JSON-backed

Status:

- accepted for the current phase

Impact:

- suitable for local simulation
- may need database migration later

### Risk: parser is still narrow

Status:

- known limitation

Impact:

- only selected phrases and aliases are understood
- more robust language coverage is still needed

## 11. Project State After the Change

The project should now be described as:

- a smart-home MQTT simulator
- with a conversational assistant interface
- backed by a persisted digital twin
- with deterministic virtual device behavior
- and a clear path toward a real broker and real hardware

It should no longer be described as only a Streamlit dashboard with random virtual sensors.

## 12. Recommended Next Steps

The next engineering steps should be:

1. replace the loopback transport with a real MQTT client layer using `paho-mqtt`
2. run against a real broker such as Mosquitto
3. add more rooms and devices
4. extend parser coverage
5. add formal tests for parser, simulator, and controller
6. define a hardware adapter boundary for future ESP32 or Raspberry Pi nodes

## 13. Final Assessment

This change set successfully establishes the internal architecture required for an MQTT-based IoT project.

The implementation is not yet a production MQTT deployment, but it does achieve the most important technical milestone:

- the system now behaves according to an MQTT-driven smart-home workflow
- the UI is no longer the owner of the IoT simulation logic
- the assistant can now operate on a persistent digital twin through message-driven control

That is a meaningful architectural transition and a valid foundation for the next phase.
