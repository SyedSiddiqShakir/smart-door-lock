import paho.mqtt.client as mqtt

# --- CONFIG ---
BROKER = "localhost"
TOPIC = "lock/command"

client = None

def start_mqtt():
    """Connects to the Mosquitto Broker"""
    global client
    try:
        client = mqtt.Client("Pi_SmartLock_Module")
        client.connect(BROKER)
        client.loop_start() # Runs in background
        print(f"MQTT Connected to {BROKER}")
    except Exception as e:
        print(f"MQTT Connection Failed: {e}")

def send_open():
    """Tells Arduino to UNLOCK"""
    if client:
        print("[MQTT] Sending OPEN command...")
        client.publish(TOPIC, "OPEN")

def send_denied():
    """Tells Arduino to show RED X"""
    if client:
        print("[MQTT] Sending DENIED command...")
        client.publish(TOPIC, "DENIED")