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
    "garage": {
        "name": "Garage",
        "devices": {
            "light_main": {
                "id": "light_main",
                "type": "light",
                "name": "Garage Light",
                "state": "off",
                "brightness": 0,
                "power_w": 0,
            },
            "door_main": {
                "id": "door_main",
                "type": "door",
                "name": "Garage Door",
                "state": "locked",
            },
            "buzzer_main": {
                "id": "buzzer_main",
                "type": "buzzer",
                "name": "Garage Safety Buzzer",
                "state": "off",
            },
        },
        "sensors": {
            "temperature": 22.6,
            "humidity": 51,
            "occupancy": False,
            "light_level": 60,
        },
        "environment": {
            "insulation_factor": 0.58,
            "sun_exposure": 0.08,
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
    "garage": {
        "rect": (760, 340, 180, 190),
        "door": ((760, 420), (760, 468)),
    },
}


ROBOT_SIMULATION_WORLD = {
    "spawn": {"x": -70.0, "y": 60.0},
    "robot_radius_cm": 12.0,
    "walkable_areas": [
        {"id": "living_room", "label": "Living Room", "x1": -220.0, "y1": 10.0, "x2": -4.0, "y2": 180.0},
        {"id": "hallway", "label": "Hallway", "x1": -32.0, "y1": -140.0, "x2": 32.0, "y2": 180.0},
        {"id": "kitchen", "label": "Kitchen", "x1": 4.0, "y1": 50.0, "x2": 170.0, "y2": 180.0},
        {"id": "bedroom", "label": "Bedroom", "x1": 4.0, "y1": -140.0, "x2": 170.0, "y2": 30.0},
        {"id": "toilet", "label": "Toilet", "x1": 146.0, "y1": 60.0, "x2": 250.0, "y2": 145.0},
        {"id": "garage", "label": "Garage", "x1": 146.0, "y1": -140.0, "x2": 300.0, "y2": 30.0},
    ],
    "obstacles": [
        {"id": "sofa", "label": "Sofa", "x1": -195.0, "y1": 35.0, "x2": -145.0, "y2": 95.0},
        {"id": "coffee_table", "label": "Coffee Table", "x1": -130.0, "y1": 82.0, "x2": -82.0, "y2": 120.0},
        {"id": "tv_console", "label": "TV Console", "x1": -205.0, "y1": 142.0, "x2": -115.0, "y2": 166.0},
        {"id": "kitchen_counter", "label": "Counter", "x1": 95.0, "y1": 126.0, "x2": 158.0, "y2": 168.0},
        {"id": "dining_table", "label": "Dining", "x1": 48.0, "y1": 78.0, "x2": 92.0, "y2": 118.0},
        {"id": "bed", "label": "Bed", "x1": 82.0, "y1": -120.0, "x2": 156.0, "y2": -44.0},
        {"id": "wardrobe", "label": "Wardrobe", "x1": 108.0, "y1": -10.0, "x2": 158.0, "y2": 24.0},
        {"id": "sink", "label": "Sink", "x1": 208.0, "y1": 108.0, "x2": 238.0, "y2": 136.0},
        {"id": "car", "label": "Car", "x1": 192.0, "y1": -126.0, "x2": 280.0, "y2": -48.0},
        {"id": "shelf", "label": "Shelf", "x1": 246.0, "y1": -12.0, "x2": 292.0, "y2": 24.0},
    ],
    "components": [
        {"room_id": "living_room", "component_id": "light_main", "kind": "light", "label": "L", "x": -120.0, "y": 170.0},
        {"room_id": "living_room", "component_id": "ac_main", "kind": "ac", "label": "AC", "x": -208.0, "y": 110.0},
        {"room_id": "living_room", "component_id": "door_main", "kind": "door", "label": "D", "x": -20.0, "y": 84.0},
        {"room_id": "living_room", "component_id": "buzzer_main", "kind": "buzzer", "label": "BZ", "x": -48.0, "y": 165.0},
        {"room_id": "living_room", "component_id": "temperature", "kind": "sensor", "label": "T", "x": -58.0, "y": 148.0},
        {"room_id": "living_room", "component_id": "gas_ppm", "kind": "gas", "label": "G", "x": -48.0, "y": 34.0},
        {"room_id": "kitchen", "component_id": "light_main", "kind": "light", "label": "L", "x": 95.0, "y": 170.0},
        {"room_id": "kitchen", "component_id": "buzzer_main", "kind": "buzzer", "label": "BZ", "x": 152.0, "y": 170.0},
        {"room_id": "kitchen", "component_id": "gas_ppm", "kind": "gas", "label": "G", "x": 44.0, "y": 112.0},
        {"room_id": "bedroom", "component_id": "light_main", "kind": "light", "label": "L", "x": 95.0, "y": 20.0},
        {"room_id": "bedroom", "component_id": "ac_main", "kind": "ac", "label": "AC", "x": 28.0, "y": -24.0},
        {"room_id": "bedroom", "component_id": "door_main", "kind": "door", "label": "D", "x": 20.0, "y": -56.0},
        {"room_id": "bedroom", "component_id": "buzzer_main", "kind": "buzzer", "label": "BZ", "x": 160.0, "y": 16.0},
        {"room_id": "toilet", "component_id": "light_main", "kind": "light", "label": "L", "x": 210.0, "y": 138.0},
        {"room_id": "toilet", "component_id": "door_main", "kind": "door", "label": "D", "x": 170.0, "y": 94.0},
        {"room_id": "toilet", "component_id": "buzzer_main", "kind": "buzzer", "label": "BZ", "x": 244.0, "y": 138.0},
        {"room_id": "garage", "component_id": "light_main", "kind": "light", "label": "L", "x": 212.0, "y": 18.0},
        {"room_id": "garage", "component_id": "door_main", "kind": "door", "label": "D", "x": 170.0, "y": -56.0},
        {"room_id": "garage", "component_id": "buzzer_main", "kind": "buzzer", "label": "BZ", "x": 286.0, "y": 18.0},
    ],
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
