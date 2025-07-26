from flask import Blueprint, render_template

pricing_bp = Blueprint('pricing', __name__)

@pricing_bp.route('/pricing')
def pricing():
    """Render the pricing page"""
    return render_template('pricing.html') 