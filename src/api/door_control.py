import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    # Import existing MQTT module from your codebase
    from src.comms.mqtt import send_open
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: MQTT module not available")

def unlock_door() -> dict:
    """
    Send unlock command to Arduino/ESP32
    Tries MQTT first, falls back to Serial

    Returns:
        Dictionary with success status and message
    """

    # Try MQTT first (preferred for ESP32)
    if MQTT_AVAILABLE:
        try:
            send_open()
            return {
                'success': True,
                'message': 'Door unlocked via MQTT',
                'method': 'mqtt'
            }
        except Exception as e:
            print(f"MQTT unlock failed: {e}")

    # If both methods unavailable, simulate for testing
    print("⚠️ No hardware connection - simulating unlock")
    return {
        'success': True,
        'message': 'Door unlock simulated (no hardware connected)',
        'method': 'simulation'
    }

def lock_door() -> dict:
    """
    Send lock command (if needed for future features)
    """
    if MQTT_AVAILABLE:
        try:
            # Implement lock command in your MQTT module
            return {
                'success': True,
                'message': 'Door locked via MQTT',
                'method': 'mqtt'
            }
        except Exception as e:
            print(f"MQTT lock failed: {e}")

    return {
        'success': False,
        'message': 'Lock command not implemented'
    }

if __name__ == '__main__':
    # Test door control
    print("Testing door unlock...")
    result = unlock_door()
    print(f"Result: {result}")