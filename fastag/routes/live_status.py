from flask import Blueprint, render_template, jsonify, request
import subprocess
import json
import logging
from datetime import datetime
import os

live_status_bp = Blueprint('live_status', __name__)

def get_tailscale_status():
    """Get Tailscale status using tailscale status --json"""
    try:
        result = subprocess.run(['tailscale', 'status', '--json'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            logging.error(f"Tailscale status command failed: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        logging.error("Tailscale status command timed out")
        return None
    except Exception as e:
        logging.error(f"Error getting Tailscale status: {e}")
        return None

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    if bytes_value == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_value >= 1024 and i < len(size_names) - 1:
        bytes_value /= 1024.0
        i += 1
    return f"{bytes_value:.1f} {size_names[i]}"

def format_timestamp(timestamp_str):
    """Format timestamp to readable format"""
    if not timestamp_str or timestamp_str == "0001-01-01T00:00:00Z":
        return "Never"
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Invalid"

def get_status_color(online, active):
    """Get color class based on device status"""
    if online and active:
        return "success"
    elif online:
        return "warning"
    else:
        return "danger"

def get_os_icon(os_name):
    """Get icon for operating system"""
    os_icons = {
        'linux': 'fab fa-linux',
        'android': 'fab fa-android',
        'windows': 'fab fa-windows',
        'darwin': 'fab fa-apple',
        'ios': 'fab fa-apple',
        'macos': 'fab fa-apple'
    }
    return os_icons.get(os_name.lower(), 'fas fa-desktop')

@live_status_bp.route('/live_status')
def live_status():
    """Main live status page"""
    status_data = get_tailscale_status()
    return render_template('live_status.html', 
                         status_data=status_data,
                         format_bytes=format_bytes,
                         format_timestamp=format_timestamp,
                         get_status_color=get_status_color,
                         get_os_icon=get_os_icon)

@live_status_bp.route('/api/live_status')
def api_live_status():
    """API endpoint for live status data"""
    status_data = get_tailscale_status()
    if status_data:
        return jsonify({
            "success": True,
            "data": status_data,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({
            "success": False,
            "error": "Failed to get Tailscale status"
        }), 500 