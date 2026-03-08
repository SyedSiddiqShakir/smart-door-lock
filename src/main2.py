import cv2
import time
import subprocess
import numpy as np
from vision import face_rec
from vision import liveness

class NativePiCamera:
    """
    """
    def __init__(self, width=1280, height=720, fps=30):
        self.width = width
        self.height = height
        #for the YUV420 frame 1.5x
        self.frame_bytes =  int(width * height * 1.5)
        
        cmd = [
                "rpicam-vid",             #Run Forever
                "-t", "0",
                "--width", str(width),
                "--height", str(height),
                "--framerate", str(fps),
                "--shutter", "30000",     #Low-Light ExposureTime
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

        yuv = np.frombuffer(raw, dtype=np.uint8).reshape((int(self.height * 1.5), self.width))
        bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
        return True, bgr
    def release(self):
        self.process.terminate()

#############
#MAIN LOOP
###########

print("Starting Camera")
cap = NativePiCamera(width=1280, height=720, fps=30)
time.sleep(2)

print("Press 'c' to check, 'q' to quit")

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: Camera disconnect or cannot be read")
            break

        #frame = cv2.resize(frame, (640, 480))
        frame = cv2.flip(frame, 1)
        cv2.imshow("Smart Lock Camera", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            print("\nProcessing frame...")

            if not liveness.has_face(frame):
                print("No Face Detected")
                continue

            is_real = liveness.check_liveness(frame)
            if not is_real:
                print("Spoof Detected")
                continue

            print("Real Face Detected")

            is_match, name = face_rec.verify_user(frame)
            if is_match:
                print(f"Access Granted: Welcome {name}")
            else:
                print("Access Denied")

        elif key == ord('q'):
            break

except KeyboardInterrupt:
    print("\nForce quitting")

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("System close")
