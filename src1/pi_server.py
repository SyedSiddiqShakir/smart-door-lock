import json
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883

TOPIC_COMMAND = "door/command"
TOPIC_SENSOR = "door/sensor"
TOPIC_ACK = "door/ack"
TOPIC_STATUS = "door/status"

def on_message(client, userdata, msg):
    payload = msg.payload.decode(errors="ignore")
    if msg.topic == TOPIC_ACK:
        print("✅ ACK:", payload)
    elif msg.topic == TOPIC_STATUS:
        try:
            data = json.loads(payload)
            print(f"📡 STATUS: lock={data.get('lock_state')} door={data.get('door_state')} ts={data.get('ts')}")
        except Exception:
            print("📡 STATUS raw:", payload)

client = mqtt.Client(client_id="pi_server_sim")
client.on_message = on_message
client.connect(BROKER, PORT)

client.subscribe(TOPIC_ACK, qos=1)
client.subscribe(TOPIC_STATUS, qos=1)
client.loop_start()

print("Pi server running.")
print("Commands:")
print("  unlock  -> send UNLOCK")
print("  lock    -> send LOCK")
print("  open    -> door sensor OPEN")
print("  close   -> door sensor CLOSED")
print("  exit    -> quit")

while True:
    cmd = input("> ").strip().lower()

    if cmd == "exit":
        break
    elif cmd == "unlock":
        client.publish(TOPIC_COMMAND, "UNLOCK", qos=1)
        print("➡️ Sent: UNLOCK")
    elif cmd == "lock":
        client.publish(TOPIC_COMMAND, "LOCK", qos=1)
        print("➡️ Sent: LOCK")
    elif cmd == "open":
        client.publish(TOPIC_SENSOR, "OPEN", qos=1, retain=True)
        print("🚪 Sensor: OPEN")
    elif cmd == "close":
        client.publish(TOPIC_SENSOR, "CLOSED", qos=1, retain=True)
        print("🚪 Sensor: CLOSED")
    else:
        print("Use: unlock | lock | open | close | exit")

client.loop_stop()
client.disconnect()
print("Stopped.")