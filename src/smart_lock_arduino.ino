#include <WiFiS3.h>
#include <ArduinoMqttClient.h>
#include "Arduino_LED_Matrix.h"
ArduinoLEDMatrix matrix;

// Full matrix ON
const uint32_t frameOn[3] = {
  0xFFFFFFFF,
  0xFFFFFFFF,
  0xFFFFFFFF
};

// Full matrix OFF
const uint32_t frameOff[3] = {
  0x00000000,
  0x00000000,
  0x00000000
};

// ── WiFi credentials ──
const char* ssid     = "TC-9E03A";//"siddiq";//
const char* password = "j2Wpr2mUN28f";//"123456789";//

// ── MQTT Broker ──
const char* broker = "192.168.0.5";//"172.20.10.10";
const int   port   = 1883;

// ── MQTT Topics ──
const char* TOPIC_COMMAND  = "door/command";
const char* TOPIC_ACK      = "door/ack";
const char* TOPIC_STATUS   = "door/status";
const char* TOPIC_SENSOR   = "door/sensor";
const char* TOPIC_ACTIVATE = "door/activate";

// ── Lock & Door State ──
String lockState = "LOCKED";
String doorState = "CLOSED";

// ── Auto-lock Timer ──
const int AUTOLOCK_SECONDS = 10;
unsigned long unlockTime = 0;
bool autolockPending = false;

// ── Mic Setup ──
const int micPin = A0;
const int MIC_LED = 13;        // pin 13 = sound detected
unsigned long lastSoundTime = 0;
const unsigned long HOLD_MS = 3000;
int baseline = 0;
bool systemActivated = false;


WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

void publishStatus() {
  String payload = "{\"lock_state\":\"" + lockState + "\",\"door_state\":\"" + doorState + "\"}";
  mqttClient.beginMessage(TOPIC_STATUS);
  mqttClient.print(payload);
  mqttClient.endMessage();
}

void doLock(String reason) {
  lockState = "LOCKED";
  autolockPending = false;


  //digitalWrite(LED_BUILTIN, LOW);  
  matrix.loadFrame(frameOff);  

  mqttClient.beginMessage(TOPIC_ACK);
  mqttClient.print("LOCKED (" + reason + ")");
  mqttClient.endMessage();
  Serial.println("LOCKED (" + reason + ")");
  publishStatus();
}

void doUnlock(String reason) {
  lockState = "UNLOCKED";

  //digitalWrite(LED_BUILTIN, HIGH); 
  matrix.loadFrame(frameOn); 

  mqttClient.beginMessage(TOPIC_ACK);
  mqttClient.print("UNLOCKED (" + reason + ")");
  mqttClient.endMessage();
  Serial.println("UNLOCKED (" + reason + ")");
  publishStatus();

  unlockTime = millis();
  autolockPending = true;
  Serial.println("Auto-lock timer started (" + String(AUTOLOCK_SECONDS) + "s)...");
}

void onMqttMessage(int messageSize) {
  String topic = mqttClient.messageTopic();
  String payload = "";
  while (mqttClient.available()) payload += (char)mqttClient.read();
  payload.trim(); payload.toUpperCase();

  if (topic == TOPIC_COMMAND) {
    if (payload == "UNLOCK") doUnlock("COMMAND");
    else if (payload == "LOCK") doLock("COMMAND");
  } else if (topic == TOPIC_SENSOR) {
    doorState = payload;
    Serial.println("Door sensor: " + doorState);
    publishStatus();
    if (doorState == "CLOSED" && lockState == "UNLOCKED") {
      doLock("AUTO_AFTER_CLOSE");
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);   // built-in LED starts OFF
  pinMode(MIC_LED, OUTPUT);
  digitalWrite(MIC_LED, LOW);       // pin 13 starts OFF

  matrix.begin();
  matrix.loadFrame(frameOff);


  // ── Mic baseline calibration ──
  Serial.println("Calibrating mic...");
  long sum = 0;
  for (int i = 0; i < 1000; i++) {
    sum += analogRead(micPin);
    delay(1);
  }
  baseline = sum / 1000;
  Serial.print("Baseline: ");
  Serial.println(baseline);

  // ── WiFi ──
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");

  // ── MQTT ──
  Serial.print("Connecting to MQTT broker...");
  mqttClient.setId("arduino_client");
  while (!mqttClient.connect(broker, port)) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nMQTT connected!");

  mqttClient.onMessage(onMqttMessage);
  mqttClient.subscribe(TOPIC_COMMAND);
  mqttClient.subscribe(TOPIC_SENSOR);
  Serial.println("Arduino ready!");
  Serial.println("Waiting for sound to activate system...");
  publishStatus();
}

void loop() {
  mqttClient.poll();

  // ── Mic detection ──
  int value = analogRead(micPin);
  int diff = abs(value - baseline);

  if (diff > 2) {
    lastSoundTime = millis();
    digitalWrite(MIC_LED, HIGH);    // pin 13 ON = sound detected
    if (!systemActivated) {
      systemActivated = true;
      Serial.println("Sound detected! Sending ACTIVATE to Pi...");
      mqttClient.beginMessage(TOPIC_ACTIVATE);
      mqttClient.print("ACTIVATE");
      mqttClient.endMessage();
    }
  }

  if (millis() - lastSoundTime > HOLD_MS) {
    systemActivated = false;
    digitalWrite(MIC_LED, LOW);     // pin 13 OFF = silence
  }

  // ── Auto-lock timer ──
  if (autolockPending && lockState == "UNLOCKED") {
    unsigned long elapsed = (millis() - unlockTime) / 1000;
    if (elapsed >= AUTOLOCK_SECONDS) {
      if (doorState == "CLOSED") {
        Serial.println("Auto-lock triggered!");
        doLock("AUTO_TIMER");
      } else {
        Serial.println("Door still open, waiting to close...");
        unlockTime = millis() - (AUTOLOCK_SECONDS - 1) * 1000;
      }
    }
  }
}

//Led-Matrix ON for 10 secs when unlocking
//Led pin13 ON for 3 secs when sound is detected

//Mic detects sound → sends "ACTIVATE" to door/activate topic → Pi receives it
//Pi starts face recognition
//If face recognized → Pi sends "UNLOCK" to door/command → Arduino unlocks