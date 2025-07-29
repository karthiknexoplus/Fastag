from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from fastag.utils.db import get_db
import logging

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