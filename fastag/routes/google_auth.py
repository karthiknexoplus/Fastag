from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from authlib.integrations.flask_client import OAuth
from functools import wraps
import requests
import json
import logging
import os
import base64
from fastag.utils.db import log_user_login, log_user_action

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

google_auth_bp = Blueprint('google_auth', __name__)

# OAuth setup
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with the Flask app"""
    oauth.init_app(app)
    
    # Check if Google OAuth credentials are configured
    client_id = app.config.get('GOOGLE_CLIENT_ID')
    client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
    logger.info(f"DEBUG: GOOGLE_CLIENT_ID={client_id!r}, GOOGLE_CLIENT_SECRET={client_secret!r}")
    # Strip whitespace for robust checking
    if not client_id or client_id.strip() == 'your-google-client-id' or 'your-actual-secret-here' in str(client_secret).strip():
        logger.warning("Google OAuth credentials not properly configured")
        return
    
    # Google OAuth configuration
    oauth.register(
        name='google',
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    logger.info("Google OAuth initialized successfully")

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('google_auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@google_auth_bp.route('/login')
def login():
    """Google OAuth login route"""
    if 'user' in session:
        return redirect(url_for('auth.home'))
    
    try:
        # Check if Google OAuth is properly configured
        if not hasattr(oauth, 'google'):
            flash('Google OAuth is not properly configured. Please contact administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        redirect_uri = url_for('google_auth.callback', _external=True)
        # Generate a nonce and store in session
        nonce = base64.urlsafe_b64encode(os.urandom(24)).decode()
        session['nonce'] = nonce
        logger.info(f"Google OAuth redirect_uri: {redirect_uri}, nonce: {nonce}")
        return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)
    except Exception as e:
        logger.error(f"Google OAuth login error: {e}")
        flash('Google OAuth is not properly configured. Please contact administrator.', 'error')
        return redirect(url_for('auth.login'))

@google_auth_bp.route('/callback')
def callback():
    """Google OAuth callback route"""
    try:
        token = oauth.google.authorize_access_token()
        nonce = session.pop('nonce', None)
        user_info = oauth.google.parse_id_token(token, nonce=nonce)
        # Extract user information
        user_data = {
            'username': user_info.get('email'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'given_name': user_info.get('given_name'),
            'family_name': user_info.get('family_name'),
            'login_method': 'google'
        }
        logger.info(f"Google OAuth login successful for user: {user_data['email']}")
        # Store user in session
        session['user'] = user_data
        session['token'] = token
        log_user_login(user_data['username'], 'google', picture=user_data['picture'])
        log_user_action(user_data['username'], 'login', 'Google login', picture=user_data['picture'])
        flash(f'Welcome, {user_data["name"]}! You have been successfully logged in.', 'success')
        return redirect(url_for('auth.home'))
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        flash('Login failed. Please try again.', 'error')
        return redirect(url_for('google_auth.login'))

@google_auth_bp.route('/logout')
def logout():
    """Redirect to general logout route"""
    return redirect(url_for('auth.logout'))

@google_auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = session.get('user', {})
    return render_template('google_profile.html', user=user)

@google_auth_bp.route('/api/user-info')
def user_info():
    """API endpoint to get current user information"""
    if 'user' in session:
        return {
            'logged_in': True,
            'user': session['user']
        }
    return {
        'logged_in': False,
        'user': None
    } 