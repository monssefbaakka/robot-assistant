#ifndef HOME_NODE_CONFIG_H
#define HOME_NODE_CONFIG_H

// Wokwi cloud Wi-Fi
#define WIFI_SSID "Wokwi-GUEST"
#define WIFI_PASSWORD ""

// Use a broker reachable from Wokwi cloud.
// Wokwi cannot connect to localhost on your PC directly.
#define MQTT_HOST "test.mosquitto.org"
#define MQTT_PORT 1883

// Stable topic contract used by the Python app
#define MQTT_COMMANDS_TOPIC "robocompagnon/home/commands"
#define MQTT_RESPONSES_TOPIC "robocompagnon/home/responses"
#define MQTT_EVENTS_TOPIC "robocompagnon/home/events"
#define MQTT_ALERT_GAS_TOPIC "robocompagnon/home/alerts/gas"

// Device identity
#define ROOM_ID "living_room"
#define NODE_NAME "wokwi-esp32-home-node"

#endif
