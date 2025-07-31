from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, current_app
import logging
import requests
from bs4 import BeautifulSoup
import os
import json
import re

# Add user agent parsing utilities
def parse_user_agent(user_agent):
    """Parse user agent string to extract device information"""
    if not user_agent:
        return {
            'device_type': 'unknown',
            'browser': 'unknown',
            'os': 'unknown'
        }
    
    user_agent = user_agent.lower()
    
    # Device type detection
    device_type = 'desktop'
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        device_type = 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        device_type = 'tablet'
    
    # Browser detection
    browser = 'unknown'
    if 'chrome' in user_agent:
        browser = 'chrome'
    elif 'firefox' in user_agent:
        browser = 'firefox'
    elif 'safari' in user_agent:
        browser = 'safari'
    elif 'edge' in user_agent:
        browser = 'edge'
    elif 'opera' in user_agent:
        browser = 'opera'
    
    # OS detection
    os_name = 'unknown'
    if 'android' in user_agent:
        os_name = 'android'
    elif 'iphone' in user_agent or 'ipad' in user_agent:
        os_name = 'ios'
    elif 'windows' in user_agent:
        os_name = 'windows'
    elif 'mac' in user_agent:
        os_name = 'macos'
    elif 'linux' in user_agent:
        os_name = 'linux'
    
    return {
        'device_type': device_type,
        'browser': browser,
        'os': os_name
    }

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

pwa_dashboard_bp = Blueprint('pwa_dashboard', __name__)

@pwa_dashboard_bp.route('/', strict_slashes=False)
def pwa_dashboard():
    return render_template('pwa_dashboard_cards.html')

@pwa_dashboard_bp.route('/reader-settings')
def reader_settings():
    """Reader Settings page with power control functionality"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    # Get all readers with their information
    readers = db.execute('''
        SELECT r.id, r.reader_ip, r.type, r.mac_address, l.lane_name, loc.name as location_name
        FROM readers r
        JOIN lanes l ON r.lane_id = l.id
        JOIN locations loc ON l.location_id = loc.id
        ORDER BY r.id
    ''').fetchall()
    
    return render_template('pwa_reader_settings.html', readers=readers)

@pwa_dashboard_bp.route('/api/fuel-price', methods=['GET'])
def api_fuel_price():
    """API endpoint for fuel prices"""
    city_filter = request.args.get('city', '').strip().lower()
    url = "https://www.coverfox.com/petrol-price-in-india/"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first table for city-wise prices
        tables = soup.find_all('table', class_='art-table')
        city_table = tables[0] if tables else None
        prices = []
        cities = set()
        
        if city_table:
            for row in city_table.tbody.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 4:
                    city1 = cols[0].text.strip()
                    price1 = cols[1].text.strip()
                    city2 = cols[2].text.strip()
                    price2 = cols[3].text.strip()
                    prices.append({'city': city1, 'price': price1})
                    prices.append({'city': city2, 'price': price2})
                    cities.add(city1)
                    cities.add(city2)
        
        # Filter if city_filter is set
        if city_filter:
            filtered_prices = [p for p in prices if p['city'].lower() == city_filter]
        else:
            filtered_prices = prices
            
        return jsonify({
            "success": True,
            "prices": filtered_prices,
            "cities": sorted(list(cities)),
            "selected_city": city_filter
        })
        
    except Exception as e:
        logging.error(f"Error fetching fuel prices: {e}")
        return jsonify({
            "success": False,
            "error": "Unable to fetch fuel prices at the moment."
        }), 500

@pwa_dashboard_bp.route('/api/vehicle-demographics', methods=['GET'])
def api_vehicle_demographics():
    """API endpoint for vehicle demographics"""
    try:
        db = get_db()
        
        # Check if we have vehicle data
        total_vehicles = db.execute("SELECT COUNT(*) FROM tag_vehicle_cache").fetchone()[0]
        
        if total_vehicles == 0:
            # No vehicle data - return default demographics
            demographics = {
                'fuel_types': [
                    {'type': 'Petrol', 'count': 0, 'percentage': 0},
                    {'type': 'Diesel', 'count': 0, 'percentage': 0},
                    {'type': 'Electric', 'count': 0, 'percentage': 0}
                ],
                'top_models': [
                    {'model': 'No data available', 'count': 0, 'percentage': 0}
                ],
                'year_analysis': {
                    'range': 'No data',
                    'count': 0
                }
            }
            return jsonify(demographics)
        
        # Fuel type distribution
        fuel_distribution = db.execute("""
            SELECT 
                COALESCE(fuel_type, 'Unknown') as fuel_type,
                COUNT(*) as count,
                CASE 
                    WHEN (SELECT COUNT(*) FROM tag_vehicle_cache WHERE fuel_type IS NOT NULL) > 0
                    THEN COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tag_vehicle_cache WHERE fuel_type IS NOT NULL)
                    ELSE 0
                END as percentage
            FROM tag_vehicle_cache 
            WHERE fuel_type IS NOT NULL
            GROUP BY fuel_type
            ORDER BY count DESC
        """).fetchall()
        
        # Most common models
        top_models = db.execute("""
            SELECT 
                COALESCE(model_name, 'Unknown') as model_name,
                COUNT(*) as count,
                CASE 
                    WHEN (SELECT COUNT(*) FROM tag_vehicle_cache WHERE model_name IS NOT NULL) > 0
                    THEN COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tag_vehicle_cache WHERE model_name IS NOT NULL)
                    ELSE 0
                END as percentage
            FROM tag_vehicle_cache 
            WHERE model_name IS NOT NULL AND model_name != 'Unknown'
            GROUP BY model_name
            ORDER BY count DESC
            LIMIT 5
        """).fetchall()
        
        # Registration year analysis (extract from vehicle_number if possible)
        year_analysis = db.execute("""
            SELECT 
                '2020-2022' as year_range,
                COUNT(*) as count
            FROM tag_vehicle_cache 
            WHERE vehicle_number IS NOT NULL
        """).fetchone()
        
        demographics = {
            'fuel_types': [
                {
                    'type': row[0],
                    'count': row[1],
                    'percentage': round(row[2], 1)
                } for row in fuel_distribution
            ],
            'top_models': [
                {
                    'model': row[0],
                    'count': row[1],
                    'percentage': round(row[2], 1)
                } for row in top_models
            ],
            'year_analysis': {
                'range': year_analysis[0] if year_analysis else 'Unknown',
                'count': year_analysis[1] if year_analysis else 0
            }
        }
        
        return jsonify(demographics)
    except Exception as e:
        logging.error(f"Error in vehicle demographics: {e}")
        return jsonify({'error': str(e)}), 500

@pwa_dashboard_bp.route('/api/reader/<int:reader_id>/power', methods=['GET'])
def get_reader_power(reader_id):
    """Get RF power for a specific reader"""
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        db = get_db()
        reader = db.execute('SELECT reader_ip FROM readers WHERE id = ?', (reader_id,)).fetchone()
        if not reader:
            return jsonify({"error": "Reader not found"}), 404
        
        # Import the RFID device functionality
        from fastag.routes.api import RFIDDevice, strip_leading_zeros_ip
        
        reader_ip = strip_leading_zeros_ip(reader['reader_ip'])
        
        with RFIDDevice(reader_ip) as dev:
            rf_power = dev.get_rf_power()
            if rf_power is None:
                return jsonify({"error": "Failed to read RF Power"}), 500
            return jsonify({"reader_id": reader_id, "rf_power": rf_power})
            
    except Exception as e:
        logging.exception(f"Exception in GET reader power: {e}")
        return jsonify({"error": str(e)}), 500

@pwa_dashboard_bp.route('/api/reader/<int:reader_id>/power', methods=['POST'])
def set_reader_power(reader_id):
    """Set RF power for a specific reader"""
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json(force=False, silent=True) or {}
        new_rf = data.get('rf_power')
        
        if not isinstance(new_rf, int) or not (1 <= new_rf <= 30):
            return jsonify({"error": "Invalid RF power value. Must be between 1-30"}), 400
        
        db = get_db()
        reader = db.execute('SELECT reader_ip FROM readers WHERE id = ?', (reader_id,)).fetchone()
        if not reader:
            return jsonify({"error": "Reader not found"}), 404
        
        # Import the RFID device functionality
        from fastag.routes.api import RFIDDevice, strip_leading_zeros_ip
        
        reader_ip = strip_leading_zeros_ip(reader['reader_ip'])
        
        with RFIDDevice(reader_ip) as dev:
            result = dev.set_rf_power(new_rf)
            if not result["success"]:
                return jsonify({"error": "Failed to set RF Power on device"}), 500
            
            if result["confirmed"]:
                return jsonify({
                    "reader_id": reader_id, 
                    "rf_power": new_rf, 
                    "status": "success",
                    "message": f"RF Power set to {new_rf} successfully"
                })
            else:
                return jsonify({
                    "reader_id": reader_id,
                    "rf_power": result.get("rf_power"),
                    "status": "warning",
                    "message": f"RF Power may not have been set correctly. Current value: {result.get('rf_power')}"
                })
                
    except Exception as e:
        logging.exception(f"Exception in SET reader power: {e}")
        return jsonify({"error": str(e)}), 500 

@pwa_dashboard_bp.route('/api/vapid_public_key', methods=['GET'])
def get_vapid_public_key():
    return current_app.config['VAPID_PUBLIC_KEY'], 200, {'Content-Type': 'text/plain'}

@pwa_dashboard_bp.route('/api/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    subscription = data.get('subscription')
    if not subscription:
        return jsonify({'success': False, 'error': 'No subscription provided'}), 400
    
    # Get user information from session
    username = session.get('user', 'anonymous')
    
    # Get device information
    user_agent = request.headers.get('User-Agent', '')
    device_info = parse_user_agent(user_agent)
    ip_address = get_client_ip()
    
    # Store subscription in database
    db = get_db()
    try:
        # Check if subscription already exists
        existing = db.execute(
            'SELECT id FROM fcm_tokens WHERE subscription_endpoint = ?',
            (subscription.get('endpoint'),)
        ).fetchone()
        
        if existing:
            # Update existing subscription
            db.execute('''
                UPDATE fcm_tokens 
                SET username = ?, user_agent = ?, device_type = ?, browser = ?, os = ?, 
                    ip_address = ?, subscription_keys = ?, last_used = CURRENT_TIMESTAMP
                WHERE subscription_endpoint = ?
            ''', (
                username, user_agent, device_info['device_type'], device_info['browser'],
                device_info['os'], ip_address, json.dumps(subscription.get('keys', {})),
                subscription.get('endpoint')
            ))
        else:
            # Insert new subscription
            db.execute('''
                INSERT INTO fcm_tokens 
                (username, user_agent, device_type, browser, os, ip_address, 
                 subscription_endpoint, subscription_keys, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                username, user_agent, device_info['device_type'], device_info['browser'],
                device_info['os'], ip_address, subscription.get('endpoint'),
                json.dumps(subscription.get('keys', {}))
            ))
        
        db.commit()
        
        # Also maintain backward compatibility with JSON file
        subs_path = os.path.join(os.path.dirname(__file__), '../../push_subscriptions.json')
        try:
            if os.path.exists(subs_path):
                with open(subs_path, 'r') as f:
                    subs = json.load(f)
            else:
                subs = []
            
            # Check if subscription already exists
            sub_exists = any(sub.get('endpoint') == subscription.get('endpoint') for sub in subs)
            if not sub_exists:
                subs.append(subscription)
                with open(subs_path, 'w') as f:
                    json.dump(subs, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to update JSON file: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Subscription saved for {username} on {device_info["device_type"]} ({device_info["os"]})'
        })
    except Exception as e:
        db.rollback()
        logging.exception(f"Error saving subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@pwa_dashboard_bp.route('/api/save-fcm-token', methods=['POST'])
def save_fcm_token():
    data = request.get_json()
    token = data.get('token')
    if not token:
        return jsonify({'success': False, 'error': 'No token provided'}), 400
    
    # Get user information from session
    username = session.get('user', 'anonymous')
    
    # Get device information
    user_agent = request.headers.get('User-Agent', '')
    device_info = parse_user_agent(user_agent)
    ip_address = get_client_ip()
    
    # Store token in database
    db = get_db()
    try:
        # Check if token already exists
        existing = db.execute('SELECT id FROM fcm_tokens WHERE token = ?', (token,)).fetchone()
        
        if existing:
            # Update existing token
            db.execute('''
                UPDATE fcm_tokens 
                SET username = ?, user_agent = ?, device_type = ?, browser = ?, os = ?, 
                    ip_address = ?, last_used = CURRENT_TIMESTAMP
                WHERE token = ?
            ''', (
                username, user_agent, device_info['device_type'], device_info['browser'],
                device_info['os'], ip_address, token
            ))
        else:
            # Insert new token
            db.execute('''
                INSERT INTO fcm_tokens 
                (token, username, user_agent, device_type, browser, os, ip_address, 
                 created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                token, username, user_agent, device_info['device_type'], device_info['browser'],
                device_info['os'], ip_address
            ))
        
        db.commit()
        
        # Also maintain backward compatibility with JSON file
        tokens_path = os.path.join(os.path.dirname(__file__), '../../fcm_tokens.json')
        try:
            if os.path.exists(tokens_path):
                with open(tokens_path, 'r') as f:
                    tokens = json.load(f)
            else:
                tokens = []
            if token not in tokens:
                tokens.append(token)
                with open(tokens_path, 'w') as f:
                    json.dump(tokens, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to update JSON file: {e}")
        
        return jsonify({
            'success': True,
            'message': f'FCM token saved for {username} on {device_info["device_type"]} ({device_info["os"]})'
        })
    except Exception as e:
        db.rollback()
        logging.exception(f"Error saving FCM token: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 

@pwa_dashboard_bp.route('/api/fcm-tokens/stats', methods=['GET'])
def get_fcm_token_stats():
    """Get FCM token statistics"""
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    db = get_db()
    try:
        # Get overall statistics
        total_tokens = db.execute('SELECT COUNT(*) FROM fcm_tokens').fetchone()[0]
        active_tokens = db.execute('SELECT COUNT(*) FROM fcm_tokens WHERE is_active = 1').fetchone()[0]
        inactive_tokens = db.execute('SELECT COUNT(*) FROM fcm_tokens WHERE is_active = 0').fetchone()[0]
        
        # Get device type breakdown
        device_stats = db.execute('''
            SELECT device_type, COUNT(*) as count 
            FROM fcm_tokens 
            WHERE is_active = 1 
            GROUP BY device_type
        ''').fetchall()
        
        # Get OS breakdown
        os_stats = db.execute('''
            SELECT os, COUNT(*) as count 
            FROM fcm_tokens 
            WHERE is_active = 1 
            GROUP BY os
        ''').fetchall()
        
        # Get browser breakdown
        browser_stats = db.execute('''
            SELECT browser, COUNT(*) as count 
            FROM fcm_tokens 
            WHERE is_active = 1 
            GROUP BY browser
        ''').fetchall()
        
        # Get recent tokens (last 7 days)
        recent_tokens = db.execute('''
            SELECT username, device_type, os, browser, created_at 
            FROM fcm_tokens 
            WHERE is_active = 1 
            AND created_at >= datetime('now', '-7 days')
            ORDER BY created_at DESC
            LIMIT 10
        ''').fetchall()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_tokens': total_tokens,
                'active_tokens': active_tokens,
                'inactive_tokens': inactive_tokens,
                'device_types': [{'type': row[0], 'count': row[1]} for row in device_stats],
                'operating_systems': [{'os': row[0], 'count': row[1]} for row in os_stats],
                'browsers': [{'browser': row[0], 'count': row[1]} for row in browser_stats],
                'recent_tokens': [
                    {
                        'username': row[0],
                        'device_type': row[1],
                        'os': row[2],
                        'browser': row[3],
                        'created_at': row[4]
                    } for row in recent_tokens
                ]
            }
        })
    except Exception as e:
        logging.exception(f"Error getting FCM token stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 