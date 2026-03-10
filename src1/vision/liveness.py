"""
# face recognition system using DeepFace with the SFace model.
#
# 1. It loads all authorized users from the "authorized_faces"
#    directory, computes facial embeddings for each image,
#    and stores the mean embedding per person in a database.

#    Note: The images used for testing have **not been pushed**.
#    To test the system, add your own respective images in the
#    "authorized_faces" folder.
#
# 2. The verify_user(frame) function takes a camera frame,
#    extracts its facial embedding, compares it against the
#    stored embeddings using cosine distance, and returns:
#       - (True, person_name) if a match is found below the
#         defined distance threshold.
#       - (False, "Unknown") otherwise.
#
# The DISTANCE_THRESHOLD can be tuned to make recognition
# more or less strict.
"""

import os

#safety to avoid overflow of RAM
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import tensorflow as tf
try:
    gpus = tf.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
except:
    pass

import numpy as np
import cv2
from deepface import DeepFace

def check_liveness(frame):
    """
    Returns:
    True: If a real face is detected
    False: If a face fake is detected
    None: If no face is detected + Error
    """
    try:
        # Extract face with anti spoofing enabled
        face_result = DeepFace.extract_faces(
            img_path = frame,
            detector_backend = "opencv",
            enforce_detection = False,
            anti_spoofing = True
                )
        # Check Results
        if not face_result:
            return "No Face Detected"

        is_real = results[0].get("is_real", False)
        return is_real
        
    except Exception as e:
        print(f"Liveness Error: {e}")
        return None

