"""
Flask API Server for Smart Door Lock Dashboard
Serves dashboard UI and provides REST API for access logs, camera feed, and system health
"""

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import os
import sys
from datetime import datetime
import json

# Add parent directory to path to import from other modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.api.database import (
    init_db, 
    get_today_logs, 
    get_denied_logs,
    log_access,
    get_hourly_activity
)
from src.api.camera import get_camera_snapshot, capture_face_for_training
from src.api.system_health import get_system_health
from src.api.door_control import unlock_door

app = Flask(__name__, 
            static_folder='../web/static',
            template_folder='../web/templates')
CORS(app)  # Enable CORS for frontend requests

# Initialize database on startup
init_db()

# Serve dashboard HTML
@app.route('/')
def index():
    return send_from_directory(app.template_folder, 'dashboard.html')

# API Routes

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """
    Get today's access logs (entries and exits)
    Returns: JSON array of log entries
    """
    try:
        logs = get_today_logs()
        return jsonify({
            'success': True,
            'data': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/logs/denied', methods=['GET'])
def get_denied():
    """
    Get denied access attempts (unrecognized faces)
    Returns: JSON array of denied entries
    """
    try:
        denied = get_denied_logs()
        return jsonify({
            'success': True,
            'data': denied,
            'count': len(denied)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/activity', methods=['GET'])
def get_activity():
    """
    Get hourly activity data for chart
    Returns: JSON with hourly entry counts
    """
    try:
        activity = get_hourly_activity()
        return jsonify({
            'success': True,
            'data': activity
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/camera/snapshot', methods=['GET'])
def camera_snapshot():
    """
    Get current camera frame as JPEG
    Returns: JPEG image
    """
    try:
        frame = get_camera_snapshot()
        if frame is not None:
            return Response(frame, mimetype='image/jpeg')
        else:
            return jsonify({
                'success': False,
                'error': 'Camera not available'
            }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/face/capture', methods=['POST'])
def capture_face():
    """
    Capture current camera frame and save for training
    Body: { "name": "John Doe" }
    Returns: Success status and file path
    """
    try:
        data = request.get_json()
        name = data.get('name', 'Unknown')
        
        result = capture_face_for_training(name)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/door/unlock', methods=['POST'])
def manual_unlock():
    """
    Manually unlock the door
    Returns: Success status
    """
    try:
        result = unlock_door()
        
        # Log the manual unlock event
        log_access(
            person_name="Manual Unlock",
            action="manual_unlock",
            face_path=None,
            confidence=1.0
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def system_health():
    """
    Get system health metrics (CPU temp, memory, FPS)
    Returns: JSON with health data
    """
    try:
        health = get_system_health()
        return jsonify({
            'success': True,
            'data': health
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Run Flask server
    # For production, use gunicorn: gunicorn -w 1 -b 0.0.0.0:5000 src.api.app:app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )