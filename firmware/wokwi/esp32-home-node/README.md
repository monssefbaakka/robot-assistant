# Wokwi ESP32 Home Node

This folder is the first hardware-simulation slice for moving device behavior out of Python and into a virtual ESP32 node.

## What it simulates

- `light_main` on GPIO26 using a yellow LED
- `ac_main` on GPIO27 using a blue LED
- `door_main` on GPIO18 using a servo
- `temperature` and `humidity` using a DHT22 on GPIO4
- `gas_ppm` using a slide potentiometer on GPIO34
- `light_level` using a photoresistor on GPIO35
- `occupancy` using a slide switch on GPIO5

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

## Files

- `sketch.ino`: ESP32 MQTT firmware
- `diagram.json`: Wokwi wiring
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
