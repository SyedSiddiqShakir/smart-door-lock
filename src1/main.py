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
