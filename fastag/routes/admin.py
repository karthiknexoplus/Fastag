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

@admin_bp.route('/edit_device/<int:device_id>', methods=['GET', 'POST'])
def edit_device(device_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    device = db.execute('SELECT * FROM devices WHERE id=?', (device_id,)).fetchone()
    users = db.execute('SELECT id, username FROM users').fetchall()
    if request.method == 'POST':
        model = request.form.get('model')
        manufacturer = request.form.get('manufacturer')
        android_version = request.form.get('android_version')
        username = request.form.get('username')
        password = request.form.get('password')
        assigned_user_id = request.form.get('assigned_user_id')
        approved = 1 if request.form.get('approved') == 'on' else 0
        db.execute('''UPDATE devices SET model=?, manufacturer=?, android_version=?, username=?, password=?, assigned_user_id=?, approved=? WHERE id=?''',
                   (model, manufacturer, android_version, username, password, assigned_user_id, approved, device_id))
        db.commit()
        flash('Device updated successfully!', 'success')
        return redirect(url_for('admin.user_approval'))
    return render_template('edit_device.html', device=device, users=users)

@admin_bp.route('/delete_device/<int:device_id>', methods=['POST'])
def delete_device(device_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    db.execute('DELETE FROM devices WHERE id=?', (device_id,))
    db.commit()
    flash('Device deleted successfully!', 'success')
    return redirect(url_for('admin.user_approval')) 