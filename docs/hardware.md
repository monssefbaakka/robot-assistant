# Hardware Reference

All components listed below are currently **simulated** in Python. Real hardware mapping is provided for future ESP32 migration.

---

## DHT22 — Temperature & Humidity Sensor

### Purpose
Measures ambient temperature and relative humidity inside a room.

### Pins
- VCC → 3.3V
- GND → GND
- DATA → GPIO4

### Used For
- `sensors.temperature` in `iot_state.json`
- `sensors.humidity` in `iot_state.json`
- Drives AC cooling simulation in `iot_simulator.py`

### Simulation
`iot_simulator.py` computes temperature drift from outside temp, AC state, occupancy, and sun exposure.

---

## MQ-2 — Gas Sensor

### Purpose
Detects combustible gas concentration (LPG, propane, methane). Returns analog voltage proportional to gas ppm.

### Pins
- VCC → 5V
- GND → GND
- AOUT → GPIO34 (ADC)
- DOUT → GPIO33 (digital threshold, optional)

### Used For
- `sensors.gas_ppm` in `iot_state.json`
- Triggers `alerts.gas = True` when ppm > 400 (edge rule in `iot_simulator.py`)
- Publishes to `robocompagnon/home/alerts/gas`

### Simulation
`gas_ppm` can now be controlled by command:
- turn gas on
- turn gas off
- set gas level to 300 ppm

When the gas level rises above the alert threshold, the Wokwi hardware simulation now also turns on a red gas alert LED on `GPIO33` so the change is visible in the diagram.

---

## Red Alert LED — Gas Alarm Indicator

### Purpose
Provides a visible warning in the Wokwi simulation when gas level is above the alert threshold.

### Pins
- Anode → GPIO33
- Cathode → GND

### Used For
- Visual gas alarm feedback in Wokwi when `gas_ppm > 400`

### Simulation
Turns on automatically when commanded or sensed gas level exceeds the threshold.

---

## Buzzer — Unconfirmed Gas Alarm

### Purpose
Warns locally if gas is activated and left unconfirmed for 30 seconds.

### Pins
- Signal → GPIO32
- GND → GND

### Used For
- `devices.buzzer_main` state in `iot_state.json`
- Local audible warning in Wokwi and future hardware mode

### Simulation
If gas remains active for 30 seconds without a confirmation command such as `it's me who did it`, the buzzer starts beeping.

---

## HC-SR501 — PIR Motion Sensor

### Purpose
Detects human presence via passive infrared. Digital output goes HIGH when motion detected.

### Pins
- VCC → 5V
- GND → GND
- OUT → GPIO5

### Used For
- `sensors.occupancy` in `iot_state.json`
- Future edge rule: night motion light (hour >= 22 and motion → turn on light)

### Simulation
`occupancy` is a static boolean in state. Not yet auto-updated by simulator.

---

## LDR + Resistor Divider — Light Sensor

### Purpose
Measures ambient light level via voltage divider. Higher light = lower resistance = higher ADC reading.

### Pins
- VCC → 3.3V
- GND → GND
- OUT → GPIO35 (ADC)

### Used For
- `sensors.light_level` in `iot_state.json` (unit: lux approximation)

### Simulation
`iot_simulator.py` computes light level from time of day + light device state.

---

## 5V Relay Module — Light Actuator

### Purpose
Controls mains-voltage light fixture via GPIO. LOW signal = relay closed = light ON.

### Pins
- VCC → 5V
- GND → GND
- IN → GPIO26

### Used For
- `devices.light_main` state in `iot_state.json`
- `devices.light_main.brightness` in `iot_state.json`

### Simulation
`light_main.state` and `brightness` can be controlled by command:
- turn on the light
- turn off the light
- set light brightness to 60%

---

## 5V Relay Module — AC Actuator

### Purpose
Controls AC unit power via GPIO. Same relay type as light actuator.

### Pins
- VCC → 5V
- GND → GND
- IN → GPIO27

### Used For
- `devices.ac_main` state in `iot_state.json`
- Target temperature logic in `iot_simulator.py`

### Simulation
`ac_main.state` toggled by `turn_on` / `turn_off` / `set_temperature` commands.

---

## SG90 Servo Motor — Door Lock

### Purpose
Physically rotates bolt to lock (0°) or unlock (90°) position via PWM signal.

### Pins
- VCC → 5V
- GND → GND
- SIGNAL → GPIO18 (PWM)

### Used For
- `devices.door_main` state in `iot_state.json` (`locked` / `unlocked`)

### Simulation
`door_main.state` toggled by `lock` / `unlock` commands in `iot_simulator.py`. Servo not physically present.

---

## ESP32 — Main Controller

### Purpose
Runs firmware connecting all sensors and actuators to the MQTT broker over WiFi.

### Used For
- Future swap: replaces `IoTMQTTSimulatorService` when real hardware is added
- Subscribes to `robocompagnon/home/commands`
- Publishes to `robocompagnon/home/rooms/+/devices/+/state`

### Simulation
Currently replaced entirely by `iot_simulator.py` + `iot_controller.py`.

---

## Mosquitto Broker — Local MQTT Broker

### Purpose
Routes MQTT messages between ESP32 devices and the Python backend.

### Connection
- Protocol: TCP
- Port: 1883
- Host: localhost (same machine as Python backend)

### Simulation
Currently replaced by `mqtt_bus.py` loopback broker (no network, in-process pub/sub).
