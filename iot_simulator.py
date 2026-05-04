from copy import deepcopy
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc)


def _parse_iso(value):
    return datetime.fromisoformat(value)


def _round_value(value):
    return round(value, 1)


def advance_state(state, now=None):
    now = now or _now()
    meta = state.setdefault("meta", {})
    last_update_raw = meta.get("last_update")
    if not last_update_raw:
        meta["last_update"] = now.isoformat()
        return state

    last_update = _parse_iso(last_update_raw)
    elapsed_seconds = max((now - last_update).total_seconds(), 0)
    if elapsed_seconds <= 0:
        return state

    # Prevent unrealistic jumps after long idle periods.
    elapsed_seconds = min(elapsed_seconds, 6 * 3600)
    steps = max(1, int(elapsed_seconds // 30))
    delta_minutes = (elapsed_seconds / steps) / 60.0

    outside = state.get("outside", {})
    outside_temp = outside.get("temperature", 29.0)
    outside_humidity = outside.get("humidity", 45)

    for step_index in range(steps):
        simulated_time = last_update + (now - last_update) * ((step_index + 1) / steps)
        hour = simulated_time.hour

        for room in state.get("rooms", {}).values():
            sensors = room.setdefault("sensors", {})
            devices = room.setdefault("devices", {})
            environment = room.setdefault("environment", {})

            insulation = environment.get("insulation_factor", 0.7)
            sun_exposure = environment.get("sun_exposure", 0.5)
            occupancy = bool(sensors.get("occupancy", True))

            temp = float(sensors.get("temperature", 25.0))
            humidity = float(sensors.get("humidity", 50.0))

            light_device = _find_device_by_type(devices, "light")
            ac_device = _find_device_by_type(devices, "ac")

            outside_drift = (outside_temp - temp) * 0.02 * (1 - insulation) * delta_minutes
            occupancy_heat = 0.03 * delta_minutes if occupancy else 0.0
            solar_gain = 0.05 * sun_exposure * delta_minutes if 8 <= hour < 18 else 0.0

            ac_cooling = 0.0
            if ac_device and ac_device.get("state") == "on":
                target_temp = float(ac_device.get("target_temp", 22))
                if temp > target_temp:
                    ac_cooling = min(0.22 * delta_minutes, temp - target_temp)
                humidity = max(30.0, humidity - 0.08 * delta_minutes)
                ac_device["power_w"] = 1200
            elif ac_device:
                ac_device["power_w"] = 0

            temp = temp + outside_drift + occupancy_heat + solar_gain - ac_cooling
            temp = max(16.0, min(35.0, temp))

            humidity_drift = (outside_humidity - humidity) * 0.01 * delta_minutes
            humidity = max(25.0, min(75.0, humidity + humidity_drift))

            daylight = _daylight_level(hour)
            light_boost = 0
            if light_device and light_device.get("state") == "on":
                brightness = float(light_device.get("brightness", 100))
                light_boost = int(4.5 * brightness)
                light_device["power_w"] = max(1, int(12 * (brightness / 100.0)))
            elif light_device:
                light_device["power_w"] = 0

            sensors["temperature"] = _round_value(temp)
            sensors["humidity"] = int(round(humidity))
            sensors["light_level"] = max(0, int(daylight + light_boost))

    meta["last_update"] = now.isoformat()
    return state


def _daylight_level(hour):
    if 7 <= hour < 10:
        return 420
    if 10 <= hour < 16:
        return 650
    if 16 <= hour < 19:
        return 360
    if 19 <= hour < 22:
        return 140
    return 40


def _find_device_by_type(devices, device_type):
    for device in devices.values():
        if device.get("type") == device_type:
            return device
    return None


def _resolve_device(room, command):
    devices = room.get("devices", {})
    device_id = command.get("device_id")
    if device_id and device_id in devices:
        return devices[device_id]

    device_type = command.get("device_type")
    return _find_device_by_type(devices, device_type)


def apply_command(state, command, now=None):
    now = now or _now()
    advance_state(state, now)

    room_id = command.get("room")
    room = state.get("rooms", {}).get(room_id)
    if not room:
        return _error_result(command, "room_not_found", f"Room '{room_id}' was not found.")

    action = command.get("action")

    if action == "get_sensor":
        sensor_type = command.get("sensor_type")
        if sensor_type not in room.get("sensors", {}):
            return _error_result(command, "sensor_not_found", f"Sensor '{sensor_type}' was not found.")

        value = room["sensors"][sensor_type]
        unit = {"temperature": "C", "humidity": "%", "light_level": "lux"}.get(sensor_type, "")
        message = _sensor_message(room["name"], sensor_type, value, unit)
        return {
            "ok": True,
            "action": action,
            "room": room_id,
            "message": message,
            "value": value,
            "unit": unit,
        }

    device = _resolve_device(room, command)
    if not device:
        device_type = command.get("device_type") or command.get("device_id") or "device"
        return _error_result(command, "device_not_found", f"No {device_type} was found in {room['name']}.")

    previous_state = deepcopy(device)
    device_type = device.get("type")

    if action == "turn_on":
        if device_type == "light":
            device["state"] = "on"
            device["brightness"] = max(20, int(device.get("brightness", 80) or 80))
            device["power_w"] = max(1, int(12 * (device["brightness"] / 100.0)))
        elif device_type == "ac":
            device["state"] = "on"
            device["power_w"] = 1200
        message = f"{room['name']} {device['name']} turned on."

    elif action == "turn_off":
        if device_type == "light":
            device["state"] = "off"
            device["brightness"] = 0
            device["power_w"] = 0
        elif device_type == "ac":
            device["state"] = "off"
            device["power_w"] = 0
        message = f"{room['name']} {device['name']} turned off."

    elif action == "set_temperature":
        if device_type != "ac":
            return _error_result(command, "unsupported_action", "Only the AC supports target temperature.")
        target_temp = int(command.get("parameters", {}).get("target_temp", device.get("target_temp", 22)))
        target_temp = max(16, min(30, target_temp))
        device["target_temp"] = target_temp
        message = f"{room['name']} AC target temperature set to {target_temp}C."

    elif action == "get_device_state":
        status = device.get("state", "unknown")
        if device_type == "ac":
            target = device.get("target_temp", 22)
            message = f"{room['name']} AC is {status} with a target of {target}C."
        else:
            brightness = int(device.get("brightness", 0))
            message = f"{room['name']} light is {status} at {brightness}% brightness."
    else:
        return _error_result(command, "unsupported_action", f"Action '{action}' is not supported.")

    advance_state(state, now)

    return {
        "ok": True,
        "action": action,
        "room": room_id,
        "device_id": device["id"],
        "device_type": device_type,
        "old_state": previous_state,
        "new_state": deepcopy(device),
        "message": message,
    }


def apply_weather_update(state, meteo_data, now=None):
    now = now or _now()
    outside = state.setdefault("outside", {})
    if "temperature" in meteo_data:
        outside["temperature"] = float(meteo_data["temperature"])
    if "humidite" in meteo_data:
        outside["humidity"] = int(meteo_data["humidite"])
    elif "humidity" in meteo_data:
        outside["humidity"] = int(meteo_data["humidity"])
    outside["source"] = meteo_data.get("source", meteo_data.get("ville", "weather"))
    outside["updated_at"] = now.isoformat()
    return state


def _sensor_message(room_name, sensor_type, value, unit):
    if sensor_type == "temperature":
        return f"The current temperature in the {room_name.lower()} is {value}{unit}."
    if sensor_type == "humidity":
        return f"The current humidity in the {room_name.lower()} is {value}{unit}."
    if sensor_type == "light_level":
        return f"The current light level in the {room_name.lower()} is {value} {unit}."
    return f"The current {sensor_type} in the {room_name.lower()} is {value}{unit}."


def _error_result(command, code, message):
    return {
        "ok": False,
        "action": command.get("action"),
        "room": command.get("room"),
        "error_code": code,
        "message": message,
    }
