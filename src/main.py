"""
HOW TO RUN THE SMART DOOR LOCK SYSTEM

1) Activate the virtual environment (smart-door-lock folder):
cd project/smart-door-lock/
source venv310/bin/activate
cd src 
python main.py
   

IMPORTANT:
- The Smart Lock camera window MUST be the active (focused) window.
- Keep the terminal visible on a second screen or behind it.
- Keyboard input only works when the camera window is selected.
- Press:
    'c' → manually capture frame and run face recognition
    'q' → quit the program
- System also activates AUTOMATICALLY when sound is detected by mic
"""
import cv2
import time
import subprocess
import numpy as np
from vision import face_rec
from vision import liveness
import os
import sys
import threading 
import paho.mqtt.client as mqtt
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.api.database import log_access
os.environ["QT_QPA_PLATFORM"] = "xcb"

# ── MQTT Setup ──
BROKER = "localhost"
PORT = 1883
TOPIC_COMMAND  = "door/command"
TOPIC_ACTIVATE = "door/activate"  # ← listen for mic trigger from Arduino

# ── Activation flag ──
activate_requested = False  # set to True when Arduino sends ACTIVATE

# ── Sound detection flag ──
sound_detected_time = 0

def on_mqtt_message(client, userdata, msg):
    global activate_requested, sound_detected_time
    print(f"MQTT message received: topic={msg.topic} payload={msg.payload.decode()}") 
    payload = msg.payload.decode().strip().upper()
    if msg.topic == TOPIC_ACTIVATE and payload == "ACTIVATE":
        print("MQTT: ACTIVATE received from Arduino!")
        activate_requested = True
        sound_detected_time = time.time()
        with open("/tmp/last_sound.txt", "w") as f:
            f.write(str(sound_detected_time))

mqtt_client = mqtt.Client(client_id="pi_main")
mqtt_client.on_message = on_mqtt_message
mqtt_client.connect(BROKER, PORT)
mqtt_client.subscribe(TOPIC_ACTIVATE)  # ← subscribe to activation topic
mqtt_client.loop_start()
print("MQTT connected to broker.")

failed_attempts = 0
MAX_ATTEMPTS = 10
ui_label_text = "READY"
ui_label_color = (255, 255, 255)
ui_reset_time = 0


class NativePiCamera:
    """
    Captures camera frames using rpicam-vid and returns BGR images.
    """
    def __init__(self, width=1280, height=720, fps=30):
        self.width = width
        self.height = height
        self.frame_bytes = int(width * height * 1.5)
        
        cmd = [
            "rpicam-vid",
            "-t", "0",                    
            "--width", str(width),
            "--height", str(height),
            "--framerate", str(fps),
            "--shutter", "20000",          
            "--gain", "2.0",
            "--awb", "auto",
            "--codec", "yuv420",
            "--flush",
            "-o", "-"
        ]
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    def read(self):
        raw = self.process.stdout.read(self.frame_bytes)
        if len(raw) != self.frame_bytes:
            return False, None
        yuv = np.frombuffer(raw, dtype=np.uint8).reshape((int(self.height*1.5), self.width))
        bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
        bgr = cv2.resize(bgr, (int(self.width*0.4), int(self.height*0.4)))
        return True, bgr

    def release(self):
        self.process.terminate()


def render_status_overlay(img, label, color):
    overlay_img = img.copy()
    cv2.rectangle(overlay_img, (0, 0), (img.shape[1], 70), color, -1)
    blended = cv2.addWeighted(overlay_img, 0.6, img, 0.4, 0)
    cv2.putText(blended, label, (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (255, 255, 255), 2, cv2.LINE_AA)
    return blended
    
def write_ui_status(text):
    with open("/tmp/ui_status.txt", "w") as f:
        f.write(text)


def process_face(clean_frame, frame):
    """Run face detection, liveness check and recognition."""
    global failed_attempts, ui_label_text, ui_label_color, ui_reset_time

    print("\nProcessing frame...")
    ui_label_text = "PROCESSING..."
    write_ui_status("PROCESSING...")
    ui_label_color = (255, 0, 0)

    # Face detection
    if not liveness.has_face(clean_frame):
        print("No face detected")
        ui_label_text = "NO FACE DETECTED"
        write_ui_status("NO FACE DETECTED")
        ui_label_color = (0, 165, 255)
        ui_reset_time = time.time()
        return

    # Liveness check
    is_real = liveness.check_liveness(clean_frame)
    if not is_real:
        print("Spoof detected - Access denied")
        failed_attempts += 1
        print(f"Failed attempts: {failed_attempts}")
        ui_label_text = "ACCESS DENIED"
        write_ui_status("ACCESS DENIED - Spoof detected")
        ui_label_color = (0, 0, 255)
        ui_reset_time = time.time()
        threading.Thread(target=log_access, args=("Spoof Attempt", "denied", None, 0.0)).start()
        return

    print("Real face detected")

    # Face recognition
    is_match, name = face_rec.verify_user(clean_frame)
    if is_match:
        print(f"ACCESS GRANTED: Welcome {name}!")
        failed_attempts = 0
        ui_label_text = f"WELCOME {name}"
        write_ui_status(f"WELCOME {name}")
        ui_label_color = (0, 255, 0)
        ui_reset_time = time.time()
        
        threading.Thread(target=log_access, args=(name, "entry", None, 1.0)).start()

        # ── SEND UNLOCK TO ARDUINO ──
        mqtt_client.publish(TOPIC_COMMAND, "UNLOCK")
        with open("/tmp/lock_status.txt", "w") as f:
            f.write(str(time.time()))
        print("MQTT: UNLOCK sent to Arduino")
        # Arduino handles auto-lock timer automatically
        

    else:
        print("ACCESS DENIED: Unknown face")
        failed_attempts += 1
        print(f"Failed attempts: {failed_attempts}")
        ui_label_text = "ACCESS DENIED"
        write_ui_status("ACCESS DENIED")
        ui_label_color = (0, 0, 255)
        ui_reset_time = time.time()
        
        threading.Thread(target=log_access, args=("Unknown", "denied", None, 0.0)).start()

        if failed_attempts >= MAX_ATTEMPTS:
            ui_label_text = "VOICE AUTH REQUIRED"
            ui_label_color = (0, 0, 255)
            temp_frame = render_status_overlay(frame, ui_label_text, ui_label_color)
            cv2.imshow("Smart Lock Camera", temp_frame)
            cv2.waitKey(1500)
            print("\nToo many failed attempts! Switching to voice authentication...\n")
            return "voice_auth"
    


print("Starting Camera...")
cap = NativePiCamera(width=1280, height=720, fps=30)
time.sleep(2)
print("System ready! Waiting for sound or press 'c' to activate manually.")

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: Camera disconnected or cannot be read")
            break

        frame = cv2.flip(frame, 1)
        cv2.imwrite("/tmp/latest_frame_tmp.jpg", frame)
        os.rename("/tmp/latest_frame_tmp.jpg", "/tmp/latest_frame.jpg")
        clean_frame = frame.copy()

        # Auto reset UI after 2 seconds
        if ui_reset_time != 0 and (time.time() - ui_reset_time > 2):
            ui_label_text = "READY"
            ui_label_color = (255, 255, 255)
            ui_reset_time = 0
            write_ui_status("WAITING")

        # ── Check if Arduino sent ACTIVATE ──
        if activate_requested:
            activate_requested = False  # reset flag
            ui_label_text = "SOUND DETECTED!"
            ui_label_color = (255, 165, 0)  # Orange
            result = process_face(clean_frame, frame)
            if result == "voice_auth":
                cap.release()
                cv2.destroyAllWindows()
                subprocess.run(["python", "test.py"])
                break

        display_frame = render_status_overlay(frame, ui_label_text, ui_label_color)
        cv2.imshow("Smart Lock Camera", display_frame)

        key = cv2.waitKey(1) & 0xFF

        # ── Manual trigger with 'c' ──
        if key == ord('c'):
            result = process_face(clean_frame, frame)
            if result == "voice_auth":
                cap.release()
                cv2.destroyAllWindows()
                subprocess.run(["python", "test.py"])
                break

        elif key == ord('q'):
            break

except KeyboardInterrupt:
    print("\nForce quitting...")

finally:
    cap.release()
    cv2.destroyAllWindows()
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("System closed")
