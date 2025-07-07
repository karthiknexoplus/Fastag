import os
from flask import Flask
from fastag.utils.logging import setup_logging
from fastag.utils.db import close_db
from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config.Config')
    setup_logging(app.config['LOG_DIR'])
    # Register blueprints
    from fastag.routes.auth import auth_bp
    from fastag.routes.locations import locations_bp
    from fastag.routes.lanes import lanes_bp
    from fastag.routes.readers import readers_bp
    from fastag.routes.api import api
    from fastag.routes.kyc_users import kyc_users_bp
    from fastag.routes.admin import admin_bp
    from fastag.routes.analytics import analytics_bp
    from fastag.routes.fuel_price import fuel_price_bp
    from fastag.routes.vehicle_finder import vehicle_finder_bp
    from fastag.routes.bank_finder import bank_finder_bp
    from fastag.routes.fastag_balance import fastag_balance_bp
    from fastag.routes.google_auth import google_auth_bp, init_oauth
    from fastag.routes.challan import challan_bp
    
    # Initialize OAuth
    init_oauth(app)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(lanes_bp)
    app.register_blueprint(readers_bp)
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(kyc_users_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(fuel_price_bp)
    app.register_blueprint(vehicle_finder_bp)
    app.register_blueprint(bank_finder_bp)
    app.register_blueprint(fastag_balance_bp)
    app.register_blueprint(google_auth_bp, url_prefix='/google')
    app.register_blueprint(challan_bp)
    # DB teardown
    app.teardown_appcontext(close_db)
    return app

# Create the app instance for direct import
app = create_app() 