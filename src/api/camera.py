"""
Camera module for handling video feed and face capture
Interfaces with Raspberry Pi Camera or USB webcam
"""

import cv2
import os
from datetime import datetime
from typing import Optional

# Global camera object (shared across requests)
camera = None

def init_camera():
    """Initialize camera object"""
    global camera
    if camera is None:
        # Try Pi Camera first, fallback to USB webcam
        try:
            camera = cv2.VideoCapture(0)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_FPS, 15)  # Low FPS to save resources
            print("✓ Camera initialized")
        except Exception as e:
            print(f"✗ Camera initialization failed: {e}")
            camera = None
    return camera

def get_camera_snapshot() -> Optional[bytes]:
    """
    Capture current frame from camera and return as JPEG bytes
    Returns: JPEG image bytes or None if camera unavailable
    """
    cam = init_camera()
    
    if cam is None or not cam.isOpened():
        return None
    
    # Read frame
    ret, frame = cam.read()
    
    if not ret:
        return None
    
    # Encode as JPEG (90% quality to save bandwidth)
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buffer.tobytes()

def capture_face_for_training(person_name: str) -> dict:
    """
    Capture current camera frame and save to authorized_faces folder
    
    Args:
        person_name: Name of the person to save
        
    Returns:
        Dictionary with success status and file path
    """
    cam = init_camera()
    
    if cam is None or not cam.isOpened():
        return {
            'success': False,
            'error': 'Camera not available'
        }
    
    # Read frame
    ret, frame = cam.read()
    
    if not ret:
        return {
            'success': False,
            'error': 'Failed to capture frame'
        }
    
    # Create directory if doesn't exist
    save_dir = os.path.join(os.path.dirname(__file__), '../../data/authorized_faces')
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{person_name.replace(' ', '_')}_{timestamp}.jpg"
    filepath = os.path.join(save_dir, filename)
    
    # Save image
    cv2.imwrite(filepath, frame)
    
    return {
        'success': True,
        'message': f'Face captured for {person_name}',
        'filepath': filepath,
        'filename': filename
    }

def get_current_frame():
    """
    Get current camera frame as numpy array
    Used by main.py for face recognition
    """
    cam = init_camera()
    
    if cam is None or not cam.isOpened():
        return None
    
    ret, frame = cam.read()
    
    if ret:
        return frame
    return None

def release_camera():
    """Release camera resources"""
    global camera
    if camera is not None:
        camera.release()
        camera = None
        print("✓ Camera released")

if __name__ == '__main__':
    # Test camera
    print("Testing camera...")
    frame_bytes = get_camera_snapshot()
    
    if frame_bytes:
        print(f"✓ Camera working! Captured {len(frame_bytes)} bytes")
    else:
        print("✗ Camera test failed")
    
    release_camera()