from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from authlib.integrations.flask_client import OAuth
from functools import wraps
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

google_auth_bp = Blueprint('google_auth', __name__)

# OAuth setup
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with the Flask app"""
    oauth.init_app(app)
    
    # Google OAuth configuration
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

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
    
    redirect_uri = url_for('google_auth.callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@google_auth_bp.route('/callback')
def callback():
    """Google OAuth callback route"""
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token)
        
        # Extract user information
        user_data = {
            'id': user_info.get('sub'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'given_name': user_info.get('given_name'),
            'family_name': user_info.get('family_name')
        }
        
        logger.info(f"Google OAuth login successful for user: {user_data['email']}")
        
        # Store user in session
        session['user'] = user_data
        session['token'] = token
        
        flash(f'Welcome, {user_data["name"]}! You have been successfully logged in.', 'success')
        return redirect(url_for('auth.home'))
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        flash('Login failed. Please try again.', 'error')
        return redirect(url_for('google_auth.login'))

@google_auth_bp.route('/logout')
def logout():
    """Logout route"""
    if 'user' in session:
        user_name = session['user'].get('name', 'User')
        session.clear()
        flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('google_auth.login'))

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