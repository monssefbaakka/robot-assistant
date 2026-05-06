# MQTT Topics

This file documents the MQTT topics currently used by the local IoT simulator.

## Topic: `robocompagnon/home/commands`

### Purpose
Receives structured IoT commands from the assistant or dashboard.

### Payload
- `correlation_id`
- `command`

### Used For
- Turn light on or off
- Set light brightness
- Turn AC on or off
- Set AC target temperature
- Turn gas simulation on or off
- Set gas level
- Request device state
- Request sensor values

## Topic: `robocompagnon/home/responses`

### Purpose
Returns the result of a command executed by the virtual MQTT simulator service.

### Payload
- `correlation_id`
- `result`

### Used For
- Matching command responses to the original request
- Returning success or error messages to the assistant

## Topic: `robocompagnon/home/events`

### Purpose
Publishes an event record for each executed IoT command.

### Payload
- `timestamp`
- `source`
- `topic`
- `room`
- `action`
- `target`
- `status`
- `raw_text`
- `details`

### Used For
- Event history
- Dashboard activity display
- Debugging command execution

## Topic: `robocompagnon/home/snapshot`

### Purpose
Publishes the full current IoT state after room updates and during the simulator heartbeat.

### Payload
- Full `iot_state.json` structure

### Used For
- Refreshing the dashboard from one complete state message
- Keeping the UI fed by simulator-owned data even when no manual command is sent

## Topic Pattern: `robocompagnon/home/rooms/{room_id}/devices/{device_id}/state`

### Purpose
Publishes the latest state for each device in a room.

### Current Topics
- `robocompagnon/home/rooms/living_room/devices/light_main/state`
- `robocompagnon/home/rooms/living_room/devices/ac_main/state`
- `robocompagnon/home/rooms/living_room/devices/buzzer_main/state`

### Used For
- Device status updates in the dashboard
- Future hardware-compatible device state subscriptions
- Continuous simulator-to-UI state streaming

## Topic Pattern: `robocompagnon/home/rooms/{room_id}/sensors/{sensor_name}`

### Purpose
Publishes the latest sensor value for each room sensor.

### Current Topics
- `robocompagnon/home/rooms/living_room/sensors/temperature`
- `robocompagnon/home/rooms/living_room/sensors/humidity`
- `robocompagnon/home/rooms/living_room/sensors/occupancy`
- `robocompagnon/home/rooms/living_room/sensors/light_level`

### Used For
- Sensor monitoring in the dashboard
- Future subscriptions for alerts or analytics
- Continuous simulator-to-UI sensor streaming

## Topic: `robocompagnon/home/alerts/gas`

### Purpose
Published when the gas sensor reading exceeds the safety threshold (400 ppm).

### Payload
- `alert`: true
- `message`: human-readable alert string

### Used For
- Gas leak notification to dashboard and future Telegram bot
- Edge-triggered: fires from within the virtual device service on every command that updates state

## Topic Pattern: `robocompagnon/home/rooms/{room_id}/devices/door_main/state`

### Purpose
Publishes door lock state after lock/unlock commands.

### Current Topics
- `robocompagnon/home/rooms/living_room/devices/door_main/state`

### Used For
- Door lock status display in dashboard

## Notes
- The current transport uses the local Mosquitto broker through `mqtt_client.py` and `paho-mqtt`.
- The simulator service still applies commands locally and publishes the same topic contract for the dashboard and future hardware.
- In simulator mode, the Python simulator now republishes snapshot, device, and sensor topics on a short interval so the UI stays read-only and does not have to advance state itself.
- Hardware mode is now prepared for a Wokwi ESP32 node publishing the same topics.
- In Wokwi cloud, the broker must be reachable from the public internet. `localhost` on the PC is not reachable directly from Wokwi.
