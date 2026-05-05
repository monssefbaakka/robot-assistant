# Task Log

## Task: Hardware Mode Startup Alignment and Wokwi Diagnostics

### Status
Completed

### Goal
Make the Python app and the Wokwi ESP32 simulation line up reliably so MQTT commands produce visible hardware-state changes instead of only local chat confirmations.

### What Was Implemented
- Added automatic `.env` loading through `config_env.py`
- Updated the MQTT client, controller, store, chat CLI, and dashboard to read runtime settings from `.env`
- Added clearer hardware-mode timeout messages when the ESP32 node does not respond
- Added runtime mode and broker visibility in `chat.py` and `app_complet.py`
- Added a local `.env` with hardware mode and the same public broker currently used by the Wokwi firmware
- Updated `.gitignore` to keep `.env` out of git
- Documented the VS Code Wokwi caveat that PlatformIO builds `src/main.cpp`

### How It Works
1. When Python starts, it now loads `.env` from the repo root if the file exists.
2. `IOT_MODE`, `MQTT_HOST`, and `MQTT_PORT` are applied automatically without needing manual PowerShell exports each time.
3. In hardware mode, Python publishes the command and waits for the ESP32 MQTT response.
4. If no response arrives, the error now points directly to the likely cause: Wokwi not running, wrong broker, or wrong mode.
5. The chat CLI and dashboard show the active mode and broker so configuration mistakes are visible immediately.
6. The Wokwi simulation documentation now notes that VS Code + PlatformIO builds `src/main.cpp`, not `sketch.ino`.

### Files Changed
- `config_env.py`
- `mqtt_client.py`
- `iot_controller.py`
- `iot_store.py`
- `chat.py`
- `app_complet.py`
- `.env`
- `.env.example`
- `.gitignore`
- `docs/wokwi-simulation.md`
- `docs/task-log.md`

### MQTT Topics
- No topic names changed
- Runtime alignment verified against:
- `robocompagnon/home/commands`
- `robocompagnon/home/responses`
- `robocompagnon/home/rooms/living_room/devices/+/state`
- `robocompagnon/home/rooms/living_room/sensors/+`

### Hardware Involved
- Virtual ESP32 in Wokwi
- Light LED on GPIO26
- AC LED on GPIO27
- Door servo on GPIO18

### How To Test
1. Start the Wokwi ESP32 simulation from `firmware/wokwi/esp32-home-node/`.
2. Confirm `config.h` still points to the same broker as `.env`.
3. Run `py chat.py` or `py -m streamlit run app_complet.py` from the repo root.
4. Check the startup output or dashboard panel for `IOT_MODE=hardware` and the active broker.
5. Send `turn on light`.
6. Verify the Wokwi LED on GPIO26 changes state and the Python side receives a hardware MQTT response.

### Notes / Limitations
- Public brokers can be noisy and less reliable than a private reachable broker.
- If you use VS Code Wokwi with PlatformIO, update `src/main.cpp` for the built firmware path.
- If you use the Arduino/Wokwi sketch path, keep `sketch.ino` in sync with `src/main.cpp`.

## Task: real-simulation Branch and Wokwi Hardware Mode Prep

### Status
Completed

### Goal
Prepare a dedicated branch for moving device behavior from the Python simulator toward a Wokwi ESP32 home node while keeping the existing Python dashboard and chat flow usable.

### What Was Implemented
- Created branch `real-simulation`
- Added `IOT_MODE=hardware` support in `iot_controller.py`
- Added `iot_hardware_bridge.py` to sync MQTT device and sensor topics back into `iot_state.json`
- Added `mqtt_topics.py` to centralize topic constants
- Updated `iot_store.py` defaults to include door, gas sensor, alerts, and transport labeling
- Added Wokwi firmware scaffold in `firmware/wokwi/esp32-home-node/`
- Added:
- `sketch.ino`
- `diagram.json`
- `libraries.txt`
- `config.example.h`
- `README.md`
- Added `docs/wokwi-simulation.md`

### How It Works
1. In `IOT_MODE=hardware`, Python no longer owns device behavior through `IoTMQTTSimulatorService`.
2. Python still publishes commands and waits for MQTT responses.
3. The Wokwi ESP32 node is expected to subscribe to `robocompagnon/home/commands`.
4. The ESP32 node publishes device state, sensor state, events, and responses.
5. `iot_hardware_bridge.py` subscribes to those MQTT topics and updates `iot_state.json`.
6. Streamlit and chat keep reading the same persisted state file, so the rest of the app remains simple.

### Files Changed
- `iot_controller.py`
- `iot_store.py`
- `iot_hardware_bridge.py`
- `mqtt_topics.py`
- `app_complet.py`
- `.env.example`
- `.gitignore`
- `docs/mqtt-topics.md`
- `docs/architecture.md`
- `docs/wokwi-simulation.md`
- `docs/task-log.md`
- `firmware/wokwi/esp32-home-node/sketch.ino`
- `firmware/wokwi/esp32-home-node/diagram.json`
- `firmware/wokwi/esp32-home-node/libraries.txt`
- `firmware/wokwi/esp32-home-node/config.example.h`
- `firmware/wokwi/esp32-home-node/README.md`

### MQTT Topics
- No topic names changed
- Hardware mode expects the Wokwi node to publish:
- `robocompagnon/home/responses`
- `robocompagnon/home/events`
- `robocompagnon/home/alerts/gas`
- `robocompagnon/home/rooms/living_room/devices/+/state`
- `robocompagnon/home/rooms/living_room/sensors/+`

### Hardware Involved
- Virtual ESP32 in Wokwi
- DHT22
- two LEDs for light and AC
- servo for door lock
- potentiometer as gas surrogate
- photoresistor
- occupancy switch

### How To Test
1. Start a reachable MQTT broker.
2. Run Python with `IOT_MODE=hardware`.
3. Start the Wokwi ESP32 home node using the files in `firmware/wokwi/esp32-home-node/`.
4. Send a command such as `turn on the lights`.
5. Verify the ESP32 publishes a response and device state updates.
6. Verify `iot_state.json` updates and the dashboard reflects the new state.

### Notes / Limitations
- Wokwi cloud cannot connect directly to `localhost` on the PC.
- The provided firmware is a first hardware-simulation slice, not full production firmware.
- Real sensor calibration and robust MQTT reconnection behavior are intentionally kept simple.

## Task: Phase 3 MQTT Broker Import Switch

### Status
Completed

### Goal
Switch `iot_controller.py` from the in-process loopback import to the real MQTT client import while keeping the rest of the controller unchanged.

### What Was Implemented
- Replaced the `mqtt_bus.py` import in `iot_controller.py`
- Aliased `get_mqtt_client` to `get_loopback_broker` so the controller code path did not need a larger refactor
- Updated `docs/mqtt-topics.md` notes to reflect that the transport now goes through Mosquitto and `paho-mqtt`

### How It Works
1. `iot_controller.py` imports `get_mqtt_client` from `mqtt_client.py`.
2. The import is aliased to the previous broker function name, so controller construction stays unchanged.
3. Commands now publish to the local Mosquitto broker instead of the in-process loopback transport.
4. The virtual simulator service subscribes on the same broker and still publishes response, event, device, sensor, snapshot, and alert topics.

### Files Changed
- `iot_controller.py`
- `docs/mqtt-topics.md`
- `docs/task-log.md`

### MQTT Topics
- No topic names changed
- Transport verified on `robocompagnon/#`

### Hardware Involved
- None. This task changes broker transport only.

### How To Test
1. Start Mosquitto with `mosquitto -v`.
2. In a second terminal run `mosquitto_sub -t "robocompagnon/#" -v`.
3. Run the app or `py chat.py`.
4. Send a command such as `turn on the lights`.
5. Verify MQTT messages appear on the subscriber terminal for commands, responses, events, snapshot, and device state topics.

### Notes / Limitations
- The simulator still runs in Python; only the transport changed.
- The import alias is an intentional short transition step, not the final cleanup.

## Task: Streamlit Dashboard Cleanup and Phase 2 UI Alignment

### Status
Completed

### Goal
Fix the Streamlit interface so it reflects the current MQTT simulator state clearly and removes the confusing split between the new digital twin UI and the old legacy light demo.

### What Was Implemented
- Reworked `app_complet.py` into a clearer dashboard layout with a hero header and grouped sections
- Added dashboard visibility for Phase 2 features already present in state
- Added `door_main` lock status and lock/unlock controls
- Added `gas_ppm` sensor visibility and an active gas alert banner
- Added occupancy status and a room summary block
- Removed the separate legacy light control block from the visible UI to avoid conflicting control paths
- Added safer rendering for chat and event content using HTML escaping
- Added optional automatic voice playback for the latest robot response

### How It Works
1. The dashboard loads the persisted MQTT snapshot through `iot_controller.get_snapshot()`.
2. The interface reads living-room devices, sensors, and top-level alerts from that snapshot.
3. Device buttons publish commands through the same MQTT controller used by chat.
4. The event log renders recent simulator events from `iot_events.json`.
5. The chat area safely renders user and assistant messages without injecting raw HTML.
6. When auto-voice is enabled, the latest robot reply is converted to audio and played once after the response is generated.

### Files Changed
- `app_complet.py`
- `docs/task-log.md`

### MQTT Topics
- No new topics added
- Existing topics used by the interface:
- `robocompagnon/home/commands`
- `robocompagnon/home/responses`
- `robocompagnon/home/events`
- `robocompagnon/home/snapshot`
- `robocompagnon/home/alerts/gas`
- `robocompagnon/home/rooms/living_room/devices/door_main/state`

### Hardware Involved
- None. This task updates the simulation dashboard only.

### How To Test
1. Run `py -m streamlit run app_complet.py`.
2. Verify the page loads with sections for devices, sensors, events, and chat.
3. Confirm the door card is visible and use `Lock Door` or `Unlock Door`.
4. Confirm the gas level sensor card is visible.
5. Set `gas_ppm` above `400` in `iot_state.json`, refresh, and verify the gas alert banner appears.
6. Send a chat message such as `turn on the lights`.
7. Verify the device state updates and the event log records the command.
8. Verify chat messages render normally without broken markup.

### Notes / Limitations
- The dashboard still targets one room only: `living_room`.
- Voice playback still depends on `gTTS` network availability.
- The legacy connected-light code still exists in the repo for compatibility, but it is no longer shown as a primary dashboard control.

## Task: Phase 2 - Gas Detection + Door Lock + Edge Rules

### Status
Completed

### Goal
Add gas sensor monitoring with local edge alert logic and door lock/unlock control via MQTT commands.

### What Was Implemented
- `gas_ppm` sensor added to `living_room` sensors in `iot_state.json`
- `door_main` device (type: door) added to `living_room` devices in `iot_state.json`
- `alerts.gas` boolean flag added at top level of state
- `GAS_THRESHOLD = 400` constant in `iot_simulator.py`
- Gas edge rule in `advance_state()`: sets `state["alerts"]["gas"] = True` if any room gas_ppm > 400
- `lock` and `unlock` actions in `apply_command()` for door devices
- Door status message in `get_device_state` handler
- `gas_ppm` unit and warning message in `_sensor_message`
- `ALERT_GAS` topic constant in `iot_controller.py`
- Gas alert published to `robocompagnon/home/alerts/gas` after every command that triggers the threshold
- `door` added to `DEVICE_ALIASES` in `iot_parser.py`
- `gas_ppm` added to `SENSOR_ALIASES` in `iot_parser.py`
- `LOCK_PATTERNS` and `UNLOCK_PATTERNS` added to parser
- Lock/unlock command parsing for door device type
- Gas sensor query now also triggered by `STATUS_PATTERNS` ("gas status")

### How It Works
1. User sends `lock the door` and the parser returns `{action: lock, device_type: door}`.
2. The controller publishes the command to the MQTT bus.
3. The simulator sets `door_main.state = "locked"` and saves state.
4. The controller publishes the updated door state topic.
5. Each command execution runs `advance_state()`, which checks `gas_ppm > 400`.
6. If the threshold is exceeded, `alerts.gas = True` in state.
7. The controller detects the flag and publishes to `robocompagnon/home/alerts/gas`.

### Files Changed
- `iot_state.json`
- `iot_simulator.py`
- `iot_controller.py`
- `iot_parser.py`
- `docs/mqtt-topics.md`
- `docs/task-log.md`

### MQTT Topics
- `robocompagnon/home/alerts/gas`
- `robocompagnon/home/rooms/living_room/devices/door_main/state`

### Hardware Involved
- Gas sensor: simulated (maps to MQ-2 on GPIO34 when real hardware is used)
- Door lock: simulated (maps to SG90 servo on GPIO18 when real hardware is used)

### How To Test
1. Run `python chat.py`.
2. Type `lock the door` and expect: `Living Room Front Door locked.`
3. Type `unlock the door` and expect: `Living Room Front Door unlocked.`
4. Type `is the door locked?` and expect the current door state.
5. Type `what is the gas level?` and expect the gas ppm reading.
6. Edit `iot_state.json` and set `gas_ppm` to `500` in `living_room` sensors.
7. Send any MQTT command such as `turn on the lights`.
8. Verify `alerts.gas = true` in state and alert publication to `robocompagnon/home/alerts/gas`.

### Notes / Limitations
- Gas ppm value is static and must be set manually in `iot_state.json` for alert testing.
- The gas alert flag is set but not auto-cleared.
- Telegram notification is not yet wired.

## Task: MQTT IoT Simulator Foundation Cleanup

### Status
Completed

### Goal
Document the MQTT-based IoT simulator work already present in the branch and bring the repository into a cleaner publishable state without changing the feature scope.

### What Was Implemented
Added the missing documentation files required by the project rules:
- `docs/task-log.md`
- `docs/mqtt-topics.md`

Also prepared the repository to stop tracking generated Python cache files by adding `.gitignore` entries for `__pycache__/` and `*.pyc`.

### How It Works
1. The assistant parses a smart-home message into a structured command.
2. The controller publishes the command to a loopback MQTT topic.
3. The virtual MQTT simulator service applies the command to the persisted IoT state.
4. The simulator publishes response, event, snapshot, device, and sensor topics.
5. The dashboard and assistant read the updated state and recent events.
6. Generated Python cache files are now ignored so they do not keep polluting git changes.

### Files Changed
- `.gitignore`
- `docs/task-log.md`
- `docs/mqtt-topics.md`

### MQTT Topics
- `robocompagnon/home/commands`
- `robocompagnon/home/responses`
- `robocompagnon/home/events`
- `robocompagnon/home/snapshot`
- `robocompagnon/home/rooms/living_room/devices/light_main/state`
- `robocompagnon/home/rooms/living_room/devices/ac_main/state`
- `robocompagnon/home/rooms/living_room/sensors/temperature`
- `robocompagnon/home/rooms/living_room/sensors/humidity`
- `robocompagnon/home/rooms/living_room/sensors/occupancy`
- `robocompagnon/home/rooms/living_room/sensors/light_level`

### Hardware Involved
- None. This branch is simulation-only.

### How To Test
1. Run `python chat.py`.
2. Send a command such as `turn on the lights` or `set the ac to 22 degrees`.
3. Verify the assistant returns a success message.
4. Inspect `iot_state.json` and confirm the device state changed.
5. Inspect `iot_events.json` and confirm an event was recorded.
6. Run `streamlit run app_complet.py` and verify the dashboard reflects the same device and sensor state.

### Notes / Limitations
- The current transport is a local loopback MQTT simulation, not a real broker.
- The current implementation uses one room only: `living_room`.
- No real hardware documentation is kept in this branch because the current implementation is fully simulated.
