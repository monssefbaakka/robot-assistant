class MQTTTopics:
    COMMANDS = "robocompagnon/home/commands"
    RESPONSES = "robocompagnon/home/responses"
    EVENTS = "robocompagnon/home/events"
    SNAPSHOT = "robocompagnon/home/snapshot"
    ALERT_GAS = "robocompagnon/home/alerts/gas"

    @staticmethod
    def room_device_state(room_id, device_id):
        return f"robocompagnon/home/rooms/{room_id}/devices/{device_id}/state"

    @staticmethod
    def room_sensor_state(room_id, sensor_name):
        return f"robocompagnon/home/rooms/{room_id}/sensors/{sensor_name}"
