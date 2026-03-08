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

@app.route('/api/sound/status')
def sound_status():
    try:
        with open("/tmp/last_sound.txt", "r") as f:
            last_time = float(f.read().strip())
        elapsed = time.time() - last_time
        active = elapsed < 5
        from datetime import datetime
        import pytz
        tz = pytz.timezone('Europe/Berlin')
        time_str = datetime.fromtimestamp(last_time, tz).strftime('%H:%M:%S')
        return jsonify({'active': active, 'last_time': time_str})
    except:
        return jsonify({'active': False, 'last_time': None})

@app.route('/api/lock/status')
def lock_status():
    try:
        with open("/tmp/lock_status.txt", "r") as f:
            unlock_time = float(f.read().strip())
        elapsed = time.time() - unlock_time
        remaining = max(0, 10 - elapsed)  # 10 second autolock timer
        unlocked = remaining > 0
        return jsonify({
            'unlocked': unlocked,
            'remaining': int(remaining)
        })
    except:
        return jsonify({'unlocked': False, 'remaining': 0})

@app.route('/api/ui/status')
def ui_status():
    try:
        with open("/tmp/ui_status.txt", "r") as f:
            text = f.read().strip()
        return jsonify({'status': text})
    except:
        return jsonify({'status': 'WAITING'})
        
@app.route('/api/mqtt/status')
def mqtt_status():
    try:
        import subprocess
        result = subprocess.run(
            ['systemctl', 'is-active', 'mosquitto'],
            capture_output=True, text=True
        )
        active = result.stdout.strip() == 'active'
        return jsonify({'active': active})
    except:
        return jsonify({'active': False})
        
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
        if result['success']:
            # Write unlock time for dashboard
            with open("/tmp/lock_status.txt", "w") as f:
                f.write(str(time.time()))
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
