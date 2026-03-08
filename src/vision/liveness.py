import cv2
from deepface import DeepFace

# ML pretrained model to check if the image has a face
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def has_face(frame):
    # Returns True if a face is detected False otherwise
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)
    return len(faces) > 0

def check_liveness(frame):
    # Returns True if a real face is detected False if spoof or no face.
    try:
        faces = DeepFace.extract_faces(
            img_path=frame,
            enforce_detection=True,
            anti_spoofing=True
        )
        if not faces:
            return False
        return faces[0]["is_real"]
    except Exception as e:
        print("Liveness error:", e)
        return False