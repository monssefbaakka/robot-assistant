# Task Log

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
