import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from deepface import DeepFace

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================

# Folder containing your images
IMG_FOLDER = "benchmark_images"
ANCHOR_IMG = os.path.join(IMG_FOLDER, "anchor.jpg") # Reference photo of YOU

# Models to test
MODELS = ["VGG-Face", "Facenet", "Facenet512", "ArcFace", "SFace"]

# Metrics storage
results = []

print(f"STARTING EXTENDED BENCHMARK (15+ Images)...")
print(f"Reading images from: {IMG_FOLDER}")

# ==========================================
# 2. THE TESTING LOOP
# ==========================================

for model in MODELS:
    print(f"\n--- Testing Model: {model} ---")
    
    # A. Test the 15 numbered images
    for i in range(1, 16): 
        filename = f"{i}.jpg"
        filepath = os.path.join(IMG_FOLDER, filename)
        
        # Skip if file doesn't exist
        if not os.path.exists(filepath):
            continue
            
        try:
            start_time = time.time()
            # Enforce detection=False allows it to run even if face is blurry
            obj = DeepFace.verify(ANCHOR_IMG, filepath, model_name=model, enforce_detection=False)
            end_time = time.time()
            
            # Distance: Lower is better (0.0 = exact match)
            # Threshold: The limit for "Yes/No"
            # Confidence Margin: (Threshold - Distance). Positive = Good Match. Negative = Failure.
            margin = obj['threshold'] - obj['distance']
            
            results.append({
                "Model": model,
                "Image Type": "Positive (You)",
                "Filename": filename,
                "Time (s)": round(end_time - start_time, 3),
                "Distance": obj['distance'],
                "Threshold": obj['threshold'],
                "Confidence Margin": margin, 
                "Verified": obj['verified']
            })
            
        except Exception as e:
            print(f"Error with {filename}: {e}")

    # B. Test the Negative Image (Stranger) - Just to make sure it still locks
    neg_path = os.path.join(IMG_FOLDER, "negative.jpg")
    if os.path.exists(neg_path):
        start_time = time.time()
        obj = DeepFace.verify(ANCHOR_IMG, neg_path, model_name=model, enforce_detection=False)
        end_time = time.time()
        
        # For negatives, we WANT the distance to be HIGHER than threshold.
        # So "Success Margin" = Distance - Threshold
        margin = obj['distance'] - obj['threshold']
        
        results.append({
            "Model": model,
            "Image Type": "Negative (Stranger)",
            "Filename": "negative.jpg",
            "Time (s)": round(end_time - start_time, 3),
            "Distance": obj['distance'],
            "Threshold": obj['threshold'],
            "Confidence Margin": margin,
            "Verified": obj['verified'] # Should be False
        })

# ==========================================
# 3. GENERATE DATAFRAME & REPORT
# ==========================================
df = pd.DataFrame(results)

# Filter for only "Positive" images for the main analysis
df_pos = df[df["Image Type"] == "Positive (You)"]

print("\n--- FINAL REPORT SUMMARY ---")
# Group by Model to see averages
summary = df_pos.groupby("Model").agg({
    "Time (s)": "mean",
    "Confidence Margin": "mean",
    "Verified": "mean" # 1.0 = 100% Accuracy
}).sort_values(by="Time (s)")

print(summary)

# ==========================================
# 4. VISUALIZATION (PLOTS)
# ==========================================
sns.set_theme(style="whitegrid")
plt.figure(figsize=(18, 10))

# --- PLOT 1: INFERENCE SPEED (Bar Chart) ---
plt.subplot(2, 2, 1)
sns.barplot(data=df_pos, x="Model", y="Time (s)", errorbar="sd", palette="viridis")
plt.title("Inference Speed (Lower is Better)", fontsize=14, fontweight='bold')
plt.ylabel("Time (seconds)")
plt.xlabel("")

# --- PLOT 2: CONFIDENCE MARGIN (Box Plot) ---
# Shows how "sure" the model is. Higher is better.
# If box is below 0 line, the model failed to recognize you.
plt.subplot(2, 2, 2)
sns.boxplot(data=df_pos, x="Model", y="Confidence Margin", palette="coolwarm")
plt.axhline(0, color='red', linestyle='--', linewidth=2, label="Failure Line")
plt.title("Model Confidence (Higher is Better)", fontsize=14, fontweight='bold')
plt.ylabel("Margin (Threshold - Distance)")
plt.legend()
plt.xlabel("")

# --- PLOT 3: DISTANCE STABILITY (Line/Strip Plot) ---
# Shows if the model is consistent across images 1-15
plt.subplot(2, 1, 2)
sns.lineplot(data=df_pos, x="Filename", y="Distance", hue="Model", marker="o")
plt.title("Distance Score across 15 Images (Lower is Better)", fontsize=14, fontweight='bold')
plt.ylabel("Distance")
plt.xticks(rotation=45)
plt.grid(True)

plt.tight_layout()
plt.show()

# --- PLOT 4: THE TRADE-OFF (Speed vs Accuracy) ---
plt.figure(figsize=(8, 6))
sns.scatterplot(data=summary, x="Time (s)", y="Confidence Margin", hue="Model", s=200, palette="deep")
plt.title("The Trade-Off: Speed vs. Confidence", fontsize=14, fontweight='bold')
plt.xlabel("Average Time (seconds) <-- Faster")
plt.ylabel("Average Confidence Margin <-- More Accurate")
for i in range(summary.shape[0]):
    plt.text(summary["Time (s)"].iloc[i]+0.02, summary["Confidence Margin"].iloc[i], 
             summary.index[i], fontsize=11, fontweight='bold')
plt.grid(True)
plt.show()