from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from fastag.utils.db import get_db
import logging
import requests
from bs4 import BeautifulSoup

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