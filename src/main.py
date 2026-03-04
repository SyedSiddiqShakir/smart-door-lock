"""
HOW TO RUN THE SMART DOOR LOCK SYSTEM

1) Activate the virtual environment (smart-door-lock folder):
   source venv310/bin/activate

2) Navigate to the src folder
   cd project/smart-door-lock/src

3) Run the program:
   python main.py

IMPORTANT:
- The Smart Lock camera window MUST be the active (focused) window.
- Keep the terminal visible on a second screen or behind it.
- Keyboard input only works when the camera window is selected.
- Press:
    'c' → capture frame and run face recognition
    'q' → quit the program
- If the camera window is not focused, key presses will not be detected.
"""
import cv2
import time
import subprocess
import numpy as np
from vision import face_rec
from vision import liveness
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

# in src folder do: source venv310/bin/activate (to activate virtual environment) then run python src/main.py

class NativePiCamera:
    """
    Captures camera frames using rpicam-vid and returns BGR images.
    """
    def __init__(self, width=1280, height=720, fps=30):
        self.width = width
        self.height = height
        # For YUV420 frame 1.5x
        self.frame_bytes = int(width * height * 1.5)
        
        cmd = [
            "rpicam-vid",
            "-t", "0",                    
            "--width", str(width),
            "--height", str(height),
            "--framerate", str(fps),
            "--shutter", "30000",          
            "--gain", "4.0",
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

        # Zoom out by resizing frame, (adjust factor (0.4) as needed)
        bgr = cv2.resize(bgr, (int(self.width*0.4), int(self.height*0.4)))
        return True, bgr

    def release(self):
        self.process.terminate()

# MAIN LOOP

print("Starting Camera...")
cap = NativePiCamera(width=1280, height=720, fps=30)
time.sleep(2)

print("Press 'c' to check face, 'q' to quit.")

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: Camera disconnected or cannot be read")
            break

        # Flip horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        cv2.imshow("Smart Lock Camera", frame)

        # Wait for user input
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            print("\nProcessing frame...")

            # Face detection
            if not liveness.has_face(frame):
                print("No face detected")
                continue

            # Liveness check
            is_real = liveness.check_liveness(frame)
            if not is_real:
                print("Spoof detected - Access denied")
                continue

            print("Real face detected")

            # Face recognition
            is_match, name = face_rec.verify_user(frame)
            if is_match:
                print(f"ACCESS GRANTED: Welcome {name}!")
                # TODO: trigger door open mechanism
            else:
                print("ACCESS DENIED: Unknown face")
                # TODO: log attempt, alert

        elif key == ord('q'):
            break

except KeyboardInterrupt:
    print("\nForce quitting...")

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("System closed")

    """
    """
 #version on Pi 04/03   
"""
import cv2
import time
import subprocess
import numpy as np
from vision import face_rec
from vision import liveness
import os
import paho.mqtt.client as mqtt 
os.environ["QT_QPA_PLATFORM"] = "xcb"

# MQTT Setup 
BROKER = "localhost"
PORT = 1883
TOPIC_COMMAND = "door/command"

mqtt_client = mqtt.Client(client_id="pi_main")
mqtt_client.connect(BROKER, PORT)
mqtt_client.loop_start()
print("MQTT connected to broker.")


failed_attempts = 0
MAX_ATTEMPTS = 10
ui_label_text = "READY"
ui_label_color = (255, 255, 255)  # white
ui_reset_time = 0


# in src folder do: source venv310/bin/activate (to activate virtual environment) then run python src/main.py

class NativePiCamera:
    
   # Captures camera frames using rpicam-vid and returns BGR images.
    
    def __init__(self, width=1280, height=720, fps=30):
        self.width = width
        self.height = height
        # For YUV420 frame 1.5x
        self.frame_bytes = int(width * height * 1.5)
        
        cmd = [
            "rpicam-vid",
            "-t", "0",                    
            "--width", str(width),
            "--height", str(height),
            "--framerate", str(fps),
            "--shutter", "30000",          
            "--gain", "4.0",
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

        # Zoom out by resizing frame, (adjust factor (0.4) as needed)
        bgr = cv2.resize(bgr, (int(self.width*0.4), int(self.height*0.4)))
        return True, bgr

    def release(self):
        self.process.terminate()

# MAIN LOOP

def render_status_overlay(img, label, color):
    overlay_img = img.copy()

    # Top bar
    cv2.rectangle(overlay_img, (0, 0), (img.shape[1], 70), color, -1)

    # Transparency
    blended = cv2.addWeighted(overlay_img, 0.6, img, 0.4, 0)

    # Text
    cv2.putText(blended, label, (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (255, 255, 255), 2, cv2.LINE_AA)

    return blended

print("Starting Camera...")
cap = NativePiCamera(width=1280, height=720, fps=30)
time.sleep(2)

print("Press 'c' to check face, 'q' to quit.")

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: Camera disconnected or cannot be read")
            break

        # Flip horizontally for mirror effect
        frame = cv2.flip(frame, 1)

        # ✅ Create clean frame BEFORE UI
        clean_frame = frame.copy()

        # Auto reset UI after 2 seconds
        if ui_reset_time != 0 and (time.time() - ui_reset_time > 2):
            ui_label_text = "READY"
            ui_label_color = (255, 255, 255)
            ui_reset_time = 0

        # UI only for display
        display_frame = render_status_overlay(frame, ui_label_text, ui_label_color)
        cv2.imshow("Smart Lock Camera", display_frame)

        # Wait for user input
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            print("\nProcessing frame...")
            ui_label_text = "PROCESSING..."
            ui_label_color = (255, 0, 0)  # Blue

            # Face detection
            if not liveness.has_face(clean_frame):
                print("No face detected")

                ui_label_text = "NO FACE DETECTED"
                ui_label_color = (0, 165, 255)  # Orange
                ui_reset_time = time.time()

                continue

            # Liveness check
            is_real = liveness.check_liveness(clean_frame)
            if not is_real:
                print("Spoof detected - Access denied")
                failed_attempts += 1
                print(f"Failed attempts: {failed_attempts}")

                ui_label_text = "ACCESS DENIED"
                ui_label_color = (0, 0, 255)
                ui_reset_time = time.time()
                continue

            print("Real face detected")
            ###

            # Face recognition
            is_match, name = face_rec.verify_user(clean_frame)
            if is_match:
                print(f"ACCESS GRANTED: Welcome {name}!")
                failed_attempts = 0

                ui_label_text = f"WELCOME {name}"
                ui_label_color = (0, 255, 0)
                ui_reset_time = time.time()
                
                # SEND UNLOCK TO ARDUINO 
                mqtt_client.publish(TOPIC_COMMAND, "UNLOCK")
                print("MQTT: UNLOCK sent to Arduino")
                # important: arduino handles auto-lock timer automatically no need to do it here
                
                
            else:
                print("ACCESS DENIED: Unknown face")
                failed_attempts += 1
                print(f"Failed attempts: {failed_attempts}")

                ui_label_text = "ACCESS DENIED"
                ui_label_color = (0, 0, 255)
                ui_reset_time = time.time()
                # TODO: log attempt, alert
                
                if failed_attempts >= MAX_ATTEMPTS:
                    ui_label_text = "VOICE AUTH REQUIRED"
                    ui_label_color = (0, 0, 255)

                    temp_frame = render_status_overlay(frame, ui_label_text, ui_label_color)
                    cv2.imshow("Smart Lock Camera", temp_frame)
                    cv2.waitKey(1500)

                    print("\nToo many failed attempts! Switching to voice authentication...\n")

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

    """
