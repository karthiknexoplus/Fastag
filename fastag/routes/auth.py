from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from fastag.utils.db import get_db, log_user_login, log_user_action
import logging
import io
import csv
from flask import jsonify, request
import sqlite3

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@auth_bp.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return redirect(url_for('locations.locations'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        
        # First try regular user login
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user'] = {'username': username, 'login_method': 'local'}
            logging.info(f"User logged in: {username}")
            log_user_login(username, 'local')
            log_user_action(username, 'login', 'Local login')
            return redirect(url_for('auth.home'))
        
        # If not found in users table, check KYC users table
        # Clean contact number (remove spaces, dashes, etc.)
        contact_number = ''.join(filter(str.isdigit, username))
        
        if len(contact_number) == 10:  # Valid contact number format
            kyc_user = db.execute('SELECT * FROM kyc_users WHERE contact_number = ?', (contact_number,)).fetchone()
            if kyc_user and password == contact_number:  # Password is the contact number itself
                session['user'] = {
                    'username': f"kyc_{contact_number}",
                    'login_method': 'kyc',
                    'kyc_user_id': kyc_user['id'],
                    'kyc_user_name': kyc_user['name'],
                    'kyc_user_contact': kyc_user['contact_number'],
                    'kyc_user_vehicle': kyc_user['vehicle_number'],
                    'kyc_user_fastag': kyc_user['fastag_id']
                }
                logging.info(f"KYC user logged in: {contact_number} ({kyc_user['name']})")
                log_user_login(f"kyc_{contact_number}", 'kyc')
                log_user_action(f"kyc_{contact_number}", 'login', f'KYC login - {kyc_user["name"]}')
                flash(f'Welcome back, {kyc_user["name"]}!', 'success')
                return redirect(url_for('auth.home'))
        
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'danger')
            return render_template('signup.html')
        
        db = get_db()
        
        # Check if username already exists
        existing_user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('Username already exists', 'danger')
            return render_template('signup.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        db.execute('INSERT INTO users (username, password, created_at) VALUES (?, ?, datetime("now"))', 
                  (username, hashed_password))
        db.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        log_user_action(username, 'signup', 'New user registered')
        return redirect(url_for('auth.login'))
    
    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    user = session.get('user')
    username = user['username'] if isinstance(user, dict) else user
    session.pop('user', None)
    session.pop('_flashes', None)  # Clear all flash messages
    if username:
        logging.info(f"User logged out: {username}")
        log_user_action(username, 'logout', 'User logged out')
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/audit-log')
def audit_log():
    db = get_db()
    # Get query params
    page = int(request.args.get('page', 1))
    per_page = 20
    search = request.args.get('search', '').strip()
    action_filter = request.args.get('action', '').strip()
    user_filter = request.args.get('user', '').strip()
    # Build query for logins
    login_query = 'SELECT * FROM user_logins'
    login_params = []
    if user_filter:
        login_query += ' WHERE username LIKE ?'
        login_params.append(f'%{user_filter}%')
    login_query += ' ORDER BY login_time DESC LIMIT ? OFFSET ?'
    login_params += [per_page, (page-1)*per_page]
    logins = db.execute(login_query, login_params).fetchall()
    # Build query for actions
    action_query = 'SELECT * FROM user_actions WHERE 1=1'
    action_params = []
    if user_filter:
        action_query += ' AND username LIKE ?'
        action_params.append(f'%{user_filter}%')
    if action_filter:
        action_query += ' AND action LIKE ?'
        action_params.append(f'%{action_filter}%')
    if search:
        action_query += ' AND (details LIKE ? OR action LIKE ? OR username LIKE ?)'
        action_params += [f'%{search}%', f'%{search}%', f'%{search}%']
    action_query += ' ORDER BY action_time DESC LIMIT ? OFFSET ?'
    action_params += [per_page, (page-1)*per_page]
    actions = db.execute(action_query, action_params).fetchall()
    # For pagination controls, get total counts
    login_count = db.execute('SELECT COUNT(*) FROM user_logins').fetchone()[0]
    action_count = db.execute('SELECT COUNT(*) FROM user_actions').fetchone()[0]
    return render_template('audit_log.html', logins=logins, actions=actions, page=page, per_page=per_page, login_count=login_count, action_count=action_count, search=search, action_filter=action_filter, user_filter=user_filter)

@auth_bp.route('/audit-log/export')
def audit_log_export():
    db = get_db()
    actions = db.execute('SELECT * FROM user_actions ORDER BY action_time DESC').fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['User', 'Action', 'Details', 'Time'])
    for a in actions:
        writer.writerow([a['username'], a['action'], a['details'], a['action_time']])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='audit_log.csv')

@auth_bp.route('/api/audit-log', methods=['GET'])
def api_audit_log():
    """
    Returns audit logs (user_actions) as JSON for external devices.
    Query params: user, action, search, start_date, end_date, page, per_page
    """
    db = get_db()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    search = request.args.get('search', '').strip()
    action_filter = request.args.get('action', '').strip()
    user_filter = request.args.get('user', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    # Build query for actions
    action_query = 'SELECT * FROM user_actions WHERE 1=1'
    action_params = []
    if user_filter:
        action_query += ' AND username LIKE ?'
        action_params.append(f'%{user_filter}%')
    if action_filter:
        action_query += ' AND action LIKE ?'
        action_params.append(f'%{action_filter}%')
    if search:
        action_query += ' AND (details LIKE ? OR action LIKE ? OR username LIKE ?)'
        action_params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if start_date:
        action_query += ' AND DATE(action_time) >= ?'
        action_params.append(start_date)
    if end_date:
        action_query += ' AND DATE(action_time) <= ?'
        action_params.append(end_date)
    action_query += ' ORDER BY action_time DESC LIMIT ? OFFSET ?'
    action_params += [per_page, (page-1)*per_page]
    actions = db.execute(action_query, action_params).fetchall()
    # Convert to dicts
    data = [dict(a) for a in actions]
    return jsonify({"success": True, "actions": data, "page": page, "per_page": per_page, "count": len(data)})

@auth_bp.route('/watchlist')
def watchlist():
    return render_template('watchlist.html')

@auth_bp.route('/onboarding')
def onboarding():
    """Serve the onboarding slider page before login."""
    # If user is already logged in, redirect to dashboard
    if 'user' in session:
        return redirect('/pwa-dashboard')
    return render_template('onboarding.html')

@auth_bp.route('/debug/env')
def debug_env():
    import os
    return {
        "GOOGLE_CLIENT_ID": os.environ.get("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET")
    }

@auth_bp.route('/clear-cache')
def clear_cache():
    """Page to clear PWA cache"""
    return send_file('clear_pwa_cache.html')

@auth_bp.route('/api/watchlist/list')
def api_watchlist_list():
    db = get_db()
    # Join with kyc_users to get registered user details
    rows = db.execute('''
        SELECT w.id, w.fastag_id, w.reason, w.added_at, k.name, k.vehicle_number, k.contact_number, k.address
        FROM watchlist_users w
        LEFT JOIN kyc_users k ON w.fastag_id = k.fastag_id
        ORDER BY w.added_at DESC
    ''').fetchall()
    results = []
    for row in rows:
        is_registered = row[4] is not None
        results.append({
            'id': row[0],
            'fastag_id': row[1],
            'reason': row[2],
            'added_at': row[3],
            'type': 'Registered' if is_registered else 'Non-User',
            'name': row[4] or '',
            'vehicle_number': row[5] or '',
            'contact_number': row[6] or '',
            'address': row[7] or ''
        })
    return jsonify({'results': results})

@auth_bp.route('/api/watchlist/add', methods=['POST'])
def api_watchlist_add():
    data = request.get_json()
    fastag_id = data.get('fastag_id')
    reason = data.get('reason', '')
    if not fastag_id:
        return jsonify({'success': False, 'error': 'fastag_id required'}), 400
    db = get_db()
    db.execute('INSERT INTO watchlist_users (fastag_id, reason) VALUES (?, ?)', (fastag_id, reason))
    db.commit()
    return jsonify({'success': True})

@auth_bp.route('/api/watchlist/delete/<int:watchlist_id>', methods=['DELETE'])
def api_watchlist_delete(watchlist_id):
    db = get_db()
    db.execute('DELETE FROM watchlist_users WHERE id = ?', (watchlist_id,))
    db.commit()
    return jsonify({'success': True})

@auth_bp.route('/api/watchlist/edit/<int:watchlist_id>', methods=['POST'])
def api_watchlist_edit(watchlist_id):
    data = request.get_json()
    reason = data.get('reason', '')
    db = get_db()
    db.execute('UPDATE watchlist_users SET reason = ? WHERE id = ?', (reason, watchlist_id))
    db.commit()
    return jsonify({'success': True})

@auth_bp.route('/api/watchlist/activity/<int:watchlist_id>')
def api_watchlist_activity(watchlist_id):
    db = get_db()
    # Get watchlist entry
    entry = db.execute('SELECT fastag_id FROM watchlist_users WHERE id = ?', (watchlist_id,)).fetchone()
    if not entry:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    fastag_id = entry['fastag_id']
    logs = db.execute('''
        SELECT 
            al.timestamp, 
            al.lane_id, 
            l.lane_name,
            r.type as lane_type,
            al.access_result, 
            al.reason,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            tvc.fuel_type
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        JOIN readers r ON al.reader_id = r.id
        WHERE al.tag_id = ?
        ORDER BY al.timestamp DESC
        LIMIT 50
    ''', (fastag_id,)).fetchall()
    results = [dict(row) for row in logs]
    return jsonify({'results': results}) 

@auth_bp.route('/api/watchlist/activity_ist/<int:watchlist_id>')
def api_watchlist_activity_ist(watchlist_id):
    import pytz
    from datetime import datetime
    db = get_db()
    entry = db.execute('SELECT fastag_id FROM watchlist_users WHERE id = ?', (watchlist_id,)).fetchone()
    if not entry:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    fastag_id = entry['fastag_id']
    logs = db.execute('''
        SELECT 
            al.timestamp, 
            al.lane_id, 
            l.lane_name,
            r.type as lane_type,
            al.access_result, 
            al.reason,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            tvc.fuel_type
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        JOIN readers r ON al.reader_id = r.id
        WHERE al.tag_id = ?
        ORDER BY al.timestamp DESC
        LIMIT 50
    ''', (fastag_id,)).fetchall()
    ist_tz = pytz.timezone('Asia/Kolkata')
    results = []
    for row in logs:
        timestamp_str = row[0]
        # Parse as UTC and convert to IST
        try:
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
            ist_time = utc_time.astimezone(ist_tz)
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            ist_time_str = timestamp_str
        results.append({
            'timestamp_ist': ist_time_str,
            'lane_id': row[1],
            'lane_name': row[2],
            'lane_type': row[3],
            'access_result': row[4],
            'reason': row[5],
            'vehicle_number': row[6],
            'owner_name': row[7],
            'model_name': row[8],
            'fuel_type': row[9],
        })
    return jsonify({'results': results}) 

@auth_bp.route('/get-the-app')
def get_the_app():
    """Serve the sleek PWA landing page for mobile users."""
    return render_template('pwa_landing.html') 

@auth_bp.route('/pwa-login', methods=['GET', 'POST'])
def pwa_login():
    # If user is already logged in, redirect to dashboard
    if 'user' in session:
        return redirect('/pwa-dashboard')
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        contact_number = ''.join(filter(str.isdigit, username))
        
        # Check if user exists and password is correct
        if len(contact_number) == 10:
            kyc_user = db.execute('SELECT * FROM kyc_users WHERE contact_number = ?', (contact_number,)).fetchone()
            if kyc_user and password == contact_number:
                # Make session permanent (30 days)
                session.permanent = True
                session['user'] = {
                    'username': f"kyc_{contact_number}",
                    'login_method': 'kyc',
                    'kyc_user_id': kyc_user['id'],
                    'kyc_user_name': kyc_user['name'],
                    'kyc_user_contact': kyc_user['contact_number'],
                    'kyc_user_vehicle': kyc_user['vehicle_number'],
                    'kyc_user_fastag': kyc_user['fastag_id']
                }
                return redirect('/pwa-dashboard')
            elif kyc_user:
                # User exists but wrong password
                error_msg = 'Incorrect password. Please try again.'
            else:
                # User doesn't exist
                error_msg = 'User not found. Please check your contact number.'
        else:
            # Invalid contact number format
            error_msg = 'Please enter a valid 10-digit contact number.'
        
        # Redirect back with error message
        return redirect(f'/pwa-login?error={error_msg}')
    
    return render_template('pwa_login.html')

@auth_bp.route('/pwa-dashboard')
def pwa_dashboard():
    # Check if user is logged in
    if 'user' not in session:
        return redirect('/pwa-login')
    
    user = session.get('user', {})
    name = user.get('kyc_user_name', 'Karthik')
    vehicle = user.get('kyc_user_vehicle', None)
    return render_template('pwa_dashboard_cards.html', name=name, vehicle=vehicle) 

@auth_bp.route('/pwa-logout', methods=['POST'])
def pwa_logout():
    """Logout from PWA and redirect to PWA login"""
    session.clear()
    return jsonify({'success': True, 'redirect': '/pwa-login'}) 