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

MODEL = "SFace"
DISTANCE_THRESHOLD = 0.5  # can be tuned
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT_DIR, "data", "authorized_faces")

# 
database = {}

for person_name in os.listdir(DB_PATH):
    person_path = os.path.join(DB_PATH, person_name)

    if not os.path.isdir(person_path):
        continue

    embeddings = []

    for file in os.listdir(person_path):
        if file.lower().endswith((".jpg", ".png", ".jpeg")):
            img_path = os.path.join(person_path, file)

            rep = DeepFace.represent(
                img_path=img_path,
                model_name=MODEL,
                enforce_detection=True
            )

            embeddings.append(rep[0]["embedding"])

    if embeddings:
        mean_embedding = np.mean(embeddings, axis=0)
        database[person_name] = mean_embedding
        print(f"Loaded {person_name} with {len(embeddings)} images")

def verify_user(frame):
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        rep = DeepFace.represent(
            img_path=rgb_frame,
            model_name=MODEL,
            enforce_detection=True
        )

        frame_embedding = rep[0]["embedding"]

        best_match = None
        lowest_distance = 1.0

        for person_name, db_embedding in database.items():

            cosine_distance = 1 - np.dot(db_embedding, frame_embedding) / (
                np.linalg.norm(db_embedding) * np.linalg.norm(frame_embedding)
            )

            print(f"{person_name} distance: {cosine_distance}")

            if cosine_distance < lowest_distance:
                lowest_distance = cosine_distance
                best_match = person_name

        if lowest_distance < DISTANCE_THRESHOLD:
            return True, best_match
        else:
            return False, "Unknown"

    except Exception as e:
        print(f"Face Rec Error: {e}")
        return False, "Unknown"
