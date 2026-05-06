# Task Log

## Task: Add Visible Door Lock Indicators In Wokwi

### Status
Completed

### Goal
Make the Wokwi simulation clearly show whether the door is locked or unlocked without relying only on subtle servo movement.

### What Was Implemented
- Added a red `door locked` LED on `GPIO19`
- Added a green `door unlocked` LED on `GPIO25`
- Updated firmware so `setDoorLocked()` drives both LEDs with the servo

### How It Works
1. When the door is locked, the red LED turns on and the green LED turns off.
2. When the door is unlocked, the green LED turns on and the red LED turns off.
3. The servo still moves, but now the state is obvious in the simulation.

### Files Changed
- `firmware/wokwi/esp32-home-node/src/main.cpp`
- `firmware/wokwi/esp32-home-node/sketch.ino`
- `firmware/wokwi/esp32-home-node/diagram.json`
- `docs/task-log.md`

### MQTT Topics
- No topic changes

### Hardware Involved
- Virtual ESP32 in Wokwi
- Door servo on GPIO18
- Red lock LED on GPIO19
- Green unlock LED on GPIO25

### How To Test
1. Rebuild the Wokwi firmware.
2. Restart the Wokwi simulation.
3. Send `lock the door`.
4. Verify the red LED turns on.
5. Send `unlock the door`.
6. Verify the green LED turns on.

### Notes / Limitations
- This is a visibility improvement for the simulation. The MQTT door state flow was already working.

## Task: Increase Door Servo Travel In Wokwi

### Status
Completed

### Goal
Make lock and unlock visibly different in the Wokwi simulation so door movement is easier to see.

### What Was Implemented
- Changed the Wokwi door servo angles from `90/0` to `180/0`

### How It Works
1. `locked` now drives the servo to `180`
2. `unlocked` drives the servo to `0`
3. The wider range makes the servo movement easier to notice in the simulator

### Files Changed
- `firmware/wokwi/esp32-home-node/src/main.cpp`
- `firmware/wokwi/esp32-home-node/sketch.ino`
- `docs/task-log.md`

### MQTT Topics
- No topic changes

### Hardware Involved
- Virtual ESP32 in Wokwi
- Door servo on GPIO18

### How To Test
1. Rebuild the Wokwi firmware.
2. Restart the Wokwi simulation.
3. Send `unlock the door`.
4. Send `lock the door`.
5. Verify the servo now rotates more visibly between the two states.

### Notes / Limitations
- The buzzer is unrelated to the door path; it only depends on active unconfirmed gas.

## Task: Fix Door Servo Direction In Wokwi

### Status
Completed

### Goal
Align the website lock status with the visible Wokwi servo position by correcting the lock and unlock servo angles.

### What Was Implemented
- Reversed the Wokwi door servo angle mapping so `locked` and `unlocked` match the visible simulation position.
- Added explicit `DOOR_LOCKED_ANGLE` and `DOOR_UNLOCKED_ANGLE` constants for easier adjustment later.

### How It Works
1. The firmware still publishes `door_main.state` as `locked` or `unlocked`.
2. The servo output angle now matches that logical state in the Wokwi diagram.
3. If needed later, the two constants can be swapped again without touching the command logic.

### Files Changed
- `firmware/wokwi/esp32-home-node/src/main.cpp`
- `firmware/wokwi/esp32-home-node/sketch.ino`
- `docs/task-log.md`

### MQTT Topics
- No topic changes
- Existing door state topic remains:
- `robocompagnon/home/rooms/living_room/devices/door_main/state`

### Hardware Involved
- Virtual ESP32 in Wokwi
- Door servo on GPIO18

### How To Test
1. Rebuild the Wokwi firmware.
2. Restart the Wokwi simulation.
3. Send `lock the door`.
4. Verify the servo moves to the visually locked position and the website shows `locked`.
5. Send `unlock the door`.
6. Verify the servo moves to the visually unlocked position and the website shows `unlocked`.

### Notes / Limitations
- This is a visual orientation fix for the Wokwi servo, not a change to the MQTT status flow.

## Task: Clarify Door Status Versus Door Action In Dashboard

### Status
Completed

### Goal
Avoid confusion where the website shows `Lock` while the door is actually unlocked, because the button represented the next action rather than the current state.

### What Was Implemented
- Updated the door card meta text to show `Current: Locked` or `Current: Unlocked`
- Renamed the door buttons to `Action: Lock Door` and `Action: Unlock Door`

### How It Works
1. The dashboard still reads the live `door_main.state` value from MQTT-backed state.
2. The card now explicitly labels the displayed value as the current state.
3. The button now clearly indicates that it is an action, not the current status.

### Files Changed
- `app_complet.py`
- `docs/task-log.md`

### MQTT Topics
- No topic changes
- Live status still comes from:
- `robocompagnon/home/rooms/living_room/devices/door_main/state`

### Hardware Involved
- Virtual ESP32 in Wokwi
- Door servo on GPIO18

### How To Test
1. Restart the dashboard.
2. Lock or unlock the door from chat or button.
3. Verify the card shows `Current: Locked` or `Current: Unlocked`.
4. Verify the button text shows the next action as `Action: Lock Door` or `Action: Unlock Door`.

### Notes / Limitations
- This is a UI wording fix only; the underlying lock state flow was already correct.

## Task: Add Unconfirmed Gas Buzzer Safety Rule

### Status
Completed

### Goal
Add a local safety alarm so the robot starts beeping if gas is activated and left unconfirmed for 30 seconds.

### What Was Implemented
- Added parser support for confirmation phrases like `it's me who did it`, `i confirm`, and `confirm gas`
- Added simulator-side 30-second gas confirmation timer
- Added `buzzer_main` device state to the shared IoT state
- Added Wokwi buzzer support on `GPIO32`
- Added hardware-side gas confirmation timer and buzzer beeping logic
- Added dashboard warning banners for pending confirmation and active buzzer alarm

### How It Works
1. A gas-on or gas-level command arms a 30-second confirmation window.
2. If the user confirms ownership before timeout, the buzzer stays off.
3. If the user does not confirm and gas is still active after 30 seconds, the buzzer turns on and starts beeping.
4. Turning gas off clears the safety alarm state.

### Files Changed
- `iot_parser.py`
- `iot_simulator.py`
- `iot_store.py`
- `iot_hardware_bridge.py`
- `app_complet.py`
- `firmware/wokwi/esp32-home-node/src/main.cpp`
- `firmware/wokwi/esp32-home-node/sketch.ino`
- `firmware/wokwi/esp32-home-node/diagram.json`
- `docs/hardware.md`
- `docs/mqtt-topics.md`
- `firmware/wokwi/esp32-home-node/README.md`
- `docs/wokwi-simulation.md`
- `docs/task-log.md`

### MQTT Topics
- `robocompagnon/home/commands`
- `robocompagnon/home/rooms/living_room/devices/buzzer_main/state`
- `robocompagnon/home/rooms/living_room/sensors/gas_ppm`

### Hardware Involved
- Virtual ESP32 in Wokwi
- Gas sensor input on GPIO34
- Gas alert LED on GPIO33
- Gas safety buzzer on GPIO32

### How To Test
1. Rebuild and restart the Wokwi firmware.
2. Send `turn the gaz on and make it at the maximum level`.
3. Do not confirm.
4. Wait 30 seconds.
5. Verify the buzzer starts beeping and the dashboard shows the buzzer warning.
6. Send `it's me who did it` or `confirm gas`.
7. Verify the buzzer stops.

### Notes / Limitations
- In simulator mode, the buzzer is represented by `buzzer_main.state` and dashboard alerts.
- In Wokwi, the gas slider still does not move automatically because it is an input widget.

## Task: Add Visible Gas Alarm Feedback In Wokwi

### Status
Completed

### Goal
Make gas commands produce a visible change in the Wokwi diagram instead of only changing MQTT state and website values.

### What Was Implemented
- Added a red gas alert LED to `firmware/wokwi/esp32-home-node/diagram.json`
- Wired the LED to `GPIO33`
- Updated ESP32 firmware so the LED turns on whenever `gas_ppm > 400`
- Updated hardware and Wokwi documentation

### How It Works
1. Gas level is still read from the sensor input or the command override.
2. After sensor publishing, the firmware checks whether `gas_ppm > 400`.
3. If true, it turns the red alert LED on.
4. This gives visible feedback in the Wokwi simulation even though the gas sensor slider itself does not move automatically.

### Files Changed
- `firmware/wokwi/esp32-home-node/src/main.cpp`
- `firmware/wokwi/esp32-home-node/sketch.ino`
- `firmware/wokwi/esp32-home-node/diagram.json`
- `docs/hardware.md`
- `firmware/wokwi/esp32-home-node/README.md`
- `docs/wokwi-simulation.md`
- `docs/task-log.md`

### MQTT Topics
- No new topics
- Existing gas state flow still uses:
- `robocompagnon/home/rooms/living_room/sensors/gas_ppm`
- `robocompagnon/home/alerts/gas`

### Hardware Involved
- Virtual ESP32 in Wokwi
- Gas sensor input on GPIO34
- Red alert LED on GPIO33

### How To Test
1. Rebuild the Wokwi firmware.
2. Restart the Wokwi simulation.
3. Send `turn the gaz on and make it at the maximum level`.
4. Verify the website gas level rises.
5. Verify the red gas alert LED turns on in the Wokwi diagram.

### Notes / Limitations
- The gas sensor slider itself is still an input widget and will not move automatically from a command.
- The visible feedback is now the red alert LED, not the slider position.

## Task: Fix Gas Max Command Parsing

### Status
Completed

### Goal
Make the robot understand natural gas-control phrases like `turn the gaz on and make it at the maximum level`.

### What Was Implemented
- Updated `iot_parser.py` to accept:
- `gaz` as well as `gas`
- `maximum` / `max` as gas level `1000`
- `minimum` / `min` as gas level `0`
- four-digit gas ppm values like `1000 ppm`

### How It Works
1. The parser now detects gas phrases with either English `gas` or French-style `gaz`.
2. If the command mentions maximum gas level, it maps directly to `set_gas_level` with `1000 ppm`.
3. If the command mentions minimum gas level, it maps to `0 ppm`.

### Files Changed
- `iot_parser.py`
- `docs/task-log.md`

### MQTT Topics
- `robocompagnon/home/commands`

### Hardware Involved
- Virtual ESP32 in Wokwi

### How To Test
1. Restart the Python app.
2. Send `turn the gaz on and make it at the maximum level`.
3. Verify the parser produces `set_gas_level` with `1000`.
4. Verify the website gas value rises and gas alert becomes active.

### Notes / Limitations
- This fixes the command understanding path.
- The Wokwi gas sensor module itself is still an input component, so its knob or physical drawing will not move automatically from a chat command.

## Task: Add Mermaid Workflow And Sensor Control Documentation

### Status
Completed

### Goal
Create a clear `/docs` document that explains the full robot workflow, the sensor flows, and how the robot controls devices using Mermaid diagrams.

### What Was Implemented
- Added `docs/robot-workflow-diagrams.md`
- Documented the end-to-end robot command flow
- Documented simulator mode and hardware mode
- Added Mermaid diagrams for global workflow, command execution, robot control map, sensor and actuator relationships, gas alert logic, temperature and humidity flow, occupancy flow, light flow, and actuator control

### How It Works
1. The new document starts from the user command and shows how the assistant, parser, controller, MQTT, simulator, ESP32, and dashboard connect together.
2. It explains each sensor in simple words and shows how the value moves through MQTT into the shared state.
3. It shows how light, AC, and door commands become hardware or simulated actions.
4. It includes the gas leak edge rule and the difference between simulator mode and hardware mode.

### Files Changed
- `docs/robot-workflow-diagrams.md`
- `docs/task-log.md`

### MQTT Topics
- `robocompagnon/home/commands`
- `robocompagnon/home/responses`
- `robocompagnon/home/rooms/living_room/devices/light_main/state`
- `robocompagnon/home/rooms/living_room/devices/ac_main/state`
- `robocompagnon/home/rooms/living_room/devices/door_main/state`
- `robocompagnon/home/rooms/living_room/sensors/temperature`
- `robocompagnon/home/rooms/living_room/sensors/humidity`
- `robocompagnon/home/rooms/living_room/sensors/occupancy`
- `robocompagnon/home/rooms/living_room/sensors/light_level`
- `robocompagnon/home/rooms/living_room/sensors/gas_ppm`
- `robocompagnon/home/alerts/gas`

### Hardware Involved
- DHT22
- MQ-2 gas sensor
- PIR occupancy sensor
- LDR
- Light output on GPIO26
- AC output on GPIO27
- Door servo on GPIO18
- ESP32

### How To Test
1. Open `docs/robot-workflow-diagrams.md`.
2. Confirm the Mermaid blocks render in your Markdown viewer.
3. Compare the diagrams with the current Python simulator and ESP32 firmware flows.
4. Verify the documented topics and GPIO references match the current repo files.

### Notes / Limitations
- This task adds documentation only. No runtime behavior was changed.
- The document reflects the current one-room setup: `living_room`.

## Task: Add Light Brightness And Gas Level Control

### Status
Completed

### Goal
Let the robot control light brightness and gas simulation state and level through the existing MQTT command flow.

### What Was Implemented
- Added parser support for:
- `set light brightness to 60%`
- `turn gas on`
- `turn gas off`
- `set gas level to 300 ppm`
- Added simulator support for `set_brightness`, `set_gas_state`, and `set_gas_level`
- Updated hardware-mode command confirmation to accept brightness and gas updates
- Added Wokwi firmware support for light brightness state and gas override commands
- Updated MQTT and hardware documentation

### How It Works
1. The robot parses brightness and gas commands into structured MQTT commands.
2. In simulator mode, the simulator updates `light_main.brightness` or `sensors.gas_ppm`.
3. In hardware mode, the ESP32 firmware applies the same command and republishes device or sensor topics.
4. The Python side reads those updates and reflects them in the shared state file and UI.

### Files Changed
- `iot_parser.py`
- `iot_simulator.py`
- `iot_controller.py`
- `firmware/wokwi/esp32-home-node/src/main.cpp`
- `firmware/wokwi/esp32-home-node/sketch.ino`
- `docs/mqtt-topics.md`
- `docs/hardware.md`
- `docs/task-log.md`

### MQTT Topics
- `robocompagnon/home/commands`
- `robocompagnon/home/responses`
- `robocompagnon/home/rooms/living_room/devices/light_main/state`
- `robocompagnon/home/rooms/living_room/sensors/gas_ppm`

### Hardware Involved
- Virtual ESP32 in Wokwi
- Light output on GPIO26
- Gas sensor input on GPIO34 with command override mode

### How To Test
1. Start the Python app.
2. In simulator mode, send:
3. `set light brightness to 35%`
4. `turn gas on`
5. `set gas level to 250 ppm`
6. Verify `iot_state.json` updates `light_main.brightness` and `sensors.gas_ppm`.
7. In hardware mode, rebuild the Wokwi firmware and restart the simulator.
8. Send the same commands and verify the device and sensor MQTT topics update.

### Notes / Limitations
- In Wokwi, light brightness is represented as state and power values; the output pin still behaves as a simple on/off demo actuator.
- Gas control uses a firmware override mode after a gas command is sent, which is simpler than adding a separate virtual gas actuator.

## Task: Fix Dashboard Event Timestamp Rendering For Wokwi Events

### Status
Completed

### Goal
Prevent the dashboard terminal from crashing when hardware-mode events use integer millisecond timestamps instead of ISO datetime strings.

### What Was Implemented
- Updated `app_complet.py` event rendering to format both numeric and string timestamps safely.
- Added support for Wokwi firmware event timestamps coming from `millis()`.
- Kept existing support for ISO timestamps produced by the Python simulator and controller.

### How It Works
1. The dashboard reads recent events from `iot_events.json`.
2. Before rendering an event row, the timestamp is passed through a small formatter.
3. If the timestamp is numeric, it is converted from milliseconds to `HH:MM:SS`.
4. If the timestamp is a string, the formatter extracts the visible time safely.
5. If the value is missing or unusual, the formatter falls back to a safe placeholder instead of crashing.

### Files Changed
- `app_complet.py`
- `docs/task-log.md`

### MQTT Topics
- No new topics
- Existing event flow:
- `robocompagnon/home/events`

### Hardware Involved
- Virtual ESP32 in Wokwi

### How To Test
1. Run `py -m streamlit run app_complet.py`.
2. Start the Wokwi ESP32 node in hardware mode.
3. Send a device command such as `turn on light` or `lock door`.
4. Verify the terminal event list renders normally.
5. Verify no `TypeError: object of type 'int' has no len()` appears.

### Notes / Limitations
- Numeric timestamps from Wokwi are displayed as elapsed device uptime, not wall-clock local time.

## Task: Accept Hardware State Sync As Command Success

### Status
Completed

### Goal
Stop the website from showing a failed hardware command when the ESP32 device state already changed and the hardware bridge already wrote that change into `iot_state.json`.

### What Was Implemented
- Updated `iot_controller.py` so hardware mode now falls back to persisted device state after a response timeout.
- If the expected device state is already present in `iot_state.json`, the command returns success instead of a timeout error.

### How It Works
1. Python still waits for the MQTT `responses` topic first.
2. In hardware mode, Python also watches for the expected device-state update.
3. If neither callback result is available in time, Python checks the persisted state written by the hardware bridge.
4. If the device already reached the expected state, the website treats the command as successful.

### Files Changed
- `iot_controller.py`
- `docs/task-log.md`

### MQTT Topics
- `robocompagnon/home/responses`
- `robocompagnon/home/rooms/living_room/devices/light_main/state`
- `robocompagnon/home/rooms/living_room/devices/ac_main/state`
- `robocompagnon/home/rooms/living_room/devices/door_main/state`

### Hardware Involved
- Virtual ESP32 in Wokwi

### How To Test
1. Fully restart the Python dashboard in hardware mode.
2. Start the Wokwi ESP32 node on the same broker.
3. Click `Turn On` for the light.
4. Verify the website shows the light as `ON`.
5. Verify the website does not show a timeout if the state file already updated correctly.

### Notes / Limitations
- This fallback covers device actions that have a clear expected state.
- It does not replace the normal MQTT response path; it only prevents false failures when the state sync already proves the command succeeded.

## Task: Limit Public Broker Subscription Scope

### Status
Completed

### Goal
Fix website timeouts and stale UI in hardware mode by stopping the Python MQTT client from subscribing to unrelated public-broker traffic.

### What Was Implemented
- Updated `mqtt_client.py` so the Paho client subscribes only to `robocompagnon/home/#` instead of `#`.

### How It Works
1. On connection, Python now listens only to this project's MQTT namespace.
2. The app no longer processes unrelated traffic from the whole public broker.
3. Response callbacks and hardware bridge updates can be handled with much less delay and noise.

### Files Changed
- `mqtt_client.py`
- `docs/task-log.md`

### MQTT Topics
- `robocompagnon/home/#`

### Hardware Involved
- Virtual ESP32 in Wokwi

### How To Test
1. Fully stop the running Streamlit or Python app.
2. Start it again in hardware mode.
3. Click `Turn On` for the light.
4. Verify the website updates and the timeout message no longer appears.

### Notes / Limitations
- This fix requires a full app restart because the old running MQTT client stays connected with the previous broad subscription.

## Task: Bind Dashboard Device Cards To Live Simulation State

### Status
Completed

### Goal
Make the Active Devices section read its visible status from the live simulation snapshot instead of relying on hardcoded card text.

### What Was Implemented
- Updated `app_complet.py` so device cards now render their `name`, `id`, and `state` directly from `iot_state.json` through the current MQTT snapshot flow.
- Added a small live meta line on each card using simulation values:
- Light card: brightness and room light level
- AC card: room temperature and AC target temperature
- Door card: lock state and occupancy status
- Changed the AC badge to show `ON` or `OFF` from the device state instead of always showing only the target temperature.

### How It Works
1. The dashboard reads the current snapshot from the IoT controller.
2. The living-room device objects and sensor values are extracted from that snapshot.
3. Each card now uses the live device object for display fields.
4. Extra card details are built from the current sensor values in the same room.
5. When the simulator or hardware bridge updates `iot_state.json`, the cards refresh with the new values.

### Files Changed
- `app_complet.py`
- `docs/task-log.md`

### MQTT Topics
- No new topics
- Existing live state flow used by the dashboard:
- `robocompagnon/home/rooms/living_room/devices/light_main/state`
- `robocompagnon/home/rooms/living_room/devices/ac_main/state`
- `robocompagnon/home/rooms/living_room/devices/door_main/state`
- `robocompagnon/home/rooms/living_room/sensors/temperature`
- `robocompagnon/home/rooms/living_room/sensors/light_level`
- `robocompagnon/home/rooms/living_room/sensors/occupancy`

### Hardware Involved
- None required for the UI change itself
- Works with both Python simulator mode and Wokwi hardware mode because both feed the same persisted state

### How To Test
1. Run `py -m streamlit run app_complet.py`.
2. Open the dashboard and inspect the Active Devices section.
3. Toggle the light, AC, or door from chat or buttons.
4. Verify the card badge updates from the live device state.
5. Verify the card code matches the current device `id` from state.
6. Verify the meta line updates from current room sensors and device values.

### Notes / Limitations
- The dashboard still assumes one room: `living_room`.
- The cards depend on the stored snapshot being updated correctly by the simulator or hardware bridge.

## Task: Accept Hardware Device State As Command Success

### Status
Completed

### Goal
Fix the case where the ESP32 or Wokwi hardware actually applies a device command, but the Python app still reports a timeout because the separate MQTT response topic was missed.

### What Was Implemented
- Updated `iot_controller.py` hardware mode so it also watches the expected device state topic for actionable commands.
- Added simple fallback success handling for:
- `light_main` turn on/off
- `ac_main` turn on/off
- `ac_main` set temperature
- `door_main` lock/unlock
- Kept the existing `robocompagnon/home/responses` path for normal command replies and status/sensor queries.

### How It Works
1. Python still publishes the command to `robocompagnon/home/commands`.
2. In hardware mode, Python now also subscribes briefly to the expected device state topic for that command.
3. If the hardware publishes the matching new state first, Python returns success immediately.
4. If a normal MQTT response arrives, Python still uses that response.
5. Only if neither the response nor the expected state arrives does Python return the timeout message.

### Files Changed
- `iot_controller.py`
- `docs/task-log.md`

### MQTT Topics
- `robocompagnon/home/commands`
- `robocompagnon/home/responses`
- `robocompagnon/home/rooms/living_room/devices/light_main/state`
- `robocompagnon/home/rooms/living_room/devices/ac_main/state`
- `robocompagnon/home/rooms/living_room/devices/door_main/state`

### Hardware Involved
- Virtual ESP32 in Wokwi
- Door servo on GPIO18
- Light output on GPIO26
- AC output on GPIO27

### How To Test
1. Run the Python app with `IOT_MODE=hardware`.
2. Start the Wokwi ESP32 node on the same broker.
3. Send `unlock the door`.
4. Verify the servo moves and `door_main` publishes `state = unlocked`.
5. Verify the Python reply now reports success instead of the old timeout message, even if `robocompagnon/home/responses` is delayed or absent.

### Notes / Limitations
- This fallback only applies to commands where success can be confirmed from a device state update.
- Sensor queries and device status questions still require the normal `robocompagnon/home/responses` payload.

## Task: Fix Python Hardware Receive Path Stability

### Status
Completed

### Goal
Fix the case where Wokwi executes the command but the website still times out and does not refresh, by stabilizing the Python MQTT receive path.

### What Was Implemented
- Hardened `mqtt_client.py` so one callback exception does not stop delivery to other MQTT subscribers.
- Added callback error collection for MQTT receive diagnostics.
- Added a store lock in `iot_store.py` to avoid concurrent read/write issues between the Streamlit UI thread and the MQTT callback thread.
- Updated `iot_controller.py` timeout messages to include the most recent Python-side callback error when available.

### How It Works
1. Python still subscribes to all required MQTT topics.
2. When a topic arrives, each callback is now wrapped separately.
3. If one callback fails, the error is recorded, but other callbacks still run.
4. Hardware bridge updates and command responses can continue reaching the app instead of silently stopping after the first callback error.

### Files Changed
- mqtt_client.py
- iot_store.py
- iot_controller.py
- docs/task-log.md

### MQTT Topics
- robocompagnon/home/responses
- robocompagnon/home/rooms/living_room/devices/light_main/state
- robocompagnon/home/rooms/living_room/devices/ac_main/state
- robocompagnon/home/rooms/living_room/devices/door_main/state
- robocompagnon/home/rooms/living_room/sensors/temperature
- robocompagnon/home/rooms/living_room/sensors/humidity
- robocompagnon/home/rooms/living_room/sensors/occupancy
- robocompagnon/home/rooms/living_room/sensors/light_level
- robocompagnon/home/rooms/living_room/sensors/gas_ppm

### Hardware Involved
- Virtual ESP32 in Wokwi

### How To Test
1. Start the Python dashboard in `IOT_MODE=hardware`.
2. Start the Wokwi ESP32 node on the same broker.
3. Click `Turn On` for the light.
4. Verify the website updates the light state and no timeout appears.
5. If a timeout still appears, read the appended Python callback error included in the message.

### Notes / Limitations
- This fix stabilizes the Python receive path, but public brokers can still produce noisy shared traffic.
- If another message format is published on the same topic contract, the new diagnostics should make that visible.

## Task: Fix Hardware Mode Broker Mismatch Guidance

### Status
Completed

### Goal
Reduce hardware-mode MQTT timeouts caused by Wokwi firmware using a different broker than the Python app, and make the timeout message point to the actual recovery steps.

### What Was Implemented
- Updated `firmware/wokwi/esp32-home-node/config.example.h` to default to `broker.emqx.io`.
- Improved the hardware timeout message in `iot_controller.py` to mention rebuilding the ESP32 firmware and checking the serial monitor subscription logs.
- Updated Wokwi documentation to state the current broker expected by the repo hardware setup.

### How It Works
1. New Wokwi config copies now start from the same broker as the Python `.env`.
2. If the ESP32 firmware is stale or built with an old broker, the Python error now tells you to rebuild and verify the serial monitor output.
3. This keeps both sides aligned on the same MQTT broker and command topic.

### Files Changed
- firmware/wokwi/esp32-home-node/config.example.h
- firmware/wokwi/esp32-home-node/README.md
- iot_controller.py
- docs/wokwi-simulation.md
- docs/task-log.md

### MQTT Topics
- robocompagnon/home/commands
- robocompagnon/home/responses

### Hardware Involved
- Virtual ESP32 in Wokwi

### How To Test
1. Confirm `.env` uses `MQTT_HOST=broker.emqx.io` and `IOT_MODE=hardware`.
2. Copy `config.example.h` to `config.h` if needed and confirm the same broker there.
3. Rebuild the firmware from `firmware/wokwi/esp32-home-node/src/main.cpp`.
4. Start Wokwi and open the serial monitor.
5. Verify it prints `MQTT connected` and `Subscribed to: robocompagnon/home/commands`.
6. Send `turn on light` from the dashboard or chat.
7. Verify the Python side receives a response instead of timing out.

### Notes / Limitations
- If Wokwi is running an older compiled binary, matching `config.h` on disk is not enough; you must rebuild.
- Public brokers can still be flaky, but this change removes the repo's default broker mismatch.

## Task: Make UI Read Only From Simulation Feed

### Status
Completed

### Goal
Ensure the dashboard gets its IoT state from the simulator-owned data flow instead of advancing or writing state from the UI side, and fix the simulator so it sends regular state updates instead of mainly receiving commands.

### What Was Implemented
- Updated `IoTMQTTSimulatorService` to publish snapshot, device, and sensor topics on a repeating heartbeat.
- Added an immediate simulator publish on service startup.
- Changed `IoTMQTTController.get_snapshot()` to become read-only and stop mutating `iot_state.json` during UI refreshes.
- Documented the simulator heartbeat behavior in architecture and MQTT topic docs.

### How It Works
1. When simulator mode starts, the MQTT simulator service subscribes to commands as before.
2. A background loop now advances the simulated state locally at a short interval.
3. After each simulator step, the service saves state and publishes snapshot, device, and sensor topics.
4. The dashboard reads the persisted state without triggering new state mutations from the UI path.
5. Command handling still works the same, but now idle simulation also keeps sending fresh data.

### Files Changed
- iot_controller.py
- docs/architecture.md
- docs/mqtt-topics.md
- docs/task-log.md

### MQTT Topics
- robocompagnon/home/snapshot
- robocompagnon/home/rooms/living_room/devices/light_main/state
- robocompagnon/home/rooms/living_room/devices/ac_main/state
- robocompagnon/home/rooms/living_room/devices/door_main/state
- robocompagnon/home/rooms/living_room/sensors/temperature
- robocompagnon/home/rooms/living_room/sensors/humidity
- robocompagnon/home/rooms/living_room/sensors/occupancy
- robocompagnon/home/rooms/living_room/sensors/light_level
- robocompagnon/home/rooms/living_room/sensors/gas_ppm

### Hardware Involved
- None. This task targets the Python simulator path.

### How To Test
1. Start Mosquitto.
2. Run the dashboard or any Python entry point with `IOT_MODE=simulator`.
3. Subscribe to `robocompagnon/home/#`.
4. Wait a few seconds without sending a command.
5. Verify snapshot, device, and sensor topics are still being published regularly.
6. Refresh the dashboard and confirm it reflects simulator data without the UI needing to advance the state itself.

### Notes / Limitations
- The dashboard still reads the persisted digital twin file locally, but the UI path no longer mutates it in simulator mode.
- The simulator heartbeat interval defaults to 2 seconds and can be changed with `IOT_SIM_PUBLISH_INTERVAL_S`.

## Task: Redesign Streamlit Dashboard to be Modern and Minimalist

### Status
Completed

### Goal
Make the UI better, fix coloring, fix the background, and provide a modern and minimalist design for the Streamlit applications.

### What Was Implemented
- Updated CSS in `app.py` to use a white/gray minimal color scheme.
- Changed `app.py` chat messages UI from simple text boxes to modern bordered message wrappers.
- Updated `app_complet.py` to remove gradients and heavy backgrounds.
- Converted `app_complet.py` dashboard cards to use subtle shadows, clean white backgrounds, and minimalist typography.
- Refined the chat input area to be simple, with flat background and clean borders.

### How It Works
- The custom HTML/CSS inside Streamlit's `st.markdown(unsafe_allow_html=True)` overrides the default elements.
- Uses `:root` CSS variables for simple color switching.
- Applies `box-shadow` and `border-radius` to simulate a clean mobile-like card UI.

### Files Changed
- `app.py`
- `app_complet.py`
- `docs/task-log.md`

### MQTT Topics
- No new topics.

### Hardware Involved
- None.

### How To Test
1. Run `streamlit run app.py` and `streamlit run app_complet.py`.
2. Ensure the UI is clean, minimalist, using mostly white/light-gray backgrounds.
3. Check the chat components for modern layout styling.

### Notes / Limitations
- Relies on Streamlit's structural class names (like `[data-testid="stChatInput"]`), which can break if Streamlit is updated.

## Task: Streamlit Chat UI Refresh

### Status
Completed

### Goal
Improve the Streamlit chat experience so device commands feel easier to send and conversation history is easier to read during demos.

### What Was Implemented
- Reworked the chat area in `app_complet.py`
- Replaced the old plain message cards with a clearer conversation layout using Streamlit chat messages
- Added quick command buttons for common IoT actions
- Added chat summary metrics for message count, reply count, and last reply time
- Switched the input area to `st.chat_input`
- Added timestamp metadata for newly sent and generated messages
- Kept voice playback support for assistant replies
- Restyled the chat composer to feel closer to a ChatGPT-style input bar with a softer white capsule and simpler chrome
- Removed the dark floating background behind the composer and changed the input bar itself to a darker capsule style
- Added broader wrapper overrides to remove the remaining full-width dark band behind the floating chat bar
- Added a targeted override for the exact `stBottomBlockContainer` wrapper and nested Streamlit emotion classes from the browser DOM
- Added hardware-mode dashboard sync improvements so button commands wait briefly for persisted device-state updates
- Wired the sidebar auto-refresh control to reload the page periodically in hardware mode so Wokwi-side changes appear on the website

### How It Works
1. The dashboard now shows a dedicated chat header with a compact summary.
2. Common room commands can be sent from one-click quick action buttons.
3. User and assistant messages render in a standard chat layout with avatars.
4. New messages are stamped with the current time when they are added to the session history.
5. The bottom chat input is styled like a rounded assistant composer, with the floating black strip removed and the bar itself carrying the darker visual weight, while still sending messages through the same `AgentRobot` flow.

### Files Changed
- `app_complet.py`
- `docs/task-log.md`

### MQTT Topics
- No topic names changed
- Chat commands still flow through:
- `robocompagnon/home/commands`
- `robocompagnon/home/responses`

### Hardware Involved
- None. UI-only improvement.

### How To Test
1. Run `py -m streamlit run app_complet.py`.
2. Open the dashboard in the browser.
3. Use a quick action such as `Turn On Light`.
4. Send a typed command from the chat input.
5. Verify the new message appears in the chat timeline and the room state updates as before.

### Notes / Limitations
- Existing older chat entries may not have timestamps because only new messages are stamped.
- Voice playback still depends on the local TTS path succeeding.

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
