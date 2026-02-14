
import cv2

# Load the pre-trained face detector (Standard OpenCV)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def has_face(frame):
    """
    Returns TRUE if a face is detected in the frame.
    Returns FALSE if empty.
    """
    # 1. Convert to Grayscale (Faster detection)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 2. Detect Faces
    # scaleFactor=1.1, minNeighbors=5 are standard settings
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)
    
    # 3. Check if list is empty
    if len(faces) > 0:
        return True # Face found!
    
    return False # No face