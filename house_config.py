from copy import deepcopy


HOUSE_ROOMS = {
    "living_room": {
        "name": "Living Room",
        "devices": {
            "light_main": {
                "id": "light_main",
                "type": "light",
                "name": "Main Light",
                "state": "on",
                "brightness": 80,
                "power_w": 12,
            },
            "ac_main": {
                "id": "ac_main",
                "type": "ac",
                "name": "Main AC",
                "state": "off",
                "mode": "cool",
                "target_temp": 22,
                "fan_speed": 2,
                "power_w": 0,
            },
            "door_main": {
                "id": "door_main",
                "type": "door",
                "name": "Front Door",
                "state": "locked",
            },
            "buzzer_main": {
                "id": "buzzer_main",
                "type": "buzzer",
                "name": "Gas Safety Buzzer",
                "state": "off",
            },
        },
        "sensors": {
            "temperature": 27.4,
            "humidity": 48,
            "occupancy": True,
            "light_level": 760,
            "gas_ppm": 120,
        },
        "environment": {
            "insulation_factor": 0.72,
            "sun_exposure": 0.65,
        },
    },
    "kitchen": {
        "name": "Kitchen",
        "devices": {
            "light_main": {
                "id": "light_main",
                "type": "light",
                "name": "Kitchen Light",
                "state": "off",
                "brightness": 0,
                "power_w": 0,
            },
            "buzzer_main": {
                "id": "buzzer_main",
                "type": "buzzer",
                "name": "Gas Safety Buzzer",
                "state": "off",
            },
        },
        "sensors": {
            "temperature": 26.2,
            "humidity": 52,
            "occupancy": False,
            "light_level": 210,
            "gas_ppm": 120,
        },
        "environment": {
            "insulation_factor": 0.68,
            "sun_exposure": 0.45,
        },
    },
    "bedroom": {
        "name": "Bedroom",
        "devices": {
            "light_main": {
                "id": "light_main",
                "type": "light",
                "name": "Bedroom Light",
                "state": "off",
                "brightness": 0,
                "power_w": 0,
            },
            "ac_main": {
                "id": "ac_main",
                "type": "ac",
                "name": "Bedroom AC",
                "state": "off",
                "mode": "cool",
                "target_temp": 23,
                "fan_speed": 1,
                "power_w": 0,
            },
            "door_main": {
                "id": "door_main",
                "type": "door",
                "name": "Bedroom Door",
                "state": "unlocked",
            },
            "buzzer_main": {
                "id": "buzzer_main",
                "type": "buzzer",
                "name": "Gas Safety Buzzer",
                "state": "off",
            },
        },
        "sensors": {
            "temperature": 24.3,
            "humidity": 47,
            "occupancy": True,
            "light_level": 120,
        },
        "environment": {
            "insulation_factor": 0.8,
            "sun_exposure": 0.25,
        },
    },
    "toilet": {
        "name": "Toilet",
        "devices": {
            "light_main": {
                "id": "light_main",
                "type": "light",
                "name": "Toilet Light",
                "state": "off",
                "brightness": 0,
                "power_w": 0,
            },
            "door_main": {
                "id": "door_main",
                "type": "door",
                "name": "Toilet Door",
                "state": "unlocked",
            },
            "buzzer_main": {
                "id": "buzzer_main",
                "type": "buzzer",
                "name": "Gas Safety Buzzer",
                "state": "off",
            },
        },
        "sensors": {
            "temperature": 23.8,
            "humidity": 58,
            "occupancy": False,
            "light_level": 90,
        },
        "environment": {
            "insulation_factor": 0.76,
            "sun_exposure": 0.1,
        },
    },
}


ROOM_ORDER = list(HOUSE_ROOMS.keys())


SIMULATION_LAYOUT = {
    "living_room": {
        "rect": (120, 160, 340, 250),
        "door": ((458, 280), (458, 335)),
    },
    "kitchen": {
        "rect": (500, 160, 220, 180),
        "door": ((558, 338), (618, 338)),
    },
    "bedroom": {
        "rect": (500, 380, 220, 190),
        "door": ((500, 448), (500, 505)),
    },
    "toilet": {
        "rect": (760, 160, 120, 140),
        "door": ((760, 214), (760, 255)),
    },
}


def default_rooms_payload():
    return deepcopy(HOUSE_ROOMS)


def room_name(room_id, room=None):
    if room and room.get("name"):
        return room["name"]
    if room_id in HOUSE_ROOMS:
        return HOUSE_ROOMS[room_id]["name"]
    return str(room_id).replace("_", " ").title()


def ordered_room_ids(rooms):
    ordered_ids = [room_id for room_id in ROOM_ORDER if room_id in rooms]
    ordered_ids.extend(room_id for room_id in rooms if room_id not in ordered_ids)
    return ordered_ids
