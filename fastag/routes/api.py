from flask import Blueprint, request, jsonify, current_app
from fastag.utils.db import get_db
import logging
import ctypes
import time
from fastag.utils.db import log_barrier_event

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

# Dummy mapping for demonstration; replace with your actual mapping
RFID_IPS = {1: '192.168.1.101', 2: '192.168.1.102'}

class RFIDDevice:
    def __init__(self, ip):
        self.ip = ip
        # self.lib = ... # Load your actual RFID library here
        pass
    def __enter__(self):
        # Connect to device
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Disconnect/cleanup
        pass
    def get_rf_power(self):
        value = ctypes.c_ubyte()
        # result = self.lib.SWNet_ReadDeviceOneParam(0xFF, 0x05, ctypes.byref(value))
        result = 1  # Simulate success
        value.value = 25  # Simulate value
        if result == 0:
            return None
        return int(value.value)
    def set_rf_power(self, new_rf):
        # result = self.lib.SWNet_SetDeviceOneParam(0xFF, 0x05, new_rf)
        result = 1  # Simulate success
        if result == 0:
            return False
        # Retry up to 5 times to confirm
        for _ in range(5):
            time.sleep(0.5)
            rf_power = self.get_rf_power()
            if rf_power == new_rf:
                return True
        return False

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

@api.route('/status', methods=['GET'])
def system_status():
    """
    Returns system status info (temperature, voltage, throttled, uptime, RAM, disk) as plain text and JSON.
    """
    try:
        from fastag.__init__ import get_rpi_system_info
        info_str = get_rpi_system_info()
        # Parse info_str into a dict for JSON
        # Example: "Temp: 46.7°C Normal | Volt: 0.8700V | Throttled: No issues | Uptime: up 5 minutes | RAM: 206Mi used / 1.8Gi total | Disk: 2.7G used / 15G total (20% full)"
        info_parts = [part.strip() for part in info_str.split('|')]
        info_dict = {}
        for part in info_parts:
            if ':' in part:
                key, value = part.split(':', 1)
                info_dict[key.strip()] = value.strip()
        return jsonify({
            "success": True,
            "info": info_dict,
            "info_str": info_str
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

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

@api.route('/barrier-control', methods=['POST'])
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

    # Only allow relays 1-3 for 3-relay hardware
    allowed_relays = [1, 2, 3]

    # Import relay controller from the app context
    relay_controller = current_app.relay_controller

    # Determine which relays to activate
    if relay_numbers is None or relay_numbers == 'all':
        relays_to_activate = allowed_relays
    else:
        relays_to_activate = [r for r in relay_numbers if r in allowed_relays]
        if not relays_to_activate:
            return jsonify({"success": False, "error": "No valid relay numbers provided"}), 400

    user = None
    if hasattr(request, 'user') and request.user:
        user = getattr(request, 'user', None)
    elif 'user' in getattr(request, 'cookies', {}):
        user = request.cookies.get('user')
    # Activate the relays
    for relay_num in relays_to_activate:
        relay_controller.turn_on(relay_num)
        log_barrier_event(
            relay_number=relay_num,
            action='opened',
            user=user,
            lane_id=None,
            lane_name=None,
            reader_id=None,
            reader_ip=None,
            device_id=None,
            source='api/barrier-control'
        )
    import time
    time.sleep(2)  # Keep relays on for 2 seconds
    for relay_num in relays_to_activate:
        relay_controller.turn_off(relay_num)
        log_barrier_event(
            relay_number=relay_num,
            action='closed',
            user=user,
            lane_id=None,
            lane_name=None,
            reader_id=None,
            reader_ip=None,
            device_id=None,
            source='api/barrier-control'
        )

    return jsonify({"success": True, "activated": relays_to_activate}), 200 

@api.route('/api/rfid/rfpower', methods=['GET', 'POST'])
def rfid_rfpower():
    """
    GET: /api/rfid/rfpower?reader=1 or 2
    POST: JSON {"reader": 1 or 2, "rf_power": 1-30}
    """
    if request.method == 'GET':
        reader = request.args.get('reader', type=int)
        if reader not in RFID_IPS:
            return jsonify({"error": "Invalid reader. Must be 1 or 2."}), 400
        try:
            with RFIDDevice(RFID_IPS[reader]) as dev:
                rf_power = dev.get_rf_power()
                if rf_power is None:
                    return jsonify({"error": "Failed to read RF Power."}), 500
                return jsonify({"reader": reader, "rf_power": rf_power})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == 'POST':
        data = request.get_json(force=True)
        reader = data.get('reader')
        new_rf = data.get('rf_power')
        if reader not in RFID_IPS or not isinstance(new_rf, int) or not (1 <= new_rf <= 30):
            return jsonify({"error": "Invalid input. 'reader' must be 1 or 2, 'rf_power' must be 1-30."}), 400
        try:
            with RFIDDevice(RFID_IPS[reader]) as dev:
                success = dev.set_rf_power(new_rf)
                if not success:
                    return jsonify({"error": "Failed to set or confirm RF Power."}), 500
                return jsonify({"reader": reader, "rf_power": new_rf, "status": "success"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500 

@api.route('/register_device', methods=['POST'])
def register_device():
    data = request.get_json()
    required = ['device_id', 'model', 'manufacturer', 'android_version']
    if not data or not all(k in data for k in required):
        return jsonify({
            "error": "Device registration failed: invalid parameters",
            "code": 400
        }), 400
    db = get_db()
    # Check if device already exists
    existing = db.execute('SELECT * FROM devices WHERE device_id=?', (data['device_id'],)).fetchone()
    if existing:
        return jsonify({"message": "Device registered for approval"}), 200
    db.execute('INSERT INTO devices (device_id, model, manufacturer, android_version, approved) VALUES (?, ?, ?, ?, 0)',
               (data['device_id'], data['model'], data['manufacturer'], data['android_version']))
    db.commit()
    return jsonify({"message": "Device registered for approval"}), 200

@api.route('/login', methods=['POST'])
def device_login():
    data = request.get_json()
    required = ['device_id', 'username', 'password']
    if not data or not all(k in data for k in required):
        return jsonify({
            "error": "Device login failed: invalid parameters",
            "code": 400
        }), 400
    db = get_db()
    device = db.execute('SELECT * FROM devices WHERE device_id=? AND username=? AND password=? AND approved=1',
                        (data['device_id'], data['username'], data['password'])).fetchone()
    if device:
        return jsonify({"success": True, "message": "Login successful", "service_ip": device['service_ip']}), 200
    else:
        return jsonify({"success": False, "message": "Invalid credentials or device not approved"}), 401 