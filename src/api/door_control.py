import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883

def unlock_door() -> dict:
    try:
        client = mqtt.Client(client_id="webapp_unlock")
        client.connect(BROKER, PORT)
        client.publish("door/command", "UNLOCK")
        client.disconnect()
        return {
            'success': True,
            'message': 'Door unlocked via MQTT',
            'method': 'mqtt'
        }
    except Exception as e:
        print(f"MQTT unlock failed: {e}")
        return {
            'success': False,
            'message': str(e)
        }

def lock_door() -> dict:
    try:
        client = mqtt.Client(client_id="webapp_lock")
        client.connect(BROKER, PORT)
        client.publish("door/command", "LOCK")
        client.disconnect()
        return {
            'success': True,
            'message': 'Door locked via MQTT',
            'method': 'mqtt'
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }
