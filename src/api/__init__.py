"""
API Package for Smart Door Lock Dashboard
"""

from .database import init_db, log_access, get_today_logs, get_denied_logs
from .camera import get_camera_snapshot, capture_face_for_training
from .system_health import get_system_health
from .door_control import unlock_door

__all__ = [
    'init_db',
    'log_access',
    'get_today_logs',
    'get_denied_logs',
    'get_camera_snapshot',
    'capture_face_for_training'
    'get_system_health',
    'unlock_door'
]