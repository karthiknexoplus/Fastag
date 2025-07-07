from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from fastag.utils.db import get_db
import logging

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
            session['user'] = username
            logging.info(f"User logged in: {username}")
            return redirect(url_for('auth.home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
            db.commit()
            logging.info(f"New user registered: {username}")
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except:
            flash('Username already exists', 'danger')
    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    username = session.get('user')
    session.pop('user', None)
    if username:
        logging.info(f"User logged out: {username}")
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/debug/env')
def debug_env():
    import os
    return {
        "GOOGLE_CLIENT_ID": os.environ.get("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET")
    } 