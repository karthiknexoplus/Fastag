import os
from flask import Flask
from fastag.utils.logging import setup_logging
from fastag.utils.db import close_db
from dotenv import load_dotenv
load_dotenv()
import subprocess
import logging

def get_rpi_system_info():
    def run(cmd):
        try:
            return subprocess.check_output(cmd, shell=True, text=True).strip()
        except Exception as e:
            logging.warning(f"System info command failed: {cmd} ({e})")
            return 'N/A'
    temp = run('/usr/bin/vcgencmd measure_temp')
    volts = run('/usr/bin/vcgencmd measure_volts')
    throttled = run('/usr/bin/vcgencmd get_throttled')
    uptime = run('/usr/bin/uptime -p')
    mem = run('/usr/bin/free -h | grep Mem')
    disk = run('/usr/bin/df -h / | tail -1')
    info = []
    if temp: info.append(f"Temp: {temp}")
    if volts: info.append(f"Volt: {volts}")
    if throttled: info.append(f"Throttled: {throttled}")
    if uptime: info.append(f"Uptime: {uptime}")
    if mem: info.append(f"RAM: {mem}")
    if disk: info.append(f"Disk: {disk}")
    return ' | '.join(info)

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
    @app.context_processor
    def inject_system_info():
        return {'system_info': get_rpi_system_info()}
    return app

# Create the app instance for direct import
app = create_app() 