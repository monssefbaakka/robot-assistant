# Wokwi ESP32 Home Node

This folder is the first hardware-simulation slice for moving device behavior out of Python and into a virtual ESP32 node.

## What it simulates

- A house-style Wokwi layout with labeled zones for:
- `living room`
- `kitchen`
- `bedroom`
- `toilet`
- `garage`
- A single ESP32 firmware that now publishes room topics for the same dashboard rooms:
- `robocompagnon/home/rooms/living_room/...`
- `robocompagnon/home/rooms/kitchen/...`
- `robocompagnon/home/rooms/bedroom/...`
- `robocompagnon/home/rooms/toilet/...`
- Connected components mapped to the dashboard device model:
- living room: light LED on GPIO26, AC LED on GPIO27, door servo on GPIO18
- kitchen: light LED on GPIO21, gas slider on GPIO34, gas alert LED on GPIO33, buzzer on GPIO32
- bedroom: light LED on GPIO14, AC LED on GPIO13, door servo on GPIO23
- toilet: light LED on GPIO22, door servo on GPIO15
- shared sensors and indicators:
- DHT22 on GPIO4
- photoresistor on GPIO35
- occupancy switch on GPIO5
- living room door state LEDs on GPIO19 and GPIO25

## MQTT contract

- Subscribes to `robocompagnon/home/commands`
- Publishes to:
- `robocompagnon/home/responses`
- `robocompagnon/home/events`
- `robocompagnon/home/alerts/gas`
- `robocompagnon/home/rooms/living_room/devices/+/state`
- `robocompagnon/home/rooms/living_room/sensors/+`

## Important limitation

Wokwi cloud cannot connect to `localhost` on your PC directly. To run this in Wokwi cloud, point the firmware to an MQTT broker reachable from the public internet.

For local development with the Python app:
- run the Python app with `IOT_MODE=hardware`
- point both sides to the same reachable MQTT broker

The firmware uses one set of shared physical sensors to generate the room sensor topics, so not every room has a dedicated temperature or humidity sensor. The main goal is to keep the Wokwi simulation simple while making the website and MQTT room model line up.

## Files

- `src/main.cpp`: ESP32 MQTT firmware
- `sketch.ino`: thin include wrapper for Wokwi/Arduino compatibility
- `diagram.json`: Wokwi wiring and enlarged room-based house schema
- `libraries.txt`: Arduino libraries needed by Wokwi
- `config.example.h`: copy to `config.h` and set your broker host if needed
  The template now defaults to `broker.emqx.io` to match the current Python hardware-mode setup in this repo.
- `platformio.ini`: local PlatformIO build config for VS Code
- `wokwi.toml`: Wokwi for VS Code simulation config

## VS Code workflow

The simplest local workflow for this folder is:

1. Install the PlatformIO IDE extension in VS Code
2. Install the Wokwi for VS Code extension and activate its license
3. Copy `config.example.h` to `config.h`
4. Open this folder directly in VS Code
5. Run a PlatformIO build
6. Open `diagram.json`
7. Start the Wokwi simulation from the embedded simulator view
