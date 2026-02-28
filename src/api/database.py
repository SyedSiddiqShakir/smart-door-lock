"""
Database module for managing access logs
Uses SQLite for lightweight, file-based storage
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'door_lock.db')

def get_db_connection():
    """Create and return a database connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    """Initialize database schema if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create access_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            person_name TEXT NOT NULL,
            action TEXT NOT NULL,
            face_image_path TEXT,
            confidence REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON access_logs(timestamp DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_action 
        ON access_logs(action)
    ''')
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {DB_PATH}")

def log_access(person_name: str, action: str, face_path: Optional[str] = None, confidence: float = 0.0):
    """
    Log an access event to database
    
    Args:
        person_name: Name of person (or "Unknown" for denied)
        action: 'entry', 'exit', 'denied', 'manual_unlock'
        face_path: Path to saved face image (optional)
        confidence: Recognition confidence score (0.0 - 1.0)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO access_logs (person_name, action, face_image_path, confidence)
        VALUES (?, ?, ?, ?)
    ''', (person_name, action, face_path, confidence))
    
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    
    return log_id

def get_today_logs() -> List[Dict]:
    """
    Get all access logs from today (entries and exits, not denied)
    Returns list of dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    cursor.execute('''
        SELECT id, timestamp, person_name, action, face_image_path, confidence
        FROM access_logs
        WHERE DATE(timestamp) = ?
        AND action IN ('entry', 'exit', 'manual_unlock')
        ORDER BY timestamp DESC
    ''', (today,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    logs = []
    for row in rows:
        logs.append({
            'id': row['id'],
            'timestamp': row['timestamp'],
            'person_name': row['person_name'],
            'action': row['action'],
            'face_image_path': row['face_image_path'],
            'confidence': row['confidence']
        })
    
    return logs

def get_denied_logs() -> List[Dict]:
    """
    Get denied access attempts from today
    Returns list of dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    cursor.execute('''
        SELECT id, timestamp, person_name, face_image_path, confidence
        FROM access_logs
        WHERE DATE(timestamp) = ?
        AND action = 'denied'
        ORDER BY timestamp DESC
    ''', (today,))
    
    rows = cursor.fetchall()
    conn.close()
    
    logs = []
    for row in rows:
        logs.append({
            'id': row['id'],
            'timestamp': row['timestamp'],
            'person_name': row['person_name'],
            'face_image_path': row['face_image_path'],
            'confidence': row['confidence']
        })
    
    return logs

def get_hourly_activity() -> Dict:
    """
    Get hourly activity counts for today (for chart)
    Returns dictionary with hours as keys and counts as values
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    cursor.execute('''
        SELECT 
            strftime('%H', timestamp) as hour,
            COUNT(*) as count
        FROM access_logs
        WHERE DATE(timestamp) = ?
        AND action IN ('entry', 'exit', 'manual_unlock')
        GROUP BY hour
        ORDER BY hour
    ''', (today,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Create dictionary with all 24 hours initialized to 0
    activity = {f"{h:02d}": 0 for h in range(24)}

    # Fill in actual counts
    for row in rows:
        activity[row['hour']] = row['count']
    
    return activity

def get_logs_by_date(date) -> List[Dict]:
    """
    Get all logs for a specific date
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, timestamp, person_name, action, face_image_path, confidence
        FROM access_logs
        WHERE DATE(timestamp) = ?
        ORDER BY timestamp DESC
    ''', (date,))
    
    rows = cursor.fetchall()
    conn.close()
    
    logs = []
    for row in rows:
        logs.append({
            'id': row['id'],
            'timestamp': row['timestamp'],
            'person_name': row['person_name'],
            'action': row['action'],
            'face_image_path': row['face_image_path'],
            'confidence': row['confidence']
        })
    
    return logs

def cleanup_old_logs(days_to_keep: int = 30):
    """
    Delete logs older than specified days
    Helps manage database size on SD card
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    cursor.execute('''
        DELETE FROM access_logs
        WHERE timestamp < ?
    ''', (cutoff_date,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count

if __name__ == '__main__':
    # Test database initialization
    init_db()
    
    # Test logging
    log_id = log_access("Test User", "entry", None, 0.95)
    print(f"✓ Test log created with ID: {log_id}")
    
    # Test retrieval
    logs = get_today_logs()
    print(f"✓ Today's logs: {len(logs)} entries")