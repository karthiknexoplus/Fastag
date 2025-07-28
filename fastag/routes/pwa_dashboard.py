from flask import Blueprint, render_template

pwa_dashboard_bp = Blueprint('pwa_dashboard', __name__)

@pwa_dashboard_bp.route('/pwa-dashboard')
def pwa_dashboard():
    return render_template('pwa_dashboard_cards.html') 