"""
Flask API Server for Smart Door Lock Dashboard
Serves dashboard UI and provides REST API for access logs, camera feed, and system health
"""

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import os
import sys
import time
from datetime import datetime
import json

# Add parent directory to path to import from other modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.api.database import (
    init_db, 
    get_today_logs, 
    log_access,
    get_hourly_activity
)
from src.api.camera import get_camera_snapshot, capture_face_for_training
from src.api.system_health import get_system_health
from src.api.door_control import unlock_door

app = Flask(__name__, 
            static_folder='../web/static',
            template_folder='../web/templates')
CORS(app)

# Initialize database on startup
init_db()

# Serve dashboard HTML
@app.route('/')
def index():
    return send_from_directory(app.template_folder, 'dashboard.html')

# ── MJPEG Stream ──
def generate_frames():
    while True:
        try:
            with open("/tmp/latest_frame.jpg", "rb") as f:
                frame = f.read()
            if len(frame) > 0:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except:
            pass
        time.sleep(0.1)

@app.route('/api/camera/snapshot', methods=['GET'])
def camera_snapshot():
    try:
        frame = get_camera_snapshot()
        if frame is not None:
            return Response(frame, mimetype='image/jpeg')
        else:
            return jsonify({'success': False, 'error': 'Camera not available'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/camera/stream')
def camera_stream():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        logs = get_today_logs()
        return jsonify({
            'success': True,
            'data': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/activity', methods=['GET'])
def get_activity():
    try:
        activity = get_hourly_activity()
        return jsonify({
            'success': True,
            'data': activity
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/face/capture', methods=['POST'])
def capture_face():
    try:
        data = request.get_json()
        name = data.get('name', 'Unknown')
        result = capture_face_for_training(name)
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/door/unlock', methods=['POST'])
def manual_unlock():
    try:
        result = unlock_door()
        log_access(
            person_name="Manual Unlock",
            action="manual_unlock",
            face_path=None,
            confidence=1.0
        )
        return jsonify(result), 200 if result['success'] else 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def system_health():
    try:
        health = get_system_health()
        return jsonify({
            'success': True,
            'data': health
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
