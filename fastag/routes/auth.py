from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from fastag.utils.db import get_db, log_user_login, log_user_action
import logging
import io
import csv

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
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user'] = {'username': username, 'login_method': 'local'}
            logging.info(f"User logged in: {username}")
            log_user_login(username, 'local')
            log_user_action(username, 'login', 'Local login')
            return redirect(url_for('auth.home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    db = get_db()
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm = request.form.get('confirm')
        if not username or not password or not confirm:
            flash('All fields are required.', 'danger')
            return render_template('signup.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html')
        existing = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            flash('Username already exists.', 'danger')
            return render_template('signup.html')
        hashed = generate_password_hash(password)
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
        db.commit()
        session['user'] = {'username': username, 'login_method': 'local'}
        log_user_login(username, 'signup')
        log_user_action(username, 'signup', 'User registered')
        flash('Signup successful! You are now logged in.', 'success')
        return redirect(url_for('auth.home'))
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

@auth_bp.route('/debug/env')
def debug_env():
    import os
    return {
        "GOOGLE_CLIENT_ID": os.environ.get("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET")
    } 