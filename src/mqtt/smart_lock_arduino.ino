#include <WiFiS3.h>
#include <ArduinoMqttClient.h>
// #include <Servo.h>  // ← uncomment when motor is available

// ── WiFi credentials (modify these credentials) ──
const char* ssid     = "TC-9E03A";
const char* password = "j2Wpr2mUN28f";

// ── MQTT Broker = Raspberry Pi IP ──
// Connect Pi to their network, run: hostname -I, use that IP below
const char* broker = "192.168.0.5";
const int   port   = 1883;

// ── MQTT Topics ──
const char* TOPIC_COMMAND = "door/command";
const char* TOPIC_ACK     = "door/ack";
const char* TOPIC_STATUS  = "door/status";
const char* TOPIC_SENSOR  = "door/sensor";

// ── Lock & Door State ──
String lockState = "LOCKED";
String doorState = "CLOSED";

// ── Auto-lock Timer ──
const int AUTOLOCK_SECONDS = 10;  // 10 secs to lock again after unlocking
unsigned long unlockTime = 0;
bool autolockPending = false;

// ── Servo Motor (uncomment when motor is available) ──
// Servo doorServo;
// const int SERVO_PIN = 9;       // ← change to the servo pin
// const int SERVO_LOCKED = 0;    // ← angle in degrees for LOCKED position
// const int SERVO_UNLOCKED = 90; // ← angle in degrees for UNLOCKED position

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

  // ── Servo: uncomment when motor is available ──
  // doorServo.write(SERVO_LOCKED);  // move servo to locked position
  // delay(500);                     // wait for servo to reach position

  // ── LED simulation (remove when motor is available) ──
  digitalWrite(LED_BUILTIN, LOW);   // LED OFF = LOCKED

  mqttClient.beginMessage(TOPIC_ACK);
  mqttClient.print("LOCKED (" + reason + ")");
  mqttClient.endMessage();
  Serial.println("LOCKED (" + reason + ")");
  publishStatus();
}

void doUnlock(String reason) {
  lockState = "UNLOCKED";

  // ── Servo: uncomment when motor is available ──
  // doorServo.write(SERVO_UNLOCKED);  // move servo to unlocked position
  // delay(500);                       // wait for servo to reach position

  // ── LED simulation (remove when motor is available) ──
  digitalWrite(LED_BUILTIN, HIGH);  // LED ON = UNLOCKED

  mqttClient.beginMessage(TOPIC_ACK);
  mqttClient.print("UNLOCKED (" + reason + ")");
  mqttClient.endMessage();
  Serial.println("UNLOCKED (" + reason + ")");
  publishStatus();

  // Start auto-lock timer
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
  digitalWrite(LED_BUILTIN, LOW);

  // ── Servo: uncomment when motor is available ──
  // doorServo.attach(SERVO_PIN);
  // doorServo.write(SERVO_LOCKED);  // start in locked position

  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { 
    delay(500); 
    Serial.print("."); 
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

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
  Serial.println("Arduino ready. Waiting for commands...");
  publishStatus();
}

void loop() { 
  mqttClient.poll();

  // Check auto-lock timer
  if (autolockPending && lockState == "UNLOCKED") {
    unsigned long elapsed = (millis() - unlockTime) / 1000;
    if (elapsed >= AUTOLOCK_SECONDS) {
      if (doorState == "CLOSED") {
        Serial.println("Auto-lock triggered!");
        doLock("AUTO_TIMER");
      } else {
        Serial.println("Door still open, waiting to close...");
        // Reset timer to check again in 1 second
        unlockTime = millis() - (AUTOLOCK_SECONDS - 1) * 1000;
      }
    }
  }
}

// When Motor Arrives Just 4 steps to do :
//1. Uncomment #include <Servo.h> at the top
//2. Uncomment doorServo lines in setup()
//3. Uncomment doorServo.write() lines in doLock() and doUnlock()
//4. Remove the LED lines