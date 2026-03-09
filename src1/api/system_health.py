"""
System health monitoring module
Monitors CPU temperature, memory usage, and FPS
"""

import psutil
import os
from typing import Dict

def get_cpu_temperature() -> float:
    """
    Get CPU temperature in Celsius
    Returns temperature or 0.0 if unable to read
    """
    try:
        # Raspberry Pi thermal zone
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read().strip()) / 1000.0
            return round(temp, 1)
    except:
        # Fallback: try vcgencmd (may require sudo)
        try:
            import subprocess
            result = subprocess.run(['vcgencmd', 'measure_temp'], 
                                  capture_output=True, text=True)
            # Output format: "temp=52.0'C"
            temp_str = result.stdout.strip().split('=')[1].replace("'C", "")
            return round(float(temp_str), 1)
        except:
            return 0.0

def get_memory_usage() -> Dict:
    """
    Get memory usage statistics
    Returns percentage and MB used
    """
    memory = psutil.virtual_memory()
    return {
        'percent': round(memory.percent, 1),
        'used_mb': round(memory.used / (1024 * 1024), 0),
        'total_mb': round(memory.total / (1024 * 1024), 0)
    }

def get_fps_estimate() -> int:
    """
    Get estimated FPS from camera/face recognition loop
    This is a placeholder - actual FPS should be calculated in main.py
    and stored in a shared file or Redis
    """
    # TODO: Read from shared state file written by main.py
    # For now, return a default value
    try:
        fps_file = '/tmp/door_lock_fps.txt'
        if os.path.exists(fps_file):
            with open(fps_file, 'r') as f:
                return int(float(f.read().strip()))
    except:
        pass
    
    return 15  # Default estimate

def get_disk_usage() -> Dict:
    """Get SD card disk usage"""
    disk = psutil.disk_usage('/')
    return {
        'percent': round(disk.percent, 1),
        'used_gb': round(disk.used / (1024 ** 3), 1),
        'total_gb': round(disk.total / (1024 ** 3), 1)
    }

def get_system_health() -> Dict:
    """
    Get comprehensive system health metrics
    Returns dictionary with all health data
    """
    return {
        'cpu_temp': get_cpu_temperature(),
        'memory': get_memory_usage(),
        'fps': get_fps_estimate(),
        'disk': get_disk_usage(),
        'timestamp': psutil.boot_time()
    }

if __name__ == '__main__':
    # Test system health monitoring
    health = get_system_health()
    print("System Health:")
    print(f"  CPU Temp: {health['cpu_temp']}°C")
    print(f"  Memory: {health['memory']['percent']}% ({health['memory']['used_mb']}MB / {health['memory']['total_mb']}MB)")
    print(f"  FPS: {health['fps']}")
    print(f"  Disk: {health['disk']['percent']}% ({health['disk']['used_gb']}GB / {health['disk']['total_gb']}GB)")