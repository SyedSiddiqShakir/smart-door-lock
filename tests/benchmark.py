import time
import pandas as pd
from deepface import DeepFace
import os


img_folder = "benchmark_images"
anchor_img = os.path.join(img_folder, "anchor.jpg")    # Reference Photo of You
positive_img = os.path.join(img_folder, "positive.jpg") # You (different lighting/angle)
negative_img = os.path.join(img_folder, "negative.jpg") # Someone else

# Check if files exist before running
if not os.path.exists(anchor_img) or not os.path.exists(positive_img) or not os.path.exists(negative_img):
    print(f"hmm... something is missing")
    exit()

models_to_test = [
    "VGG-Face", 
    "Facenet", 
    "Facenet512", 
    "ArcFace", 
    "SFace"
]

results = []

print("\nStarting Benchmark...\n")

for model in models_to_test:
    print(f"Testing {model}...")
    
    try:
        # me vs me : True
        start_time = time.time()
        res_pos = DeepFace.verify(img1_path=anchor_img, img2_path=positive_img, model_name=model, enforce_detection=False)
        end_time = time.time()
        time_pos = end_time - start_time
        
        # Me vs not Me : False
        start_time = time.time()
        res_neg = DeepFace.verify(img1_path=anchor_img, img2_path=negative_img, model_name=model, enforce_detection=False)
        end_time = time.time()
        time_neg = end_time - start_time
        
        # Average Speed
        avg_time = (time_pos + time_neg) / 2
        
        # Accuracy Check
        passed = "Pass" if (res_pos['verified'] == True and res_neg['verified'] == False) else "Fail"

        results.append({
            "Model": model,
            "Avg Time (s)": round(avg_time, 4),
            "Result": passed,
            "Pos Dist (Low=Good)": round(res_pos['distance'], 4),
            "Neg Dist (High=Good)": round(res_neg['distance'], 4),
            "Threshold": res_pos['threshold']
        })

    except Exception as e:
        print(f"Model {model} failed: {e}")


df = pd.DataFrame(results)
print("\nBENCHMARK RESULTS")
print(df.to_string(index=False))

# Pick the winner
if not df.empty:
    fastest = df.sort_values(by="Avg Time (s)").iloc[0]
    print(f"\nFastest Model for Pi: {fastest['Model']} ({fastest['Avg Time (s)']}s)")