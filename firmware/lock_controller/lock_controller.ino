#include <ArduinoMqttClient.h>
#include <WiFiS3.h> // specific for R4 WiFi
#include <Servo.h>

///////wifi connections
char ssid[] = "WIFI_NAME";        // <<<< WIFI NAME
char pass[] = "PASSWORD";    // <<<< WIFI PASSWORD

// MQTT Broker Settings
const char broker[] = "192.168.0.128";  // <<<< PI'S IP ADDRESS
int        port     = 1883;
const char topic[]  = "lock/command";

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);
Servo myservo;

void setup() {
  Serial.begin(9600);
  myservo.attach(9); // Connect Servo to Pin 9
  myservo.write(0);  // Start Locked

  // 1. Connect to WiFi
  Serial.print("Attempting to connect to WPA SSID: ");
  Serial.println(ssid);
  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    Serial.print(".");
    delay(5000);
  }
  Serial.println("Connected to WiFi!");

  // 2. Connect to MQTT Broker (The Pi)
  Serial.print("Attempting to connect to the MQTT broker: ");
  Serial.println(broker);

  if (!mqttClient.connect(broker, port)) {
    Serial.print("MQTT connection failed! Error code = ");
    Serial.println(mqttClient.connectError());
    while (1); // Halt if failed
  }

  Serial.println("You're connected to the MQTT broker!");

  // 3. Subscribe to the lock topic
  mqttClient.onMessage(onMqttMessage); // Set the function to run when message arrives
  mqttClient.subscribe(topic);
  Serial.print("Subscribing to topic: ");
  Serial.println(topic);
}

void loop() {
  // Keep the connection alive
  mqttClient.poll();
}

// This runs AUTOMATICALLY when a message arrives
void onMqttMessage(int messageSize) {
  // Read the message
  String message = "";
  while (mqttClient.available()) {
    message += (char)mqttClient.read();
  }

  Serial.print("Received: ");
  Serial.println(message);

  // Check command
  if (message == "OPEN") {
    Serial.println("Unlocking Door...");
    myservo.write(90);  // Unlock
    delay(5000);        // Wait 5 seconds
    myservo.write(0);   // Lock again
    Serial.println("Door Locked.");
  }
}