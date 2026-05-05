# Task Log

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
