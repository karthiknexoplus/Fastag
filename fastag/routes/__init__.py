from .auth import auth_bp
from .pwa_dashboard import pwa_dashboard_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(pwa_dashboard_bp, url_prefix='/pwa-dashboard')