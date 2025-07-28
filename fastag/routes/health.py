from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/api/health')
def health_check():
    """Health check endpoint for PWA service worker"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'FASTag Parking Management System'
    }) 