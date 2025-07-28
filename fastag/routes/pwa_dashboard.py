from flask import Blueprint, render_template

pwa_dashboard_bp = Blueprint('pwa_dashboard', __name__)

@pwa_dashboard_bp.route('/')
def pwa_dashboard():
    return render_template('pwa_dashboard_cards.html') 