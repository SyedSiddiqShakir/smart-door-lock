import time
from deepface import DeepFace
import cv2

# --- CONFIG ---
# Replace these with actual filenames from your Kaggle dataset
img1_path = "../data/kaggle_ds/anushka_sharma/anushka_sharma_1.jpg" 
img2_path = "../data/kaggle_ds/anushka_sharma/anushka_sharma_2.jpg" # Same person, different photo

print("Starting SFace Verification on Pi 5...")

# --- 1. COLD START (Load Model) ---
start = time.time()

# We force the model to load first. 
# Note: "opencv" detector is critical for speed on Pi.
model = DeepFace.build_model("SFace") 

print(f"Model Loaded in {time.time() - start:.2f} seconds")

# --- 2. THE REAL TEST ---
start = time.time()

result = DeepFace.verify(
    img1_path = img1_path,
    img2_path = img2_path,
    model_name = "SFace",
    detector_backend = "opencv",  # ⚡ FASTEST backend for Pi
    distance_metric = "cosine"
)

end = time.time()

# --- 3. REPORT ---
print(f"\n--- RESULT ---")
print(f"Verified: {result['verified']}")
print(f"Distance: {result['distance']:.4f}")
print(f"Threshold: {result['threshold']}")
print(f"⏱️ Time Taken: {end - start:.4f} seconds")

if result['verified']:
    print("MATCH FOUND!")
else:
    print("NO MATCH")