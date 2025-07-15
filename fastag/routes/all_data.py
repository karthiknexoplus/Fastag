from flask import Blueprint, render_template, request, session, jsonify
import requests
import logging
from fastag.routes.live_status import get_tailscale_status
from fastag.utils.db import get_db
from datetime import datetime

all_data_bp = Blueprint('all_data', __name__)

# Helper to get device list from Tailscale status
def get_device_list():
    status_data = get_tailscale_status()
    devices = []
    if not status_data:
        return devices
    # Add Self
    if 'Self' in status_data:
        devices.append({
            'name': status_data['Self'].get('HostName'),
            'dns': status_data['Self'].get('DNSName'),
        })
    # Add Peers
    for peer in status_data.get('Peer', {}).values():
        devices.append({
            'name': peer.get('HostName'),
            'dns': peer.get('DNSName'),
        })
    return devices

@all_data_bp.route('/all_data', methods=['GET', 'POST'])
def all_data():
    if 'user' not in session:
        return render_template('login.html')
    devices = get_device_list()
    selected = None
    data = None
    error = None
    db = get_db()
    if request.method == 'POST':
        selected = request.form.get('device')
        # Find DNS for selected
        device = next((d for d in devices if d['name'] == selected), None)
        if device and device['dns']:
            api_url = f"https://{device['dns'].rstrip('.')}/api/api/all_data"
            try:
                resp = requests.get(api_url, timeout=10, verify=False)
                if resp.status_code == 200:
                    data = resp.json()
                    # Store/update in DB (simple upsert by device name)
                    db.execute('REPLACE INTO all_data_cache (device, data, updated_at) VALUES (?, ?, ?)',
                        (selected, resp.text, datetime.now().isoformat()))
                    db.commit()
                else:
                    error = f"API error: {resp.status_code}"
            except Exception as e:
                error = f"Request failed: {e}"
        else:
            error = "Device not found or DNS missing."
    # On GET or if no new fetch, try to load from DB
    if not data and selected:
        row = db.execute('SELECT data FROM all_data_cache WHERE device=?', (selected,)).fetchone()
        if row:
            try:
                data = row['data']
                import json
                data = json.loads(data)
            except Exception:
                data = None
    return render_template('all_data.html', devices=devices, selected=selected, data=data, error=error) 