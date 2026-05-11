#include <Arduino.h>
#include <ArduinoJson.h>
#include <DHTesp.h>
#include <ESP32Servo.h>
#include <PubSubClient.h>
#include <WiFi.h>

#include "../config.h"

static const int ROOM_COUNT = 5;
static const int LIVING_ROOM_INDEX = 0;
static const int KITCHEN_INDEX = 1;
static const int BEDROOM_INDEX = 2;
static const int TOILET_INDEX = 3;
static const int GARAGE_INDEX = 4;

static const char *ROOM_IDS[ROOM_COUNT] = {
  "living_room",
  "kitchen",
  "bedroom",
  "toilet",
  "garage",
};

static const char *ROOM_NAMES[ROOM_COUNT] = {
  "Living Room",
  "Kitchen",
  "Bedroom",
  "Toilet",
  "Garage",
};

static const int LIGHT_PINS[ROOM_COUNT] = {26, 21, 14, 22, 17};
static const int AC_PINS[ROOM_COUNT] = {27, -1, 13, -1, -1};
static const int DOOR_PINS[ROOM_COUNT] = {18, -1, 23, 15, 16};

static const bool ROOM_HAS_AC[ROOM_COUNT] = {true, false, true, false, false};
static const bool ROOM_HAS_DOOR[ROOM_COUNT] = {true, false, true, true, true};
static const bool ROOM_HAS_GAS_SENSOR[ROOM_COUNT] = {true, true, false, false, false};

static const char *LIGHT_NAMES[ROOM_COUNT] = {
  "Main Light",
  "Kitchen Light",
  "Bedroom Light",
  "Toilet Light",
  "Garage Light",
};

static const char *AC_NAMES[ROOM_COUNT] = {
  "Main AC",
  "",
  "Bedroom AC",
  "",
  "",
};

static const char *DOOR_NAMES[ROOM_COUNT] = {
  "Front Door",
  "",
  "Bedroom Door",
  "Toilet Door",
  "Garage Door",
};

static const int DHT_PIN = 4;
static const int OCCUPANCY_PIN = 5;
static const int GAS_PIN = 34;
static const int GAS_ALERT_PIN = 33;
static const int BUZZER_PIN = 32;
static const int LDR_PIN = 35;
static const int DOOR_LOCKED_LED_PIN = 19;
static const int DOOR_UNLOCKED_LED_PIN = 25;
static const int DOOR_LOCKED_ANGLE = 90;
static const int DOOR_UNLOCKED_ANGLE = 0;
static const int DOOR_SWEEP_STEP = 3;
static const int DOOR_SWEEP_DELAY_MS = 20;

static const int BUZZER_LEDC_CHANNEL = 1;
static const int BUZZER_FREQUENCY = 2200;
static const unsigned long GAS_CONFIRM_TIMEOUT_MS = 60000;
static const unsigned long BUZZER_TOGGLE_MS = 300;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
DHTesp dht;
Servo livingDoorServo;
Servo bedroomDoorServo;
Servo toiletDoorServo;
Servo garageDoorServo;
Servo *doorServos[ROOM_COUNT] = {&livingDoorServo, nullptr, &bedroomDoorServo, &toiletDoorServo, &garageDoorServo};

bool lightOn[ROOM_COUNT] = {true, false, false, false, false};
int lightBrightness[ROOM_COUNT] = {80, 0, 0, 0, 0};
bool acOn[ROOM_COUNT] = {false, false, false, false, false};
int acTargetTemp[ROOM_COUNT] = {22, 0, 23, 0, 0};
String doorState[ROOM_COUNT] = {"locked", "", "unlocked", "unlocked", "locked"};
int doorServoAngle[ROOM_COUNT] = {
  DOOR_UNLOCKED_ANGLE,
  DOOR_UNLOCKED_ANGLE,
  DOOR_UNLOCKED_ANGLE,
  DOOR_UNLOCKED_ANGLE,
  DOOR_UNLOCKED_ANGLE,
};
bool gasOverrideActive = false;
int gasOverridePpm = 0;
bool gasPending = false;
bool gasConfirmed = false;
bool gasBuzzerActive = false;
bool buzzerToneOn = false;
unsigned long gasArmedMs = 0;
unsigned long lastBuzzerToggleMs = 0;
unsigned long lastSensorPublishMs = 0;

float sensorTemperature[ROOM_COUNT] = {25.0f, 26.2f, 24.3f, 23.8f, 22.6f};
int sensorHumidity[ROOM_COUNT] = {50, 52, 47, 58, 51};
bool sensorOccupancy[ROOM_COUNT] = {true, false, true, false, false};
int sensorLightLevel[ROOM_COUNT] = {600, 210, 120, 90, 60};
int sensorGasPpm[ROOM_COUNT] = {50, 120, 0, 0, 0};

int roomIndexFromId(const char *roomId) {
  for (int index = 0; index < ROOM_COUNT; index++) {
    if (String(roomId) == ROOM_IDS[index]) {
      return index;
    }
  }
  return -1;
}

String roomLabel(int roomIndex) {
  if (roomIndex < 0 || roomIndex >= ROOM_COUNT) return "Room";
  return String(ROOM_NAMES[roomIndex]);
}

String deviceTopic(int roomIndex, const char *deviceId) {
  return String("robocompagnon/home/rooms/") + ROOM_IDS[roomIndex] + "/devices/" + deviceId + "/state";
}

String sensorTopic(int roomIndex, const char *sensorName) {
  return String("robocompagnon/home/rooms/") + ROOM_IDS[roomIndex] + "/sensors/" + sensorName;
}

int currentGasPpm() {
  if (gasOverrideActive) return gasOverridePpm;
  return map(analogRead(GAS_PIN), 0, 4095, 50, 800);
}

void setBuzzer(bool on) {
  if (on) {
    ledcWriteTone(BUZZER_LEDC_CHANNEL, BUZZER_FREQUENCY);
  } else {
    ledcWriteTone(BUZZER_LEDC_CHANNEL, 0);
  }
  buzzerToneOn = on;
}

void armGasSafety() {
  gasPending = true;
  gasConfirmed = false;
  gasBuzzerActive = false;
  gasArmedMs = millis();
  lastBuzzerToggleMs = millis();
  setBuzzer(false);
}

void resetGasSafety() {
  gasPending = false;
  gasConfirmed = false;
  gasBuzzerActive = false;
  setBuzzer(false);
}

void updateGasSafety() {
  if (!gasPending && !gasBuzzerActive) {
    setBuzzer(false);
    return;
  }
  if (gasPending && !gasConfirmed && millis() - gasArmedMs >= GAS_CONFIRM_TIMEOUT_MS) {
    gasPending = false;
    gasBuzzerActive = true;
  }
  if (gasBuzzerActive && millis() - lastBuzzerToggleMs >= BUZZER_TOGGLE_MS) {
    lastBuzzerToggleMs = millis();
    setBuzzer(!buzzerToneOn);
  } else if (!gasBuzzerActive) {
    setBuzzer(false);
  }
}

void moveDoorServo(int roomIndex, int targetAngle) {
  if (!ROOM_HAS_DOOR[roomIndex] || !doorServos[roomIndex]) return;
  targetAngle = constrain(targetAngle, 0, 180);
  if (targetAngle == doorServoAngle[roomIndex]) return;

  int step = targetAngle > doorServoAngle[roomIndex] ? DOOR_SWEEP_STEP : -DOOR_SWEEP_STEP;
  int angle = doorServoAngle[roomIndex];
  while (true) {
    angle += step;
    if ((step > 0 && angle >= targetAngle) || (step < 0 && angle <= targetAngle)) break;
    doorServos[roomIndex]->write(angle);
    delay(DOOR_SWEEP_DELAY_MS);
  }
  doorServos[roomIndex]->write(targetAngle);
  doorServoAngle[roomIndex] = targetAngle;
}

void setDoorLocked(int roomIndex, bool locked) {
  if (!ROOM_HAS_DOOR[roomIndex]) return;
  doorState[roomIndex] = locked ? "locked" : "unlocked";
  moveDoorServo(roomIndex, locked ? DOOR_LOCKED_ANGLE : DOOR_UNLOCKED_ANGLE);

  if (roomIndex == LIVING_ROOM_INDEX) {
    digitalWrite(DOOR_LOCKED_LED_PIN, locked ? HIGH : LOW);
    digitalWrite(DOOR_UNLOCKED_LED_PIN, locked ? LOW : HIGH);
  }
}

void publishJson(const String &topic, JsonDocument &doc) {
  char buffer[1024];
  size_t length = serializeJson(doc, buffer, sizeof(buffer));
  mqttClient.publish(topic.c_str(), buffer, length);
}

void updateSensorCache() {
  TempAndHumidity reading = dht.getTempAndHumidity();
  float baseTemperature = isnan(reading.temperature) ? 25.0f : reading.temperature;
  float baseHumidity = isnan(reading.humidity) ? 50.0f : reading.humidity;
  bool occupancySwitchOn = digitalRead(OCCUPANCY_PIN) == HIGH;
  int gasPpm = currentGasPpm();
  int ldrRaw = analogRead(LDR_PIN);
  int livingLux = map(ldrRaw, 0, 4095, 10, 900);

  sensorTemperature[LIVING_ROOM_INDEX] = baseTemperature;
  sensorTemperature[KITCHEN_INDEX] = baseTemperature + 1.2f;
  sensorTemperature[BEDROOM_INDEX] = baseTemperature - 0.7f;
  sensorTemperature[TOILET_INDEX] = baseTemperature - 1.2f;
  sensorTemperature[GARAGE_INDEX] = baseTemperature - 2.4f;

  sensorHumidity[LIVING_ROOM_INDEX] = (int)roundf(baseHumidity);
  sensorHumidity[KITCHEN_INDEX] = min(90, sensorHumidity[LIVING_ROOM_INDEX] + 4);
  sensorHumidity[BEDROOM_INDEX] = max(25, sensorHumidity[LIVING_ROOM_INDEX] - 3);
  sensorHumidity[TOILET_INDEX] = min(95, sensorHumidity[LIVING_ROOM_INDEX] + 8);
  sensorHumidity[GARAGE_INDEX] = min(90, max(25, sensorHumidity[LIVING_ROOM_INDEX] + 3));

  sensorOccupancy[LIVING_ROOM_INDEX] = true;
  sensorOccupancy[KITCHEN_INDEX] = false;
  sensorOccupancy[BEDROOM_INDEX] = occupancySwitchOn;
  sensorOccupancy[TOILET_INDEX] = false;
  sensorOccupancy[GARAGE_INDEX] = false;

  sensorLightLevel[LIVING_ROOM_INDEX] = lightOn[LIVING_ROOM_INDEX] ? max(livingLux, 550) : livingLux;
  sensorLightLevel[KITCHEN_INDEX] = lightOn[KITCHEN_INDEX] ? 400 : 40;
  sensorLightLevel[BEDROOM_INDEX] = lightOn[BEDROOM_INDEX] ? 380 : 40;
  sensorLightLevel[TOILET_INDEX] = lightOn[TOILET_INDEX] ? 400 : 35;
  sensorLightLevel[GARAGE_INDEX] = lightOn[GARAGE_INDEX] ? 320 : 20;

  sensorGasPpm[LIVING_ROOM_INDEX] = gasPpm;
  sensorGasPpm[KITCHEN_INDEX] = gasPpm;
  sensorGasPpm[BEDROOM_INDEX] = 0;
  sensorGasPpm[TOILET_INDEX] = 0;
  sensorGasPpm[GARAGE_INDEX] = 0;

  digitalWrite(GAS_ALERT_PIN, gasPpm > 400 ? HIGH : LOW);
}

void publishDeviceStates() {
  for (int roomIndex = 0; roomIndex < ROOM_COUNT; roomIndex++) {
    StaticJsonDocument<256> lightDoc;
    lightDoc["id"] = "light_main";
    lightDoc["type"] = "light";
    lightDoc["name"] = LIGHT_NAMES[roomIndex];
    lightDoc["state"] = lightOn[roomIndex] ? "on" : "off";
    lightDoc["brightness"] = lightOn[roomIndex] ? lightBrightness[roomIndex] : 0;
    lightDoc["power_w"] = lightOn[roomIndex] ? max(1, (int)roundf(12.0f * (lightBrightness[roomIndex] / 100.0f))) : 0;
    publishJson(deviceTopic(roomIndex, "light_main"), lightDoc);

    if (ROOM_HAS_AC[roomIndex]) {
      StaticJsonDocument<256> acDoc;
      acDoc["id"] = "ac_main";
      acDoc["type"] = "ac";
      acDoc["name"] = AC_NAMES[roomIndex];
      acDoc["state"] = acOn[roomIndex] ? "on" : "off";
      acDoc["mode"] = "cool";
      acDoc["target_temp"] = acTargetTemp[roomIndex];
      acDoc["fan_speed"] = roomIndex == BEDROOM_INDEX ? 1 : 2;
      acDoc["power_w"] = acOn[roomIndex] ? 1200 : 0;
      publishJson(deviceTopic(roomIndex, "ac_main"), acDoc);
    }

    if (ROOM_HAS_DOOR[roomIndex]) {
      StaticJsonDocument<256> doorDoc;
      doorDoc["id"] = "door_main";
      doorDoc["type"] = "door";
      doorDoc["name"] = DOOR_NAMES[roomIndex];
      doorDoc["state"] = doorState[roomIndex];
      publishJson(deviceTopic(roomIndex, "door_main"), doorDoc);
    }

    StaticJsonDocument<128> buzzerDoc;
    buzzerDoc["id"] = "buzzer_main";
    buzzerDoc["type"] = "buzzer";
    buzzerDoc["name"] = "Gas Safety Buzzer";
    buzzerDoc["state"] = gasBuzzerActive ? "on" : "off";
    publishJson(deviceTopic(roomIndex, "buzzer_main"), buzzerDoc);
  }
}

template <typename TValue>
void publishSensorValue(int roomIndex, const char *name, TValue value) {
  StaticJsonDocument<128> doc;
  doc["name"] = name;
  doc["value"] = value;
  publishJson(sensorTopic(roomIndex, name), doc);
}

void publishSensors() {
  updateSensorCache();

  for (int roomIndex = 0; roomIndex < ROOM_COUNT; roomIndex++) {
    publishSensorValue(roomIndex, "temperature", roundf(sensorTemperature[roomIndex] * 10.0f) / 10.0f);
    publishSensorValue(roomIndex, "humidity", sensorHumidity[roomIndex]);
    publishSensorValue(roomIndex, "occupancy", sensorOccupancy[roomIndex]);
    publishSensorValue(roomIndex, "light_level", sensorLightLevel[roomIndex]);
    if (ROOM_HAS_GAS_SENSOR[roomIndex]) {
      publishSensorValue(roomIndex, "gas_ppm", sensorGasPpm[roomIndex]);
    }
  }

  if (sensorGasPpm[KITCHEN_INDEX] > 400) {
    StaticJsonDocument<128> alertDoc;
    alertDoc["alert"] = true;
    alertDoc["message"] = "Gas leak detected!";
    publishJson(MQTT_ALERT_GAS_TOPIC, alertDoc);
  }
}

void publishResponse(const char *correlationId, bool ok, const String &message, const char *action, const char *deviceType, const char *roomId) {
  StaticJsonDocument<512> responseDoc;
  responseDoc["correlation_id"] = correlationId;
  JsonObject result = responseDoc.createNestedObject("result");
  result["ok"] = ok;
  result["action"] = action;
  result["room"] = roomId;
  if (strlen(deviceType) > 0) result["device_type"] = deviceType;
  result["message"] = message;
  publishJson(MQTT_RESPONSES_TOPIC, responseDoc);
}

void publishEvent(const char *action, const char *target, const char *rawText, const char *status, const char *roomId, const String &message) {
  StaticJsonDocument<512> eventDoc;
  eventDoc["timestamp"] = millis();
  eventDoc["source"] = NODE_NAME;
  eventDoc["topic"] = MQTT_COMMANDS_TOPIC;
  eventDoc["room"] = roomId;
  eventDoc["action"] = action;
  eventDoc["target"] = target;
  eventDoc["status"] = status;
  eventDoc["raw_text"] = rawText;
  JsonObject details = eventDoc.createNestedObject("details");
  details["message"] = message;
  publishJson(MQTT_EVENTS_TOPIC, eventDoc);
}

String sensorMessage(int roomIndex, const char *sensorType) {
  if (String(sensorType) == "temperature") {
    return "The current temperature in the " + String(ROOM_NAMES[roomIndex]) + " is " + String(sensorTemperature[roomIndex], 1) + "C.";
  }
  if (String(sensorType) == "humidity") {
    return "The current humidity in the " + String(ROOM_NAMES[roomIndex]) + " is " + String(sensorHumidity[roomIndex]) + "%.";
  }
  if (String(sensorType) == "gas_ppm") {
    return "Gas level in the " + String(ROOM_NAMES[roomIndex]) + " is " + String(sensorGasPpm[roomIndex]) + " ppm.";
  }
  if (String(sensorType) == "light_level") {
    return "The current light level in the " + String(ROOM_NAMES[roomIndex]) + " is " + String(sensorLightLevel[roomIndex]) + " lux.";
  }
  return "Unsupported sensor request.";
}

bool supportsDeviceType(int roomIndex, const String &deviceType) {
  if (deviceType == "light") return true;
  if (deviceType == "ac") return ROOM_HAS_AC[roomIndex];
  if (deviceType == "door") return ROOM_HAS_DOOR[roomIndex];
  return false;
}

void handleCommand(char *topic, byte *payload, unsigned int length) {
  StaticJsonDocument<1024> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    Serial.println("Failed to parse MQTT command payload");
    return;
  }

  const char *correlationId = doc["correlation_id"] | "";
  JsonObject command = doc["command"];
  const char *roomId = command["room"] | "living_room";
  const char *action = command["action"] | "";
  const char *deviceType = command["device_type"] | "";
  const char *sensorType = command["sensor_type"] | "";
  const char *rawText = command["raw_text"] | "";

  int roomIndex = roomIndexFromId(roomId);
  bool ok = true;
  String message = "Unsupported command for Wokwi home node.";

  if (roomIndex < 0) {
    ok = false;
    message = "Unknown room requested.";
  } else {
    String roomName = roomLabel(roomIndex);
    String deviceTypeStr = String(deviceType);
    String actionStr = String(action);

    if (deviceTypeStr.length() > 0) {
      if (!supportsDeviceType(roomIndex, deviceTypeStr)) {
        ok = false;
        message = roomName + " does not have that device.";
      } else if (deviceTypeStr == "light") {
        if (actionStr == "turn_on") {
          lightOn[roomIndex] = true;
          if (lightBrightness[roomIndex] <= 0) lightBrightness[roomIndex] = 80;
          digitalWrite(LIGHT_PINS[roomIndex], HIGH);
          message = roomName + " " + String(LIGHT_NAMES[roomIndex]) + " turned on.";
        } else if (actionStr == "turn_off") {
          lightOn[roomIndex] = false;
          lightBrightness[roomIndex] = 0;
          digitalWrite(LIGHT_PINS[roomIndex], LOW);
          message = roomName + " " + String(LIGHT_NAMES[roomIndex]) + " turned off.";
        } else if (actionStr == "set_brightness") {
          lightBrightness[roomIndex] = constrain(command["parameters"]["brightness"] | lightBrightness[roomIndex], 0, 100);
          lightOn[roomIndex] = lightBrightness[roomIndex] > 0;
          digitalWrite(LIGHT_PINS[roomIndex], lightOn[roomIndex] ? HIGH : LOW);
          message = roomName + " light brightness updated.";
        } else if (actionStr == "get_device_state") {
          message = roomName + " light is " + String(lightOn[roomIndex] ? "on" : "off") + " at " + String(lightOn[roomIndex] ? lightBrightness[roomIndex] : 0) + "% brightness.";
        } else {
          ok = false;
        }
      } else if (deviceTypeStr == "ac") {
        if (actionStr == "turn_on") {
          acOn[roomIndex] = true;
          digitalWrite(AC_PINS[roomIndex], HIGH);
          message = roomName + " " + String(AC_NAMES[roomIndex]) + " turned on.";
        } else if (actionStr == "turn_off") {
          acOn[roomIndex] = false;
          digitalWrite(AC_PINS[roomIndex], LOW);
          message = roomName + " " + String(AC_NAMES[roomIndex]) + " turned off.";
        } else if (actionStr == "set_temperature") {
          acTargetTemp[roomIndex] = constrain(command["parameters"]["target_temp"] | acTargetTemp[roomIndex], 16, 30);
          message = roomName + " AC target temperature updated.";
        } else if (actionStr == "get_device_state") {
          message = roomName + " AC is " + String(acOn[roomIndex] ? "on" : "off") + " with a target of " + String(acTargetTemp[roomIndex]) + "C.";
        } else {
          ok = false;
        }
      } else if (deviceTypeStr == "door") {
        if (actionStr == "lock") {
          setDoorLocked(roomIndex, true);
          message = roomName + " " + String(DOOR_NAMES[roomIndex]) + " locked.";
        } else if (actionStr == "unlock") {
          setDoorLocked(roomIndex, false);
          message = roomName + " " + String(DOOR_NAMES[roomIndex]) + " unlocked.";
        } else if (actionStr == "get_device_state") {
          message = roomName + " " + String(DOOR_NAMES[roomIndex]) + " is " + doorState[roomIndex] + ".";
        } else {
          ok = false;
        }
      } else {
        ok = false;
      }
    } else if (actionStr == "get_sensor") {
      updateSensorCache();
      if (String(sensorType) == "gas_ppm" && !ROOM_HAS_GAS_SENSOR[roomIndex]) {
        ok = false;
        message = roomName + " does not have a gas sensor.";
      } else {
        message = sensorMessage(roomIndex, sensorType);
        ok = message != "Unsupported sensor request.";
      }
    } else if (actionStr == "set_gas_state") {
      bool enabled = command["parameters"]["enabled"] | false;
      gasOverrideActive = true;
      if (enabled && gasOverridePpm <= 0) gasOverridePpm = 550;
      if (!enabled) gasOverridePpm = 0;
      if (enabled) {
        armGasSafety();
        message = roomName + " gas simulation turned on. Confirm within 60 seconds to avoid buzzer alarm.";
      } else {
        resetGasSafety();
        message = roomName + " gas simulation turned off.";
      }
    } else if (actionStr == "set_gas_level") {
      gasOverrideActive = true;
      gasOverridePpm = constrain(command["parameters"]["gas_ppm"] | gasOverridePpm, 0, 1000);
      if (gasOverridePpm > 0) {
        armGasSafety();
        message = roomName + " gas level set to " + String(gasOverridePpm) + " ppm. Confirm within 60 seconds to avoid buzzer alarm.";
      } else {
        resetGasSafety();
        message = roomName + " gas level set to 0 ppm.";
      }
    } else if (actionStr == "confirm_gas_owner") {
      updateSensorCache();
      if (sensorGasPpm[KITCHEN_INDEX] <= 0) {
        ok = false;
        message = "Gas is not active right now.";
      } else {
        gasPending = false;
        gasConfirmed = true;
        gasBuzzerActive = false;
        setBuzzer(false);
        message = roomName + " gas confirmed by user. Buzzer disarmed.";
      }
    } else {
      ok = false;
    }
  }

  if (!ok && message == "Unsupported command for Wokwi home node.") {
    message = "Unsupported command for Wokwi home node.";
  }

  publishDeviceStates();
  publishSensors();
  publishResponse(correlationId, ok, message, action, deviceType, roomId);
  publishEvent(action, strlen(deviceType) > 0 ? deviceType : sensorType, rawText, ok ? "success" : "error", roomId, message);
  Serial.println(message);
}

void ensureMqtt() {
  while (!mqttClient.connected()) {
    String clientId = String(NODE_NAME) + "-" + String(random(1000, 9999));
    Serial.print("Connecting to MQTT broker ");
    Serial.print(MQTT_HOST);
    Serial.print(":");
    Serial.println(MQTT_PORT);
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("MQTT connected");
      mqttClient.subscribe(MQTT_COMMANDS_TOPIC);
      Serial.print("Subscribed to: ");
      Serial.println(MQTT_COMMANDS_TOPIC);
      publishDeviceStates();
      publishSensors();
    } else {
      Serial.print("MQTT connect failed, rc=");
      Serial.println(mqttClient.state());
      delay(2000);
    }
  }
}

void ensureWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(250);
  }
  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void setupPins() {
  for (int roomIndex = 0; roomIndex < ROOM_COUNT; roomIndex++) {
    pinMode(LIGHT_PINS[roomIndex], OUTPUT);
    digitalWrite(LIGHT_PINS[roomIndex], lightOn[roomIndex] ? HIGH : LOW);

    if (ROOM_HAS_AC[roomIndex]) {
      pinMode(AC_PINS[roomIndex], OUTPUT);
      digitalWrite(AC_PINS[roomIndex], acOn[roomIndex] ? HIGH : LOW);
    }
  }

  pinMode(DOOR_LOCKED_LED_PIN, OUTPUT);
  pinMode(DOOR_UNLOCKED_LED_PIN, OUTPUT);
  pinMode(GAS_ALERT_PIN, OUTPUT);
  pinMode(OCCUPANCY_PIN, INPUT);
  digitalWrite(DOOR_LOCKED_LED_PIN, LOW);
  digitalWrite(DOOR_UNLOCKED_LED_PIN, LOW);
  digitalWrite(GAS_ALERT_PIN, LOW);
}

void setupDoors() {
  for (int roomIndex = 0; roomIndex < ROOM_COUNT; roomIndex++) {
    if (!ROOM_HAS_DOOR[roomIndex] || !doorServos[roomIndex]) continue;
    doorServos[roomIndex]->attach(DOOR_PINS[roomIndex]);
    doorServos[roomIndex]->write(DOOR_UNLOCKED_ANGLE);
    doorServoAngle[roomIndex] = DOOR_UNLOCKED_ANGLE;
    delay(250);
    setDoorLocked(roomIndex, doorState[roomIndex] == "locked");
  }
}

void setup() {
  Serial.begin(115200);
  delay(250);
  Serial.println("Wokwi ESP32 multi-room home node booting...");

  setupPins();

  dht.setup(DHT_PIN, DHTesp::DHT22);

  ledcSetup(BUZZER_LEDC_CHANNEL, BUZZER_FREQUENCY, 8);
  ledcAttachPin(BUZZER_PIN, BUZZER_LEDC_CHANNEL);
  setBuzzer(false);

  setupDoors();

  ensureWiFi();
  mqttClient.setBufferSize(2048);
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(handleCommand);
  Serial.println("Setup complete");
}

void loop() {
  ensureWiFi();
  ensureMqtt();
  mqttClient.loop();

  if (!gasOverrideActive) {
    int physPpm = map(analogRead(GAS_PIN), 0, 4095, 50, 800);
    if (physPpm > 400 && !gasPending && !gasBuzzerActive && !gasConfirmed) {
      armGasSafety();
    } else if (physPpm <= 400 && (gasPending || gasBuzzerActive)) {
      resetGasSafety();
    }
  }

  updateGasSafety();

  if (millis() - lastSensorPublishMs > 5000) {
    publishDeviceStates();
    publishSensors();
    lastSensorPublishMs = millis();
  }
}
