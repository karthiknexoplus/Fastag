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
        # Try to find tailscale in common locations
        tailscale_paths = [
            'tailscale',
            '/usr/bin/tailscale',
            '/usr/local/bin/tailscale',
            '/opt/tailscale/tailscale'
        ]
        
        tailscale_cmd = None
        for path in tailscale_paths:
            try:
                result = subprocess.run([path, 'version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    tailscale_cmd = path
                    break
            except:
                continue
        
        if not tailscale_cmd:
            logging.error("Tailscale command not found in system PATH")
            # Return sample data for development/testing
            return get_sample_tailscale_data()
            
        result = subprocess.run([tailscale_cmd, 'status', '--json'], 
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

def get_sample_tailscale_data():
    """Return sample Tailscale data for development/testing"""
    return {
        "Version": "1.84.0-t160c11f37-gbf6042458",
        "TUN": True,
        "BackendState": "Running",
        "HaveNodeKey": True,
        "AuthURL": "",
        "TailscaleIPs": [
            "100.126.86.89",
            "fd7a:115c:a1e0::2901:5659"
        ],
        "Self": {
            "ID": "nkqSsYpUZi11CNTRL",
            "PublicKey": "nodekey:88304d1f46685751c2f7140592e0e2069b72705f54692b3788e2e10329be5658",
            "HostName": "ip-172-31-27-131",
            "DNSName": "ip-172-31-27-131.tail2528d1.ts.net.",
            "OS": "linux",
            "UserID": 1759203656033992,
            "TailscaleIPs": [
                "100.126.86.89",
                "fd7a:115c:a1e0::2901:5659"
            ],
            "AllowedIPs": [
                "100.126.86.89/32",
                "fd7a:115c:a1e0::2901:5659/128"
            ],
            "Addrs": [
                "13.61.147.37:41641",
                "172.31.27.131:41641"
            ],
            "CurAddr": "",
            "Relay": "hel",
            "RxBytes": 1024,
            "TxBytes": 2048,
            "Created": "2025-07-10T16:13:44.788433036Z",
            "LastWrite": "0001-01-01T00:00:00Z",
            "LastSeen": "0001-01-01T00:00:00Z",
            "LastHandshake": "0001-01-01T00:00:00Z",
            "Online": True,
            "ExitNode": False,
            "ExitNodeOption": False,
            "Active": False,
            "PeerAPIURL": [
                "http://100.126.86.89:36810",
                "http://[fd7a:115c:a1e0::2901:5659]:41127"
            ],
            "TaildropTarget": 0,
            "NoFileSharingReason": "",
            "Capabilities": [
                "HTTPS://TAILSCALE.COM/s/DEPRECATED-NODE-CAPS#see-https://github.com/tailscale/tailscale/issues/11508",
                "funnel",
                "https",
                "https://tailscale.com/cap/file-sharing",
                "https://tailscale.com/cap/funnel-ports?ports=443,8443,10000",
                "https://tailscale.com/cap/is-admin",
                "https://tailscale.com/cap/ssh",
                "https://tailscale.com/cap/tailnet-lock",
                "probe-udp-lifetime",
                "ssh-behavior-v1",
                "ssh-env-vars",
                "store-appc-routes"
            ],
            "CapMap": {
                "funnel": None,
                "https": None,
                "https://tailscale.com/cap/file-sharing": None,
                "https://tailscale.com/cap/funnel-ports?ports=443,8443,10000": None,
                "https://tailscale.com/cap/is-admin": None,
                "https://tailscale.com/cap/ssh": None,
                "https://tailscale.com/cap/tailnet-lock": None,
                "probe-udp-lifetime": None,
                "ssh-behavior-v1": None,
                "ssh-env-vars": None,
                "store-appc-routes": None
            },
            "InNetworkMap": True,
            "InMagicSock": False,
            "InEngine": False,
            "KeyExpiry": "2026-01-06T16:13:44Z"
        },
        "Health": [],
        "MagicDNSSuffix": "tail2528d1.ts.net",
        "CurrentTailnet": {
            "Name": "karthik.devarajiit@gmail.com",
            "MagicDNSSuffix": "tail2528d1.ts.net",
            "MagicDNSEnabled": True
        },
        "CertDomains": [
            "ip-172-31-27-131.tail2528d1.ts.net"
        ],
        "Peer": {
            "nodekey:185a58a955187efc6da32fc483cf57c9b6d5c11148ed3b6856d36c22751cd043": {
                "ID": "n2kyycMXh121CNTRL",
                "PublicKey": "nodekey:185a58a955187efc6da32fc483cf57c9b6d5c11148ed3b6856d36c22751cd043",
                "HostName": "localhost",
                "DNSName": "xiaomi-22031116ai.tail2528d1.ts.net.",
                "OS": "android",
                "UserID": 1759203656033992,
                "TailscaleIPs": [
                    "100.92.208.68",
                    "fd7a:115c:a1e0::7501:d044"
                ],
                "AllowedIPs": [
                    "100.92.208.68/32",
                    "fd7a:115c:a1e0::7501:d044/128"
                ],
                "Addrs": None,
                "CurAddr": "",
                "Relay": "",
                "RxBytes": 512,
                "TxBytes": 1024,
                "Created": "2025-07-08T04:02:23.112670989Z",
                "LastWrite": "0001-01-01T00:00:00Z",
                "LastSeen": "2025-07-10T14:06:52.1Z",
                "LastHandshake": "0001-01-01T00:00:00Z",
                "Online": False,
                "ExitNode": False,
                "ExitNodeOption": False,
                "Active": False,
                "PeerAPIURL": [
                    "http://100.92.208.68:1",
                    "http://[fd7a:115c:a1e0::7501:d044]:1"
                ],
                "TaildropTarget": 5,
                "NoFileSharingReason": "",
                "InNetworkMap": True,
                "InMagicSock": True,
                "InEngine": False,
                "Expired": True,
                "KeyExpiry": "2025-07-09T17:58:36Z"
            },
            "nodekey:66305fc09eb2560901dc23d191e8604106e8a862c4ec92c8127942321dfed315": {
                "ID": "nBCqx71UC621CNTRL",
                "PublicKey": "nodekey:66305fc09eb2560901dc23d191e8604106e8a862c4ec92c8127942321dfed315",
                "HostName": "pgshospital",
                "DNSName": "pgshospital.tail2528d1.ts.net.",
                "OS": "linux",
                "UserID": 1759203656033992,
                "TailscaleIPs": [
                    "100.126.211.22",
                    "fd7a:115c:a1e0::1d01:d316"
                ],
                "AllowedIPs": [
                    "100.126.211.22/32",
                    "fd7a:115c:a1e0::1d01:d316/128"
                ],
                "Addrs": None,
                "CurAddr": "",
                "Relay": "",
                "RxBytes": 256,
                "TxBytes": 512,
                "Created": "2025-07-10T13:44:40.721509577Z",
                "LastWrite": "0001-01-01T00:00:00Z",
                "LastSeen": "2025-07-10T16:18:02.1Z",
                "LastHandshake": "0001-01-01T00:00:00Z",
                "Online": False,
                "ExitNode": False,
                "ExitNodeOption": False,
                "Active": False,
                "PeerAPIURL": [
                    "http://100.126.211.22:49093",
                    "http://[fd7a:115c:a1e0::1d01:d316]:37032"
                ],
                "TaildropTarget": 5,
                "NoFileSharingReason": "",
                "InNetworkMap": True,
                "InMagicSock": True,
                "InEngine": False,
                "Expired": True,
                "KeyExpiry": "2025-07-09T16:17:53Z"
            }
        },
        "User": {
            "1759203656033992": {
                "ID": 1759203656033992,
                "LoginName": "karthik.devarajiit@gmail.com",
                "DisplayName": "Karthik Devaraj",
                "ProfilePicURL": "https://lh3.googleusercontent.com/a/ACg8ocK7zxPZmAEYM51sA1I2iy5ixwryYKKM1dMSs4K5uCXydEAfZA=s96-c"
            }
        },
        "ClientVersion": {
            "RunningLatest": True
        }
    }

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