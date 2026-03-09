import json
import time
import threading
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883

TOPIC_COMMAND = "door/command"
TOPIC_ACK = "door/ack"
TOPIC_STATUS = "door/status"
TOPIC_SENSOR = "door/sensor"     # OPEN / CLOSED updates from “sensor”

lock_state = "LOCKED"            # LOCKED / UNLOCKED
door_state = "CLOSED"            # OPEN / CLOSED

AUTOLOCK_SECONDS = 10            # change to whatever you want

autolock_timer = None
timer_lock = threading.Lock()

def publish_status(client):
    payload = {
        "lock_state": lock_state,
        "door_state": door_state,
        "ts": int(time.time())
    }
    client.publish(TOPIC_STATUS, json.dumps(payload), qos=1, retain=True)

def cancel_autolock():
    global autolock_timer
    with timer_lock:
        if autolock_timer is not None:
            autolock_timer.cancel()
            autolock_timer = None

def schedule_autolock(client):
    """
    Auto-lock ONLY when door is CLOSED.
    If door is OPEN, we will NOT lock yet.
    We wait until we receive door CLOSED event to lock.
    """
    global autolock_timer

    cancel_autolock()

    def autolock_action():
        global lock_state
        # Check door state at the moment of autolock
        if door_state == "CLOSED" and lock_state == "UNLOCKED":
            lock_state = "LOCKED"
            client.publish(TOPIC_ACK, "LOCKED (AUTO)", qos=1)
            print("🔒 AUTO-LOCK executed (door is CLOSED).")
            publish_status(client)
        else:
            # Door still open → do nothing
            print("⏸️ AUTO-LOCK skipped (door is OPEN). Waiting for door to close...")

    with timer_lock:
        autolock_timer = threading.Timer(AUTOLOCK_SECONDS, autolock_action)
        autolock_timer.start()
        print(f"⏱️ Auto-lock scheduled in {AUTOLOCK_SECONDS}s (only if door is CLOSED).")

def do_lock(client, reason="MANUAL"):
    global lock_state
    cancel_autolock()
    if lock_state != "LOCKED":
        time.sleep(1)  # simulate servo movement
        lock_state = "LOCKED"
    client.publish(TOPIC_ACK, f"LOCKED ({reason})", qos=1)
    print("ACK sent:", f"LOCKED ({reason})")
    publish_status(client)

def do_unlock(client, reason="MANUAL"):
    global lock_state
    if lock_state != "UNLOCKED":
        time.sleep(1)  # simulate servo movement
        lock_state = "UNLOCKED"
    client.publish(TOPIC_ACK, f"UNLOCKED ({reason})", qos=1)
    print("ACK sent:", f"UNLOCKED ({reason})")
    publish_status(client)
    schedule_autolock(client)

def on_message(client, userdata, msg):
    global door_state

    topic = msg.topic
    payload = msg.payload.decode().strip().upper()

    if topic == TOPIC_COMMAND:
        if payload not in ["LOCK", "UNLOCK"]:
            print("Unknown command:", payload)
            return

        print("➡️ Command received:", payload)

        if payload == "UNLOCK":
            do_unlock(client, reason="COMMAND")
        else:
            do_lock(client, reason="COMMAND")

    elif topic == TOPIC_SENSOR:
        if payload not in ["OPEN", "CLOSED"]:
            print("Unknown sensor state:", payload)
            return

        door_state = payload
        print("🚪 Door sensor:", door_state)
        publish_status(client)

        # If door just closed AND we are unlocked → lock immediately (realistic)
        if door_state == "CLOSED" and lock_state == "UNLOCKED":
            # If the timer already fired and skipped, this will enforce lock now.
            do_lock(client, reason="AUTO_AFTER_CLOSE")

client = mqtt.Client(client_id="arduino_client_sim")
client.on_message = on_message
client.connect(BROKER, PORT)

client.subscribe(TOPIC_COMMAND, qos=1)
client.subscribe(TOPIC_SENSOR, qos=1)

print("Arduino client running...")
print("Waiting for commands on:", TOPIC_COMMAND)
print("Waiting for door sensor on:", TOPIC_SENSOR)

publish_status(client)
client.loop_forever()