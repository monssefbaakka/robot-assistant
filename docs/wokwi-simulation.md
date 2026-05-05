# Wokwi Simulation Setup

This branch prepares the project for a split simulation:

- Python app on the PC
- Mosquitto broker
- ESP32 home node running in Wokwi

## What changed

- `iot_controller.py` supports `IOT_MODE=hardware`
- `iot_hardware_bridge.py` listens to MQTT state topics and updates `iot_state.json`
- `firmware/wokwi/esp32-home-node/` contains the first Wokwi firmware scaffold

## Recommended run mode

### Python side

Use:

```powershell
$env:IOT_MODE='hardware'
$env:MQTT_HOST='your-broker-host'
$env:MQTT_PORT='1883'
py -m streamlit run app_complet.py
```

or:

```powershell
$env:IOT_MODE='hardware'
$env:MQTT_HOST='your-broker-host'
py chat.py
```

### Wokwi side

1. Open `firmware/wokwi/esp32-home-node` in Wokwi
2. Copy `config.example.h` to `config.h`
3. Set `MQTT_HOST` to a broker reachable from Wokwi cloud
4. Run the simulation

## Important limitation

Wokwi cloud cannot connect directly to `localhost` on your PC. If you want to use Wokwi cloud, use a public or tunneled broker.

## First working scope

The provided firmware handles:

- `light_main`
- `ac_main`
- `door_main`
- `temperature`
- `humidity`
- `gas_ppm`
- `light_level`
- `occupancy`

## End-to-end flow

1. User sends command in Streamlit or `chat.py`
2. Python publishes to `robocompagnon/home/commands`
3. Wokwi ESP32 receives command and actuates simulated devices
4. ESP32 publishes:
- device state topics
- sensor topics
- `robocompagnon/home/responses`
- `robocompagnon/home/events`
- gas alert topic when needed
5. `iot_hardware_bridge.py` updates `iot_state.json`
6. Dashboard reflects the hardware simulation state
