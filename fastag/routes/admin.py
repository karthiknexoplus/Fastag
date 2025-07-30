from flask import Blueprint, redirect, url_for, session, flash, jsonify, request, current_app
import subprocess
import os

admin_bp = Blueprint('admin', __name__)

# PWA-only mode check function
def check_pwa_only_mode():
    if current_app.config.get('PWA_ONLY_MODE', False):
        return redirect('/get-the-app')
    return None

@admin_bp.route('/admin/restart_readers', methods=['POST'])
def restart_readers():
    # Check PWA-only mode
    pwa_check = check_pwa_only_mode()
    if pwa_check:
        return pwa_check
    
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