from deepface import DeepFace
import os
import pandas as pd

# --- CONFIG ---
DB_PATH = "allowed_people"
MODEL = "SFace"
BACKEND = "opencv"

def verify_user(frame):
    """
    Checks the frame against the 'allowed_people' folder.
    Returns: (is_match, name)
    """
    try:
        # DeepFace.find compares the live frame to the folder
        dfs = DeepFace.find(
            img_path = frame,
            db_path = DB_PATH,
            model_name = MODEL,
            detector_backend = BACKEND,
            distance_metric = "cosine",
            enforce_detection = False, # Liveness already checked, so skip strict check
            silent = True
        )
        
        # Check if we got a result
        if len(dfs) > 0 and not dfs[0].empty:
            # Get the path of the matching image
            full_path = dfs[0].iloc[0]['identity']
            
            # Extract just the name (e.g., "allowed_people/shakir.jpg" -> "shakir")
            name = os.path.basename(full_path).split('.')[0]
            
            return True, name
            
    except Exception as e:
        print(f"Face Rec Error: {e}")
        
    return False, "Unknown"