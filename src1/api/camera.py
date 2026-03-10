"""
Camera module for handling video feed and face capture
Interfaces with Raspberry Pi Camera (rpicam-vid) or USB webcam (PC fallback)
"""

import cv2
import os
import subprocess
import numpy as np
from datetime import datetime
from typing import Optional

class NativePiCamera:
    """
    Pi: captures frames via rpicam-vid subprocess (YUV420 → BGR)
    PC: captures frames via cv2.VideoCapture (webcam fallback)
    """

    def __init__(self, width: int = 640, height: int = 480, fps: int = 15):
        self.width = width
        self.height = height
        self.is_pi = self._is_raspberry_pi()
        self._cap = None
        self._process = None

        if self.is_pi:
            self.frame_bytes = int(width * height * 1.5)
            cmd = [
                "rpicam-vid",
                "-t", "0",
                "--width", str(width),
                "--height", str(height),
                "--framerate", str(fps),
                "--shutter", "30000",
                "--gain", "4.0",
                "--awb", "auto",
                "--codec", "yuv420",
                "--flush",
                "-o", "-"
            ]
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            print("✓ Pi Camera initialized via rpicam-vid")
        else:
            self._cap = cv2.VideoCapture(0)
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self._cap.set(cv2.CAP_PROP_FPS, fps)
            print("⚠ PC mode — using webcam fallback")

    def is_opened(self) -> bool:
        if self.is_pi:
            return self._process is not None and self._process.poll() is None
        return self._cap is not None and self._cap.isOpened()

    def read(self) -> tuple:
        if self.is_pi:
            raw = self._process.stdout.read(self.frame_bytes)
            if len(raw) != self.frame_bytes:
                return False, None
            yuv = np.frombuffer(raw, dtype=np.uint8).reshape(
                (int(self.height * 1.5), self.width)
            )
            bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
            return True, bgr
        return self._cap.read()

    def release(self):
        if self.is_pi and self._process:
            self._process.terminate()
            self._process = None
        elif self._cap:
            self._cap.release()
            self._cap = None
    
    @staticmethod
    def _is_raspberry_pi() -> bool:
        try:
            with open('/proc/device-tree/model', 'r') as f:
                return 'Raspberry Pi' in f.read()
        except:
            return False


# Global camera instance (shared across requests)
_camera: Optional[NativePiCamera] = None


def init_camera() -> Optional[NativePiCamera]:
    """Initialize the global camera instance"""
    global _camera
    if _camera is None or not _camera.is_opened():
        try:
            _camera = NativePiCamera(width=640, height=480, fps=15)
            print("✓ Camera initialized")
        except Exception as e:
            print(f"✗ Camera initialization failed: {e}")
            _camera = None
    return _camera


def get_camera_snapshot() -> Optional[bytes]:
    try:
        with open("/tmp/latest_frame.jpg", "rb") as f:
            return f.read()
    except:
        return None


def capture_face_for_training(person_name: str) -> dict:
    """
    Capture current frame and save to authorized_faces folder.

    Args:
        person_name: Name of the person to save

    Returns:
        Dictionary with success status and file path
    """
    cam = init_camera()
    if cam is None or not cam.is_opened():
        return {'success': False, 'error': 'Camera not available'}

    ret, frame = cam.read()
    if not ret or frame is None:
        return {'success': False, 'error': 'Failed to capture frame'}

    save_dir = os.path.join(os.path.dirname(__file__), '../../data/authorized_faces')
    os.makedirs(save_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{person_name.replace(' ', '_')}_{timestamp}.jpg"
    filepath = os.path.join(save_dir, filename)

    cv2.imwrite(filepath, frame)

    return {
        'success': True,
        'message': f'Face captured for {person_name}',
        'filepath': filepath,
        'filename': filename
    }


def get_current_frame() -> Optional[np.ndarray]:
    """
    Get current frame as numpy array.
    Used by main.py for face recognition.
    """
    cam = init_camera()
    if cam is None or not cam.is_opened():
        return None

    ret, frame = cam.read()
    return frame if ret else None


def release_camera():
    """Release camera resources"""
    global _camera
    if _camera is not None:
        _camera.release()
        _camera = None
        print("✓ Camera released")


if __name__ == '__main__':
    print("Testing camera...")
    frame_bytes = get_camera_snapshot()

    if frame_bytes:
        print(f"✓ Camera working! Captured {len(frame_bytes)} bytes")
    else:
        print("✗ Camera test failed")

    release_camera()
