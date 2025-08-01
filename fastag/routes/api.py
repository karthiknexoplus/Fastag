from flask import Blueprint, request, jsonify, current_app
from fastag.utils.db import get_db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

@api.route('/device/lookup', methods=['POST'])
def device_lookup():
    """
    API endpoint for external devices to lookup their configuration
    based on MAC address.
    
    Expected JSON payload:
    {
        "mac_address": "00:1A:2B:3C:4D:5E"
    }
    
    Returns:
    {
        "success": true,
        "data": [
            {
                "reader_id": 1,
                "mac_address": "00:1A:2B:3C:4D:5E",
                "reader_ip": "192.168.1.100",
                "type": "entry",
                "lane": {
                    "id": 1,
                    "lane_name": "Main Entry",
                    "location": {
                        "id": 1,
                        "name": "Central Parking",
                        "site_id": "CP001"
                    }
                }
            }
        ]
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        mac_address = data.get('mac_address')
        
        if not mac_address:
            return jsonify({
                "success": False,
                "error": "MAC address is required"
            }), 400
        
        # Clean MAC address (remove colons, dashes, etc.)
        mac_address = mac_address.replace(':', '').replace('-', '').replace('.', '').upper()
        
        # Accept any even-length MAC address (e.g., 8 or 12 hex digits)
        if len(mac_address) % 2 != 0 or len(mac_address) < 4:
            return jsonify({
                "success": False,
                "error": "Invalid MAC address format. Must be even number of hex digits (at least 4)",
                "mac_address": mac_address
            }), 400
        
        # Add colons back for database lookup
        formatted_mac = ':'.join([mac_address[i:i+2] for i in range(0, len(mac_address), 2)])
        
        logger.info(f"Looking up device with MAC: {formatted_mac}")
        
        # Query database for all readers with this MAC address
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT 
                r.id as reader_id,
                r.mac_address,
                r.reader_ip,
                r.type,
                l.id as lane_id,
                l.lane_name,
                loc.id as location_id,
                loc.name as location_name,
                loc.site_id
            FROM readers r
            JOIN lanes l ON r.lane_id = l.id
            JOIN locations loc ON l.location_id = loc.id
            WHERE r.mac_address = ?
        """, (formatted_mac,))
        
        reader_rows = cursor.fetchall()
        
        if not reader_rows:
            logger.warning(f"No reader found for MAC: {formatted_mac}")
            return jsonify({
                "success": False,
                "error": "Device not found",
                "mac_address": formatted_mac
            }), 404
        
        # Format response as a list
        response_data = []
        for reader_data in reader_rows:
            response_data.append({
                "reader_id": reader_data['reader_id'],
                "mac_address": reader_data['mac_address'],
                "reader_ip": reader_data['reader_ip'],
                "type": reader_data['type'],
                "lane": {
                    "id": reader_data['lane_id'],
                    "lane_name": reader_data['lane_name'],
                    "location": {
                        "id": reader_data['location_id'],
                        "name": reader_data['location_name'],
                        "site_id": reader_data['site_id']
                    }
                }
            })
        
        logger.info(f"Found devices: {response_data}")
        
        return jsonify({
            "success": True,
            "data": response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error in device lookup: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@api.route('/device/status', methods=['GET'])
def device_status():
    """
    Health check endpoint for external devices
    """
    return jsonify({
        "success": True,
        "status": "online",
        "service": "FASTag Device Lookup API"
    }), 200

@api.route('/device/register', methods=['POST'])
def device_register():
    """
    Optional endpoint for devices to register themselves
    (Could be used for device management in the future)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        mac_address = data.get('mac_address')
        device_type = data.get('type', 'unknown')
        
        if not mac_address:
            return jsonify({
                "success": False,
                "error": "MAC address is required"
            }), 400
        
        # Clean MAC address
        mac_address = mac_address.replace(':', '').replace('-', '').replace('.', '').upper()
        
        # Accept any even-length MAC address (e.g., 8 or 12 hex digits)
        if len(mac_address) % 2 != 0 or len(mac_address) < 4:
            return jsonify({
                "success": False,
                "error": "Invalid MAC address format. Must be even number of hex digits (at least 4)",
                "mac_address": mac_address
            }), 400
        
        formatted_mac = ':'.join([mac_address[i:i+2] for i in range(0, len(mac_address), 2)])
        
        logger.info(f"Device registration attempt: {formatted_mac} ({device_type})")
        
        # Check if device already exists
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("SELECT id FROM readers WHERE mac_address = ?", (formatted_mac,))
        existing = cursor.fetchone()
        
        if existing:
            return jsonify({
                "success": True,
                "message": "Device already registered",
                "mac_address": formatted_mac
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Device not found in system. Please register through admin panel first.",
                "mac_address": formatted_mac
            }), 404
            
    except Exception as e:
        logger.error(f"Error in device registration: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500 

@api.route('/api/barrier-control', methods=['POST'])
def barrier_control():
    """
    Control the barrier relays. Accepts JSON:
    {
        "action": "open",
        "relay_numbers": [1, 2]  # optional, if omitted, all relays are activated
    }
    """
    data = request.get_json()
    action = data.get('action')
    relay_numbers = data.get('relay_numbers', None)

    if action != 'open':
        return jsonify({"success": False, "error": "Unsupported action"}), 400

    # Get the number of readers from the database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM readers")
    total_relays = cursor.fetchone()[0]

    # Import relay controller from the app context
    relay_controller = getattr(current_app, 'relay_controller', None)
    if relay_controller is None:
        from fastag.rfid.rfid_service import RelayController
        relay_controller = RelayController()
        setattr(current_app, 'relay_controller', relay_controller)

    # Determine which relays to activate
    if relay_numbers is None or relay_numbers == 'all':
        relays_to_activate = list(range(1, total_relays + 1))
    else:
        relays_to_activate = relay_numbers

    # Activate the relays
    for relay_num in relays_to_activate:
        relay_controller.turn_on(relay_num)
    import time
    time.sleep(2)  # Keep relays on for 2 seconds
    for relay_num in relays_to_activate:
        relay_controller.turn_off(relay_num)

    return jsonify({"success": True, "activated": relays_to_activate}), 200 