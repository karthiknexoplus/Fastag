import os
from flask import Flask
from fastag.utils.logging import setup_logging
from fastag.utils.db import close_db
from dotenv import load_dotenv
load_dotenv()
import subprocess
import logging
from markupsafe import Markup
import requests
import time

def get_rpi_system_info():
    def run(cmd):
        try:
            return subprocess.check_output(cmd, shell=True, text=True).strip()
        except Exception as e:
            logging.warning(f"System info command failed: {cmd} ({e})")
            return 'N/A'
    # Get raw values
    temp_raw = run('/usr/bin/vcgencmd measure_temp')
    volts_raw = run('/usr/bin/vcgencmd measure_volts')
    throttled_raw = run('/usr/bin/vcgencmd get_throttled')
    uptime = run('/usr/bin/uptime -p')
    # RAM: show used/total
    mem_raw = run('/usr/bin/free -h')
    ram = 'N/A'
    if mem_raw and 'Mem:' in mem_raw:
        for line in mem_raw.splitlines():
            if line.startswith('Mem:'):
                parts = line.split()
                if len(parts) >= 3:
                    ram = f"{parts[2]} used / {parts[1]} total"
    # Disk: show used/total
    disk_raw = run('/usr/bin/df -h /')
    disk = 'N/A'
    if disk_raw:
        lines = disk_raw.splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 5:
                disk = f"{parts[2]} used / {parts[1]} total ({parts[4]} full)"
    # Parse temp
    temp = 'N/A'
    temp_status = ''
    temp_status_color = '#28a745'  # green
    temp_icon = '<i class="fas fa-thermometer-half"></i>'
    if temp_raw and 'temp=' in temp_raw:
        try:
            tval = float(temp_raw.split('=')[1].replace("'C",''))
            temp = f"{tval:.1f}°C"
            if tval < 60:
                temp_status = 'Normal'
                temp_status_color = '#28a745'  # green
            elif tval < 75:
                temp_status = 'High'
                temp_status_color = '#ffc107'  # yellow
            else:
                temp_status = 'Critical'
                temp_status_color = '#dc3545'  # red
        except Exception:
            temp = temp_raw
    # Parse volts
    volts = volts_raw.split('=')[1] if volts_raw and '=' in volts_raw else volts_raw
    volts_icon = '<i class="fas fa-bolt"></i>'
    # Parse throttled
    throttled = 'N/A'
    throttled_icon = '<i class="fas fa-tachometer-alt"></i>'
    throttled_color = '#28a745'
    if throttled_raw and 'throttled=' in throttled_raw:
        code = throttled_raw.split('=')[1]
        if code == '0x0':
            throttled = 'No issues'
            throttled_color = '#28a745'
        else:
            issues = []
            throttled_color = '#dc3545'
            val = int(code, 16)
            if val & 0x1: issues.append('Undervoltage detected')
            if val & 0x2: issues.append('ARM frequency capped')
            if val & 0x4: issues.append('Currently throttled')
            if val & 0x8: issues.append('Soft temperature limit active')
            if val & 0x10000: issues.append('Undervoltage has occurred')
            if val & 0x20000: issues.append('ARM frequency capping has occurred')
            if val & 0x40000: issues.append('Throttling has occurred')
            if val & 0x80000: issues.append('Soft temp limit has occurred')
            throttled = ', '.join(issues) if issues else code
    # Uptime
    uptime_icon = '<i class="fas fa-clock"></i>'
    # RAM
    ram_icon = '<i class="fas fa-memory"></i>'
    # Disk
    disk_icon = '<i class="fas fa-hdd"></i>'
    # Compose info with icons and badges
    info = []
    info.append(f"<span style='color:#764ba2;'>{temp_icon} Temp:</span> <span style='color:#333;'>{temp}</span> <span style='background:{temp_status_color};color:#fff;padding:2px 8px;border-radius:8px;font-size:0.85em;margin-left:4px;'>{temp_status}</span>")
    info.append(f"<span style='color:#764ba2;'>{volts_icon} Volt:</span> <span style='color:#333;'>{volts}</span>")
    info.append(f"<span style='color:#764ba2;'>{throttled_icon} Throttled:</span> <span style='color:{throttled_color};'>{throttled}</span>")
    info.append(f"<span style='color:#764ba2;'>{uptime_icon} Uptime:</span> <span style='color:#333;'>{uptime}</span>")
    info.append(f"<span style='color:#764ba2;'>{ram_icon} RAM:</span> <span style='color:#333;'>{ram}</span>")
    info.append(f"<span style='color:#764ba2;'>{disk_icon} Disk:</span> <span style='color:#333;'>{disk}</span>")
    return ' | '.join(info)

def add_missing_columns():
    import sqlite3
    db_path = 'instance/fastag.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("PRAGMA table_info(access_logs)")
    columns = [row[1] for row in c.fetchall()]
    if 'user_id' not in columns:
        c.execute("ALTER TABLE access_logs ADD COLUMN user_id INTEGER;")
    if 'device_id' not in columns:
        c.execute("ALTER TABLE access_logs ADD COLUMN device_id INTEGER;")
    if 'created_at' not in columns:
        c.execute("ALTER TABLE access_logs ADD COLUMN created_at TIMESTAMP;")
    if 'access_time' not in columns:
        c.execute("ALTER TABLE access_logs ADD COLUMN access_time TIMESTAMP;")
    if 'status' not in columns:
        c.execute("ALTER TABLE access_logs ADD COLUMN status TEXT;")
    conn.commit()
    conn.close()

# Call this during initialization
add_missing_columns()

def fastag_mask(value):
    """Mask a FASTag ID, e.g., 34161FA82032861412298640 -> 3*******************40"""
    if not value or len(value) < 5:
        return '*' * len(value)
    return value[0] + '*' * (len(value) - 3) + value[-2:]

def vehicle_mask(value):
    """Mask a vehicle number, e.g., TN66AT2938 -> T*******38"""
    if not value or len(value) < 5:
        return '*' * len(value)
    return value[0] + '*' * (len(value) - 3) + value[-2:]

def create_app():
    from fastag.rfid.relay_controller import RelayController  # updated import after moving class
    from flask import send_from_directory, redirect, url_for
    import os
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config.Config')
    setup_logging(app.config['LOG_DIR'])
    # Attach a single RelayController instance to the app
    app.relay_controller = RelayController()
    
    # PWA-only mode decorator
    def pwa_only_required(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if app.config.get('PWA_ONLY_MODE', False):
                # In PWA-only mode, redirect non-PWA routes to get-the-app
                return redirect('/get-the-app')
            return f(*args, **kwargs)
        return decorated_function
    
    # Register the decorator with the app
    app.pwa_only_required = pwa_only_required
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
    from fastag.routes.offline import offline_bp
    from fastag.routes.health import health_bp
    from fastag.routes.pwa_dashboard import pwa_dashboard_bp
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
    app.register_blueprint(offline_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(pwa_dashboard_bp, url_prefix='/pwa-dashboard')
    # DB teardown
    app.teardown_appcontext(close_db)
    # Register Jinja filters for FASTag and vehicle masking
    app.jinja_env.filters['fastag_mask'] = fastag_mask
    app.jinja_env.filters['vehicle_mask'] = vehicle_mask
    @app.context_processor
    def inject_system_info():
        import os
        return {
            'system_info': Markup(get_rpi_system_info()),
            'config': app.config,
            'COMPANY_NAME': os.environ.get('COMPANY_NAME', 'Onebee Technology Pvt Ltd'),
            'COMPANY_MOBILE': os.environ.get('COMPANY_MOBILE', '9500850000'),
            'COMPANY_EMAIL': os.environ.get('COMPANY_EMAIL', 'info@onebee.in'),
            'COMPANY_WEBSITE': os.environ.get('COMPANY_WEBSITE', 'www.onebee.in'),
            'LOGO_FILENAME': os.environ.get('LOGO_FILENAME', 'logo.png'),
            'FAVICON_FILENAME': os.environ.get('FAVICON_FILENAME', 'favicon.ico'),
            'APP_TITLE': os.environ.get('APP_TITLE', 'FASTag Parking'),
        }
    # Serve the service worker at the web root
    @app.route('/sw.js')
    def sw():
        return send_from_directory(os.path.abspath(os.path.dirname(__file__) + '/../'), 'sw.js')
    @app.route('/firebase-messaging-sw.js')
    def firebase_messaging_sw():
        from flask import send_from_directory
        import os
        return send_from_directory(os.path.abspath(os.path.dirname(__file__) + '/../'), 'firebase-messaging-sw.js')
    return app 