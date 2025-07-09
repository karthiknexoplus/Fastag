from flask import Blueprint, redirect, url_for, session, flash, jsonify, request, render_template
import subprocess
import os
from fastag.utils.db import get_db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/restart_readers', methods=['POST'])
def restart_readers():
    if 'user' not in session:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return redirect(url_for('auth.login'))
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../launcher_readers.py'))
        subprocess.Popen(['python3', script_path])
        if request.is_json:
            return jsonify({'success': True, 'message': 'RFID reader services restarted.'})
        flash('RFID reader services restarted.', 'success')
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Failed to restart RFID reader services: ' + str(e), 'danger')
    return redirect(url_for('kyc_users.kyc_users'))

@admin_bp.route('/user_approval', methods=['GET', 'POST'])
def user_approval():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    if request.method == 'POST':
        # Approve device and set username/password/assigned_user_id
        device_id = request.form.get('device_id')
        username = request.form.get('username')
        password = request.form.get('password')
        assigned_user_id = request.form.get('assigned_user_id')
        if device_id and username and password:
            db.execute('UPDATE devices SET approved=1, username=?, password=?, assigned_user_id=? WHERE id=?',
                       (username, password, assigned_user_id, device_id))
            db.commit()
            flash('Device approved and user assigned!', 'success')
        else:
            flash('All fields are required to approve a device.', 'danger')
    # List all devices pending approval
    devices = db.execute('SELECT * FROM devices WHERE approved=0').fetchall()
    users = db.execute('SELECT id, username FROM users').fetchall()
    # List all approved devices with assigned user info
    approved_devices = db.execute('''
        SELECT d.*, u.username as assigned_username FROM devices d
        LEFT JOIN users u ON d.assigned_user_id = u.id
        WHERE d.approved=1
        ORDER BY d.created_at DESC
    ''').fetchall()
    return render_template('user_approval.html', devices=devices, users=users, approved_devices=approved_devices) 