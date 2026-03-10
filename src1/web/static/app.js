// Dashboard JavaScript - Smart Door Lock System
// Handles real-time updates, API calls, and chart rendering

const API_BASE = '';  // Empty for same-origin requests
let activityChart = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initDashboard();
});

function initDashboard() {
    console.log('🔒 Initializing Smart Door Lock Dashboard...');
    
    // Initialize activity chart
    initActivityChart();
    
    // Set up button event listeners
    setupEventListeners();
    
    // Start real-time updates
    startRealTimeUpdates();
    
    // Update time display
    updateTime();
    setInterval(updateTime, 1000);
    
    console.log('✓ Dashboard initialized');
}

// ============================================================================
// CHART INITIALIZATION
// ============================================================================

function initActivityChart() {
    const ctx = document.getElementById('activityChart').getContext('2d');
    activityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['00', '02', '04', '06', '08', '10', '12', '14', '16', '18', '20', '22'],
            datasets: [{
                label: 'Entries',
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                backgroundColor: '#10b981',
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#666',
                        stepSize: 1
                    },
                    grid: {
                        color: '#2a2a2a'
                    }
                },
                x: {
                    ticks: {
                        color: '#666'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function updateActivityChart(activityData) {
    if (!activityChart) return;
    
    // Convert object to array of counts for each 2-hour block
    const hours = ['00', '02', '04', '06', '08', '10', '12', '14', '16', '18', '20', '22'];
    activityChart.data.datasets[0].data = hours.map(hour => {
        const h = parseInt(hour);
        // Sum up the current hour and next hour for 2-hour blocks
        let count = 0;
        const h1 = h.toString().padStart(2, '0');
        const h2 = (h + 1).toString().padStart(2, '0');
        count += activityData[h1] || 0;
        count += activityData[h2] || 0;
        return count;
    });
    activityChart.update('none'); // Update without animation for performance
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function setupEventListeners() {
    // Unlock door button
    const unlockBtn = document.querySelector('.btn-unlock');
    if (unlockBtn) {
        unlockBtn.addEventListener('click', handleUnlockDoor);
    }
    
    // Capture face button
    const captureBtn = document.querySelector('.btn-capture');
    if (captureBtn) {
        captureBtn.addEventListener('click', handleCaptureFace);
    }
}

// ============================================================================
// BUTTON HANDLERS
// ============================================================================

async function handleUnlockDoor(event) {
    const button = event.target;
    button.disabled = true;
    button.textContent = '🔓 Unlocking...';
    
    try {
        const response = await fetch(`${API_BASE}/api/door/unlock`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Door unlocked successfully!', 'success');
            // Refresh logs after unlock
            setTimeout(() => {
                fetchLogs();
            }, 1000);
        } else {
            showNotification('Failed to unlock door: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Unlock error:', error);
        showNotification('Network error: Could not unlock door', 'error');
    } finally {
        button.disabled = false;
        button.textContent = '🔓 Unlock Door';
    }
}

async function handleCaptureFace(event) {
    const name = prompt('Enter person name:');
    
    if (!name || name.trim() === '') {
        showNotification('Name is required', 'error');
        return;
    }
    
    const button = event.target;
    button.disabled = true;
    button.textContent = '📸 Capturing...';
    
    try {
        const response = await fetch(`${API_BASE}/api/face/capture`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: name.trim() })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(`Face captured for ${name}!`, 'success');
        } else {
            showNotification('Failed to capture face: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Capture error:', error);
        showNotification('Network error: Could not capture face', 'error');
    } finally {
        button.disabled = false;
        button.textContent = '📸 Capture Face';
    }
}

// ============================================================================
// REAL-TIME UPDATES
// ============================================================================

function startRealTimeUpdates() {
    // Initial fetch
    fetchLogs();
    fetchActivity();
    fetchSystemHealth();
    updateCameraFeed();
    
    // Periodic updates
    setInterval(fetchLogs, 5000);           // Every 5 seconds
    setInterval(fetchActivity, 30000);       // Every 30 seconds
    setInterval(fetchSystemHealth, 3000);    // Every 3 seconds
}

// ============================================================================
// API CALLS
// ============================================================================

async function fetchLogs() {
    try {
        const response = await fetch(`${API_BASE}/api/logs`);
        const result = await response.json();
        
        if (result.success) {
            updateLogsList(result.data);
        }
    } catch (error) {
        console.error('Error fetching logs:', error);
    }
}

async function fetchActivity() {
    try {
        const response = await fetch(`${API_BASE}/api/activity`);
        const result = await response.json();
        
        if (result.success) {
            updateActivityChart(result.data);
        }
    } catch (error) {
        console.error('Error fetching activity:', error);
    }
}

async function fetchSystemHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const result = await response.json();
        
        if (result.success) {
            updateSystemHealth(result.data);
        }
    } catch (error) {
        console.error('Error fetching health:', error);
    }
}

function updateCameraFeed() {
    const feedEl = document.querySelector('.video-feed');
    if (!feedEl) return;
    feedEl.style.backgroundImage = "url('/api/camera/stream')";
    feedEl.style.backgroundSize = 'cover';
    feedEl.style.backgroundPosition = 'center';
    feedEl.textContent = '';
}

// ============================================================================
// UI UPDATES
// ============================================================================

function updateLogsList(logs) {
    const logList = document.querySelector('.log-list');
    if (!logList) return;
    
    // Clear existing logs
    logList.innerHTML = '';
    
    // Add new logs
    logs.forEach(log => {
        const logItem = createLogItem(log);
        logList.appendChild(logItem);
    });
    
    // If no logs, show message
    if (logs.length === 0) {
        logList.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">No entries today</div>';
    }
}

function createLogItem(log) {
    const item = document.createElement('div');
    item.className = 'log-item';
    
    // Add denied class for denied entries
    if (log.action === 'denied') {
        item.classList.add('denied');
    }
    
    // Format timestamp
    const timestamp = new Date(log.timestamp);
    const timeStr = timestamp.toLocaleTimeString('en-US', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    // Create avatar (use face image if available)
    const avatar = document.createElement('div');
    avatar.className = 'log-avatar';
    if (log.face_image_path) {
        avatar.style.backgroundImage = `url('${log.face_image_path}')`;
        avatar.style.backgroundSize = 'cover';
        avatar.style.backgroundPosition = 'center';
    }
    
    // Create info section
    const info = document.createElement('div');
    info.className = 'log-info';
    
    const name = document.createElement('div');
    name.className = 'log-name';
    name.textContent = log.person_name;
    
    const time = document.createElement('div');
    time.className = 'log-time';
    
    // Format action text
    let actionText = log.action.charAt(0).toUpperCase() + log.action.slice(1);
    if (log.action === 'manual_unlock') {
        actionText = 'Manual Unlock';
    }
    
    time.textContent = `${timeStr} • ${actionText}`;
    
    info.appendChild(name);
    info.appendChild(time);
    
    item.appendChild(avatar);
    item.appendChild(info);
    
    return item;
}

function updateSystemHealth(health) {
    // Update CPU temperature
    const cpuEl = document.querySelector('.stat-box:nth-child(1) .stat-value');
    if (cpuEl && health.cpu_temp) {
        cpuEl.innerHTML = `${health.cpu_temp}<span class="stat-unit">°C</span>`;
    }
    
    // Update memory
    const memEl = document.querySelector('.stat-box:nth-child(2) .stat-value');
    if (memEl && health.memory) {
        memEl.innerHTML = `${health.memory.percent}<span class="stat-unit">%</span>`;
    }
    
    // Update FPS
    const fpsEl = document.querySelector('.stat-box:nth-child(3) .stat-value');
    if (fpsEl && health.fps) {
        fpsEl.textContent = health.fps;
    }
}

function updateTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
    const timeEl = document.querySelector('.status-item:last-child span');
    if (timeEl) {
        timeEl.textContent = timeStr;
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#dc2626' : '#2563eb'};
        color: white;
        border-radius: 8px;
        font-size: 14px;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Add CSS for notification animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ============================================================================
// ERROR HANDLING
// ============================================================================

window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
});

// Handle network errors gracefully
window.addEventListener('online', function() {
    showNotification('Connection restored', 'success');
    // Refresh all data
    fetchLogs();
    fetchActivity();
    fetchSystemHealth();
});

window.addEventListener('offline', function() {
    showNotification('Connection lost', 'error');
});

console.log('✓ Dashboard script loaded');