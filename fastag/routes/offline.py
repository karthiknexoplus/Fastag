from flask import Blueprint, render_template

offline_bp = Blueprint('offline', __name__)

@offline_bp.route('/offline.html')
def offline():
    """Serve the offline page"""
    return render_template('offline.html') 