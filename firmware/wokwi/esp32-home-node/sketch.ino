#include <ArduinoJson.h>
#include <DHTesp.h>
#include <ESP32Servo.h>
#include <PubSubClient.h>
#include <WiFi.h>

#include "config.h"

static const int LIGHT_PIN = 26;
static const int AC_PIN = 27;
static const int DOOR_PIN = 18;
static const int DOOR_LOCKED_LED_PIN = 19;
static const int DOOR_UNLOCKED_LED_PIN = 25;
static const int DOOR_LOCKED_ANGLE = 180;
static const int DOOR_UNLOCKED_ANGLE = 0;
static const int OCCUPANCY_PIN = 5;
static const int GAS_PIN = 34;
static const int GAS_ALERT_PIN = 33;
static const int BUZZER_PIN = 32;
static const int LDR_PIN = 35;
static const int DHT_PIN = 4;
static const unsigned long GAS_CONFIRM_TIMEOUT_MS = 30000;
static const unsigned long BUZZER_TOGGLE_MS = 300;
static const int BUZZER_CHANNEL = 0;
static const int BUZZER_FREQUENCY = 2200;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
DHTesp dht;
Servo doorServo;

String doorState = "locked";
bool lightOn = false;
int lightBrightness = 80;
bool acOn = false;
int acTargetTemp = 22;
bool gasOverrideActive = false;
int gasOverridePpm = 0;
bool gasConfirmationPending = false;
bool gasConfirmed = false;
bool gasBuzzerActive = false;
bool buzzerToneOn = false;
unsigned long gasCommandMs = 0;
unsigned long lastBuzzerToggleMs = 0;
unsigned long lastSensorPublishMs = 0;

String deviceTopic(const char *deviceId) {
  return String("robocompagnon/home/rooms/") + ROOM_ID + "/devices/" + deviceId + "/state";
}

String sensorTopic(const char *sensorName) {
  return String("robocompagnon/home/rooms/") + ROOM_ID + "/sensors/" + sensorName;
}

void setDoorLocked(bool locked) {
  doorState = locked ? "locked" : "unlocked";
  doorServo.write(locked ? DOOR_LOCKED_ANGLE : DOOR_UNLOCKED_ANGLE);
  digitalWrite(DOOR_LOCKED_LED_PIN, locked ? HIGH : LOW);
  digitalWrite(DOOR_UNLOCKED_LED_PIN, locked ? LOW : HIGH);
  Serial.println(locked ? "Door locked" : "Door unlocked");
}

void publishJson(const String &topic, JsonDocument &doc) {
  char buffer[1024];
  size_t length = serializeJson(doc, buffer, sizeof(buffer));
  mqttClient.publish(topic.c_str(), buffer, length);
}

void publishDeviceStates() {
  Serial.println("Publishing device states...");
  StaticJsonDocument<256> lightDoc;
  lightDoc["id"] = "light_main";
  lightDoc["type"] = "light";
  lightDoc["name"] = "Main Light";
  lightDoc["state"] = lightOn ? "on" : "off";
  lightDoc["brightness"] = lightOn ? lightBrightness : 0;
  lightDoc["power_w"] = lightOn ? max(1, (int)roundf(12.0f * (lightBrightness / 100.0f))) : 0;
  publishJson(deviceTopic("light_main"), lightDoc);

  StaticJsonDocument<256> acDoc;
  acDoc["id"] = "ac_main";
  acDoc["type"] = "ac";
  acDoc["name"] = "Main AC";
  acDoc["state"] = acOn ? "on" : "off";
  acDoc["mode"] = "cool";
  acDoc["target_temp"] = acTargetTemp;
  acDoc["fan_speed"] = 2;
  acDoc["power_w"] = acOn ? 1200 : 0;
  publishJson(deviceTopic("ac_main"), acDoc);

  StaticJsonDocument<256> doorDoc;
  doorDoc["id"] = "door_main";
  doorDoc["type"] = "door";
  doorDoc["name"] = "Front Door";
  doorDoc["state"] = doorState;
  publishJson(deviceTopic("door_main"), doorDoc);

  StaticJsonDocument<128> buzzerDoc;
  buzzerDoc["id"] = "buzzer_main";
  buzzerDoc["type"] = "buzzer";
  buzzerDoc["name"] = "Gas Safety Buzzer";
  buzzerDoc["state"] = gasBuzzerActive ? "on" : "off";
  publishJson(deviceTopic("buzzer_main"), buzzerDoc);
}

template <typename TValue>
void publishSensorValue(const char *name, TValue value) {
  StaticJsonDocument<128> doc;
  doc["name"] = name;
  doc["value"] = value;
  publishJson(sensorTopic(name), doc);
}

void publishSensors() {
  Serial.println("Publishing sensor values...");
  TempAndHumidity reading = dht.getTempAndHumidity();
  float temperature = isnan(reading.temperature) ? 25.0 : reading.temperature;
  float humidity = isnan(reading.humidity) ? 50.0 : reading.humidity;
  bool occupancy = digitalRead(OCCUPANCY_PIN) == HIGH;
  int gasRaw = analogRead(GAS_PIN);
  int ldrRaw = analogRead(LDR_PIN);
  int gasPpm = gasOverrideActive ? gasOverridePpm : map(gasRaw, 0, 4095, 50, 800);
  int lightLux = map(ldrRaw, 0, 4095, 10, 900);

  publishSensorValue("temperature", roundf(temperature * 10.0f) / 10.0f);
  publishSensorValue("humidity", (int)roundf(humidity));
  publishSensorValue("occupancy", occupancy);
  publishSensorValue("gas_ppm", gasPpm);
  publishSensorValue("light_level", lightLux);

  if (gasPpm > 400) {
    StaticJsonDocument<128> alertDoc;
    alertDoc["alert"] = true;
    alertDoc["message"] = "Gas leak detected!";
    publishJson(MQTT_ALERT_GAS_TOPIC, alertDoc);
    Serial.println("Gas alert published");
  }

  digitalWrite(GAS_ALERT_PIN, gasPpm > 400 ? HIGH : LOW);
}

int currentGasPpm() {
  if (gasOverrideActive) {
    return gasOverridePpm;
  }
  return map(analogRead(GAS_PIN), 0, 4095, 50, 800);
}

void setBuzzerOutput(bool enabled) {
  if (enabled) {
    ledcWriteTone(BUZZER_CHANNEL, BUZZER_FREQUENCY);
  } else {
    ledcWriteTone(BUZZER_CHANNEL, 0);
  }
  buzzerToneOn = enabled;
}

void resetGasSafety() {
  gasConfirmationPending = false;
  gasConfirmed = false;
  gasBuzzerActive = false;
  gasCommandMs = 0;
  setBuzzerOutput(false);
}

void armGasSafety() {
  gasConfirmationPending = true;
  gasConfirmed = false;
  gasBuzzerActive = false;
  gasCommandMs = millis();
  lastBuzzerToggleMs = millis();
  setBuzzerOutput(false);
}

void updateGasSafety() {
  int gasPpm = currentGasPpm();
  if (gasPpm <= 0) {
    resetGasSafety();
    return;
  }

  if (gasConfirmationPending && !gasConfirmed && millis() - gasCommandMs >= GAS_CONFIRM_TIMEOUT_MS) {
    gasBuzzerActive = true;
  }

  if (!gasBuzzerActive) {
    setBuzzerOutput(false);
    return;
  }

  if (millis() - lastBuzzerToggleMs >= BUZZER_TOGGLE_MS) {
    lastBuzzerToggleMs = millis();
    setBuzzerOutput(!buzzerToneOn);
  }
}

void publishResponse(const char *correlationId, bool ok, const String &message, const char *action, const char *deviceType) {
  StaticJsonDocument<512> responseDoc;
  responseDoc["correlation_id"] = correlationId;
  JsonObject result = responseDoc.createNestedObject("result");
  result["ok"] = ok;
  result["action"] = action;
  result["room"] = ROOM_ID;
  result["device_type"] = deviceType;
  result["message"] = message;
  publishJson(MQTT_RESPONSES_TOPIC, responseDoc);
}

void publishEvent(const char *action, const char *target, const char *rawText, const char *status, const String &message) {
  StaticJsonDocument<512> eventDoc;
  eventDoc["timestamp"] = millis();
  eventDoc["source"] = NODE_NAME;
  eventDoc["topic"] = MQTT_COMMANDS_TOPIC;
  eventDoc["room"] = ROOM_ID;
  eventDoc["action"] = action;
  eventDoc["target"] = target;
  eventDoc["status"] = status;
  eventDoc["raw_text"] = rawText;
  JsonObject details = eventDoc.createNestedObject("details");
  details["message"] = message;
  publishJson(MQTT_EVENTS_TOPIC, eventDoc);
}

void handleCommand(char *topic, byte *payload, unsigned int length) {
  Serial.print("MQTT message received on topic: ");
  Serial.println(topic);
  StaticJsonDocument<1024> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    Serial.println("Failed to parse MQTT command payload");
    return;
  }

  const char *correlationId = doc["correlation_id"] | "";
  JsonObject command = doc["command"];
  const char *room = command["room"] | "";
  const char *action = command["action"] | "";
  const char *deviceType = command["device_type"] | "";
  const char *rawText = command["raw_text"] | "";
  Serial.print("Action: ");
  Serial.print(action);
  Serial.print(" | Device: ");
  Serial.println(deviceType);
  if (String(room) != ROOM_ID) {
    Serial.println("Ignoring command for another room");
    return;
  }

  String message = "Unsupported command.";
  bool ok = true;

  if (String(deviceType) == "light") {
    if (String(action) == "turn_on") {
      lightOn = true;
      if (lightBrightness <= 0) {
        lightBrightness = 80;
      }
      digitalWrite(LIGHT_PIN, HIGH);
      message = "Living Room Main Light turned on.";
    } else if (String(action) == "turn_off") {
      lightOn = false;
      lightBrightness = 0;
      digitalWrite(LIGHT_PIN, LOW);
      message = "Living Room Main Light turned off.";
    } else if (String(action) == "set_brightness") {
      lightBrightness = command["parameters"]["brightness"] | lightBrightness;
      lightBrightness = constrain(lightBrightness, 0, 100);
      lightOn = lightBrightness > 0;
      digitalWrite(LIGHT_PIN, lightOn ? HIGH : LOW);
      message = "Living Room light brightness updated.";
    } else if (String(action) == "get_device_state") {
      message = lightOn ? "Living room light is on at " + String(lightBrightness) + "% brightness."
                        : "Living room light is off at 0% brightness.";
    } else {
      ok = false;
    }
  } else if (String(deviceType) == "ac") {
    if (String(action) == "turn_on") {
      acOn = true;
      digitalWrite(AC_PIN, HIGH);
      message = "Living Room Main AC turned on.";
    } else if (String(action) == "turn_off") {
      acOn = false;
      digitalWrite(AC_PIN, LOW);
      message = "Living Room Main AC turned off.";
    } else if (String(action) == "set_temperature") {
      acTargetTemp = command["parameters"]["target_temp"] | acTargetTemp;
      message = "Living Room AC target temperature updated.";
    } else if (String(action) == "get_device_state") {
      message = String("Living room AC is ") + (acOn ? "on" : "off") + " with a target of " + acTargetTemp + "C.";
    } else {
      ok = false;
    }
  } else if (String(deviceType) == "door") {
    if (String(action) == "lock") {
      setDoorLocked(true);
      message = "Living Room Front Door locked.";
    } else if (String(action) == "unlock") {
      setDoorLocked(false);
      message = "Living Room Front Door unlocked.";
    } else if (String(action) == "get_device_state") {
      message = String("Living Room Front Door is ") + doorState + ".";
    } else {
      ok = false;
    }
  } else if (String(action) == "get_sensor") {
    const char *sensorType = command["sensor_type"] | "";
    TempAndHumidity reading = dht.getTempAndHumidity();
    if (String(sensorType) == "temperature") {
      message = "The current temperature in the living room is " + String(reading.temperature, 1) + "C.";
    } else if (String(sensorType) == "humidity") {
      message = "The current humidity in the living room is " + String((int)roundf(reading.humidity)) + "%.";
    } else if (String(sensorType) == "gas_ppm") {
      int gasPpm = currentGasPpm();
      message = "Gas level in the living room is " + String(gasPpm) + " ppm.";
    } else if (String(sensorType) == "light_level") {
      int lightLux = map(analogRead(LDR_PIN), 0, 4095, 10, 900);
      message = "The current light level in the living room is " + String(lightLux) + " lux.";
    } else {
      ok = false;
    }
  } else if (String(action) == "set_gas_state") {
    bool enabled = command["parameters"]["enabled"] | false;
    gasOverrideActive = true;
    if (enabled && gasOverridePpm <= 0) {
      gasOverridePpm = 550;
    } else if (!enabled) {
      gasOverridePpm = 0;
    }
    if (enabled) {
      armGasSafety();
      message = "Living Room gas simulation turned on. Confirm within 30 seconds to avoid buzzer alarm.";
    } else {
      resetGasSafety();
      message = "Living Room gas simulation turned off.";
    }
  } else if (String(action) == "set_gas_level") {
    gasOverrideActive = true;
    gasOverridePpm = command["parameters"]["gas_ppm"] | gasOverridePpm;
    gasOverridePpm = constrain(gasOverridePpm, 0, 1000);
    if (gasOverridePpm > 0) {
      armGasSafety();
      message = "Living Room gas level set to " + String(gasOverridePpm) + " ppm. Confirm within 30 seconds to avoid buzzer alarm.";
    } else {
      resetGasSafety();
      message = "Living Room gas level set to 0 ppm.";
    }
  } else if (String(action) == "confirm_gas_owner") {
    if (currentGasPpm() <= 0) {
      ok = false;
      message = "Gas is not active right now.";
    } else {
      gasConfirmationPending = false;
      gasConfirmed = true;
      gasBuzzerActive = false;
      setBuzzerOutput(false);
      message = "Living Room gas action confirmed by user. Buzzer remains off.";
    }
  } else {
    ok = false;
  }

  if (!ok) {
    message = "Unsupported command for Wokwi home node.";
  }

  publishDeviceStates();
  publishSensors();
  publishResponse(correlationId, ok, message, action, deviceType);
  publishEvent(action, deviceType, rawText, ok ? "success" : "error", message);
  Serial.print("Command result: ");
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
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }
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

void setup() {
  Serial.begin(115200);
  delay(250);
  Serial.println("Wokwi ESP32 home node booting...");
  pinMode(LIGHT_PIN, OUTPUT);
  pinMode(AC_PIN, OUTPUT);
  pinMode(DOOR_LOCKED_LED_PIN, OUTPUT);
  pinMode(DOOR_UNLOCKED_LED_PIN, OUTPUT);
  pinMode(GAS_ALERT_PIN, OUTPUT);
  pinMode(OCCUPANCY_PIN, INPUT);
  digitalWrite(LIGHT_PIN, LOW);
  digitalWrite(AC_PIN, LOW);
  digitalWrite(DOOR_LOCKED_LED_PIN, LOW);
  digitalWrite(DOOR_UNLOCKED_LED_PIN, LOW);
  digitalWrite(GAS_ALERT_PIN, LOW);

  dht.setup(DHT_PIN, DHTesp::DHT22);
  doorServo.attach(DOOR_PIN);
  ledcSetup(BUZZER_CHANNEL, BUZZER_FREQUENCY, 8);
  ledcAttachPin(BUZZER_PIN, BUZZER_CHANNEL);
  setBuzzerOutput(false);
  setDoorLocked(true);

  ensureWiFi();
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(handleCommand);
  Serial.println("Setup complete");
}

void loop() {
  ensureWiFi();
  ensureMqtt();
  mqttClient.loop();
  updateGasSafety();

  if (millis() - lastSensorPublishMs > 5000) {
    publishDeviceStates();
    publishSensors();
    lastSensorPublishMs = millis();
  }
}
