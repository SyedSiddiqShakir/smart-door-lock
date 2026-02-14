import cv2
import time
import os

# --- IMPORT OUR MODULES ---
import comms.mqtt as mqtt
import vision.liveness as liveness
import vision.face_rec as face_rec

# --- SETUP ---
# Create the folder if it doesn't exist
if not os.path.exists("allowed_people"):
    os.makedirs("allowed_people")
    print("Created 'allowed_people' folder. Please put your photo inside!")

# Initialize MQTT
mqtt.start_mqtt()

# Start Camera
cap = cv2.VideoCapture(0)
cap.set(3, 640) # Width
cap.set(4, 480) # Height

# --- COOLDOWN LOGIC ---
last_attempt_time = 0
COOLDOWN = 5 # Seconds between scans

print("SYSTEM READY. WAITING FOR FACES...")

try:
    while True:
        ret, frame = cap.read()
        if not ret: break

        # Show live feed
        cv2.imshow("Smart Lock", frame)
        
        # Check current time
        current_time = time.time()

        # Only run AI if cooldown is over
        if (current_time - last_attempt_time) > COOLDOWN:
            
            # STEP 1: LIVENESS (Fast Check)
            if liveness.has_face(frame):
                print("Face Detected! Verifying...")
                
                # STEP 2: RECOGNITION (Heavy Check)
                is_match, name = face_rec.verify_user(frame)
                
                if is_match:
                    print(f"ACCESS GRANTED: Welcome {name}!")
                    mqtt.send_open()
                else:
                    print("ACCESS DENIED: Unknown Face")
                    mqtt.send_denied()
                
                # Reset Timer
                last_attempt_time = time.time()

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    cap.release()
    cv2.destroyAllWindows()