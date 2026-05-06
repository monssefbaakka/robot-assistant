from copy import deepcopy
from datetime import datetime, timezone

GAS_THRESHOLD = 400
GAS_CONFIRMATION_TIMEOUT_S = 60


def _now():
    return datetime.now(timezone.utc)


def _parse_iso(value):
    return datetime.fromisoformat(value)


def _round_value(value):
    return round(value, 1)


def _gas_safety(state):
    return state.setdefault(
        "safety",
        {"gas_confirmation": {"active": False, "pending": False, "armed_at": None, "confirmed": False}},
    ).setdefault("gas_confirmation", {"active": False, "pending": False, "armed_at": None, "confirmed": False})


def _buzzer_device(room):
    return room.setdefault("devices", {}).setdefault(
        "buzzer_main",
        {"id": "buzzer_main", "type": "buzzer", "name": "Gas Safety Buzzer", "state": "off"},
    )


def _set_gas_monitor(state, now, gas_active, confirmed=False):
    gas_confirmation = _gas_safety(state)
    alerts = state.setdefault("alerts", {})
    for room in state.get("rooms", {}).values():
        buzzer = _buzzer_device(room)
        if gas_active:
            gas_confirmation["active"] = True
            gas_confirmation["pending"] = not confirmed
            gas_confirmation["armed_at"] = now.isoformat()
            gas_confirmation["confirmed"] = confirmed
            buzzer["state"] = "off"
            alerts["gas_unconfirmed"] = not confirmed
            alerts["gas_buzzer"] = False
        else:
            gas_confirmation["active"] = False
            gas_confirmation["pending"] = False
            gas_confirmation["armed_at"] = None
            gas_confirmation["confirmed"] = False
            buzzer["state"] = "off"
            alerts["gas_unconfirmed"] = False
            alerts["gas_buzzer"] = False


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

    alerts = state.setdefault("alerts", {})
    alerts["gas"] = False
    gas_confirmation = _gas_safety(state)
    alerts["gas_unconfirmed"] = bool(gas_confirmation.get("active") and gas_confirmation.get("pending"))
    alerts["gas_buzzer"] = False
    for room in state.get("rooms", {}).values():
        buzzer = _buzzer_device(room)
        gas_ppm = room.get("sensors", {}).get("gas_ppm", 0)
        if gas_ppm > GAS_THRESHOLD:
            alerts["gas"] = True
        if gas_ppm <= 0 or not gas_confirmation.get("active"):
            buzzer["state"] = "off"
            continue

        armed_at_raw = gas_confirmation.get("armed_at")
        if gas_confirmation.get("pending") and armed_at_raw:
            armed_at = _parse_iso(armed_at_raw)
            elapsed = max((now - armed_at).total_seconds(), 0)
            if elapsed >= GAS_CONFIRMATION_TIMEOUT_S:
                buzzer["state"] = "on"
                alerts["gas_buzzer"] = True
            else:
                buzzer["state"] = "off"
                alerts["gas_unconfirmed"] = True
        elif gas_confirmation.get("confirmed"):
            buzzer["state"] = "off"
        else:
            buzzer["state"] = "off"

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
        unit = {"temperature": "C", "humidity": "%", "light_level": "lux", "gas_ppm": "ppm"}.get(sensor_type, "")
        message = _sensor_message(room["name"], sensor_type, value, unit)
        return {
            "ok": True,
            "action": action,
            "room": room_id,
            "message": message,
            "value": value,
            "unit": unit,
        }

    if action == "set_gas_state":
        enabled = bool(command.get("parameters", {}).get("enabled"))
        previous_gas = room["sensors"].get("gas_ppm", 120)
        room["sensors"]["gas_ppm"] = 550 if enabled and previous_gas <= 0 else (previous_gas if enabled else 0)
        _set_gas_monitor(state, now, room["sensors"]["gas_ppm"] > 0)
        message = (
            f"{room['name']} gas simulation turned {'on' if enabled else 'off'}."
            + (" Confirm within 30 seconds to avoid buzzer alarm." if enabled else "")
        )
        advance_state(state, now)
        return {
            "ok": True,
            "action": action,
            "room": room_id,
            "sensor_type": "gas_ppm",
            "value": room["sensors"]["gas_ppm"],
            "message": message,
        }

    if action == "set_gas_level":
        gas_ppm = int(command.get("parameters", {}).get("gas_ppm", room["sensors"].get("gas_ppm", 0)))
        gas_ppm = max(0, min(1000, gas_ppm))
        room["sensors"]["gas_ppm"] = gas_ppm
        _set_gas_monitor(state, now, gas_ppm > 0)
        message = f"{room['name']} gas level set to {gas_ppm} ppm."
        if gas_ppm > 0:
            message += " Confirm within 30 seconds to avoid buzzer alarm."
        advance_state(state, now)
        return {
            "ok": True,
            "action": action,
            "room": room_id,
            "sensor_type": "gas_ppm",
            "value": gas_ppm,
            "message": message,
        }

    if action == "confirm_gas_owner":
        gas_ppm = int(room.get("sensors", {}).get("gas_ppm", 0))
        if gas_ppm <= 0:
            return _error_result(command, "gas_not_active", "Gas is not active right now.")
        _set_gas_monitor(state, now, True, confirmed=True)
        advance_state(state, now)
        return {
            "ok": True,
            "action": action,
            "room": room_id,
            "sensor_type": "gas_ppm",
            "value": gas_ppm,
            "message": f"{room['name']} gas action confirmed by user. Buzzer remains off.",
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

    elif action == "set_brightness":
        if device_type != "light":
            return _error_result(command, "unsupported_action", "Only the light supports brightness control.")
        brightness = int(command.get("parameters", {}).get("brightness", device.get("brightness", 80)))
        brightness = max(0, min(100, brightness))
        device["brightness"] = brightness
        device["state"] = "on" if brightness > 0 else "off"
        device["power_w"] = max(1, int(12 * (brightness / 100.0))) if brightness > 0 else 0
        message = f"{room['name']} light brightness set to {brightness}%."

    elif action in ("lock", "unlock"):
        if device_type != "door":
            return _error_result(command, "unsupported_action", "Only the door supports lock/unlock.")
        device["state"] = "locked" if action == "lock" else "unlocked"
        message = f"{room['name']} {device['name']} {'locked' if action == 'lock' else 'unlocked'}."

    elif action == "get_device_state":
        status = device.get("state", "unknown")
        if device_type == "ac":
            target = device.get("target_temp", 22)
            message = f"{room['name']} AC is {status} with a target of {target}C."
        elif device_type == "door":
            message = f"{room['name']} {device['name']} is {status}."
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
    if sensor_type == "gas_ppm":
        alert = " WARNING: gas leak detected!" if value > GAS_THRESHOLD else ""
        return f"Gas level in the {room_name.lower()} is {value} {unit}.{alert}"
    return f"The current {sensor_type} in the {room_name.lower()} is {value}{unit}."


def _error_result(command, code, message):
    return {
        "ok": False,
        "action": command.get("action"),
        "room": command.get("room"),
        "error_code": code,
        "message": message,
    }
