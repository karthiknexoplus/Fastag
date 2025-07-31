from flask import Blueprint, request, jsonify, current_app
from fastag.utils.db import get_db
import logging
import ctypes
import time
import sqlite3
import json
import subprocess
import os
import platform
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

# Dummy mapping for demonstration; replace with your actual mapping
RFID_IPS = {1: '192.168.1.101', 2: '192.168.1.102'}

class RFIDDevice:
    def __init__(self, ip):
        self.ip = ip.encode()  # Ensure bytes
        self.port = 60000
        self.lib = ctypes.cdll.LoadLibrary('fastag/rfid/libSWNetClientApi.so')
        # Set argtypes/restype
        self.lib.SWNet_OpenDevice.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.lib.SWNet_OpenDevice.restype = ctypes.c_int
        self.lib.SWNet_ReadDeviceOneParam.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.POINTER(ctypes.c_ubyte)]
        self.lib.SWNet_ReadDeviceOneParam.restype = ctypes.c_int
        self.lib.SWNet_SetDeviceOneParam.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ubyte]
        self.lib.SWNet_SetDeviceOneParam.restype = ctypes.c_int
        self.lib.SWNet_CloseDevice.restype = ctypes.c_int

    def __enter__(self):
        logging.info(f"Opening device connection to {self.ip} on port {self.port}")
        # Open device connection
        if self.lib.SWNet_OpenDevice(self.ip, self.port) == 0:
            logging.error(f"Failed to open device {self.ip}")
            raise Exception("Failed to open device")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info(f"Closing device connection to {self.ip}")
        # Close device connection
        self.lib.SWNet_CloseDevice()

    def get_rf_power(self):
        logging.info(f"Attempting to get RF power for device {self.ip}")
        value = ctypes.c_ubyte()
        result = self.lib.SWNet_ReadDeviceOneParam(0xFF, 0x05, ctypes.byref(value))
        logging.info(f"SWNet_ReadDeviceOneParam result: {result}, value: {value.value}")
        if result == 0:
            logging.error("Failed to read RF Power from device")
            return None
        return int(value.value)

    def set_rf_power(self, new_rf):
        logging.info(f"Attempting to set RF power to {new_rf} for device {self.ip}")
        result = self.lib.SWNet_SetDeviceOneParam(0xFF, 0x05, new_rf)
        logging.info(f"SWNet_SetDeviceOneParam result: {result}")
        if result == 0:
            logging.error("Failed to set RF Power on device")
            return {"success": False, "confirmed": False, "rf_power": None}
        last_rf = None
        for _ in range(10):
            time.sleep(1)
            rf_power = self.get_rf_power()
            last_rf = rf_power
            if rf_power == new_rf:
                logging.info(f"Confirmed RF Power set to {new_rf} for device {self.ip}")
                return {"success": True, "confirmed": True, "rf_power": rf_power}
        logging.warning(f"Set command succeeded but failed to confirm RF Power set to {new_rf} for device {self.ip}. Last read: {last_rf}")
        return {"success": True, "confirmed": False, "rf_power": last_rf}

def strip_leading_zeros_ip(ip):
    # Split by '.', remove leading zeros from each octet, and rejoin
    return '.'.join(str(int(part)) for part in ip.split('.'))

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

    # Control the relays based on action
    if action == 'open':
        # Activate the relays (turn on, wait, turn off)
        for relay_num in relays_to_activate:
            relay_controller.turn_on(relay_num)
        import time
        time.sleep(2)  # Keep relays on for 2 seconds
        for relay_num in relays_to_activate:
            relay_controller.turn_off(relay_num)
    elif action == 'close':
        # For close action, just ensure relays are off
        for relay_num in relays_to_activate:
            relay_controller.turn_off(relay_num)

    return jsonify({"success": True, "activated": relays_to_activate}), 200 

@api.route('/rfid/rfpower', methods=['GET', 'POST'])
def rfid_rfpower():
    logging.info(f"/api/rfid/rfpower endpoint called. Method: {request.method}, Args: {request.args}, JSON: {request.get_json(force=False, silent=True)}")
    if request.method == 'GET':
        reader_id = request.args.get('reader', type=int)
        if not reader_id:
            return jsonify({"error": "Missing or invalid reader_id."}), 400
        row = get_db().execute('SELECT reader_ip FROM readers WHERE id = ?', (reader_id,)).fetchone()
        if not row:
            return jsonify({"error": "Reader not found."}), 404
        reader_ip = strip_leading_zeros_ip(row['reader_ip'])
        try:
            with RFIDDevice(reader_ip) as dev:
                rf_power = dev.get_rf_power()
                if rf_power is None:
                    return jsonify({"error": "Failed to read RF Power."}), 500
                return jsonify({"reader_id": reader_id, "rf_power": rf_power})
        except Exception as e:
            logging.exception(f"Exception in GET /api/rfid/rfpower: {e}")
            return jsonify({"error": str(e)}), 500
    elif request.method == 'POST':
        data = request.get_json(force=False, silent=True) or {}
        reader_id = data.get('reader_id')
        new_rf = data.get('rf_power')
        logging.info(f"POST /api/rfid/rfpower received: data={data}, reader_id={reader_id} (type {type(reader_id)}), rf_power={new_rf} (type {type(new_rf)})")
        if not reader_id or not isinstance(new_rf, int) or not (1 <= new_rf <= 30):
            return jsonify({"error": "Invalid input. 'reader_id' and 'rf_power' (1-30) required."}), 400
        row = get_db().execute('SELECT reader_ip FROM readers WHERE id = ?', (reader_id,)).fetchone()
        if not row:
            return jsonify({"error": "Reader not found."}), 404
        reader_ip = strip_leading_zeros_ip(row['reader_ip'])
        try:
            with RFIDDevice(reader_ip) as dev:
                result = dev.set_rf_power(new_rf)
                if not result["success"]:
                    return jsonify({"error": "Failed to set RF Power on device."}), 500
                if result["confirmed"]:
                    return jsonify({"reader_id": reader_id, "rf_power": new_rf, "status": "success"})
                else:
                    return jsonify({
                        "reader_id": reader_id,
                        "rf_power": result["rf_power"],
                        "requested_rf_power": new_rf,
                        "status": "warning",
                        "warning": "Set command succeeded but could not confirm new value within 10 seconds. Please check manually."
                    }), 200
        except Exception as e:
            logging.exception(f"Exception in POST /api/rfid/rfpower: {e}")
            return jsonify({"error": str(e)}), 500 

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

@api.route('/all_data', methods=['GET'])
def get_all_data():
    """
    Returns all locations, lanes, readers, and kyc_users in a single response.
    """
    try:
        db = get_db()
        locations = db.execute('SELECT * FROM locations').fetchall()
        lanes = db.execute('SELECT * FROM lanes').fetchall()
        readers = db.execute('SELECT * FROM readers').fetchall()
        kyc_users = db.execute('SELECT * FROM kyc_users').fetchall()

        locations_list = [dict(l) for l in locations]
        lanes_list = [dict(l) for l in lanes]
        readers_list = [dict(r) for r in readers]
        kyc_users_list = [dict(u) for u in kyc_users]

        return jsonify({
            'success': True,
            'locations': locations_list,
            'lanes': lanes_list,
            'readers': readers_list,
            'kyc_users': kyc_users_list
        }), 200
    except Exception as e:
        logger.error(f"Error in /api/all_data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 

@api.route('/relay-status', methods=['GET'])
def relay_status():
    """
    Returns the real-time status of the 3 relays (GPIO 26, 20, 21) as ON/OFF.
    """
    try:
        relay_controller = current_app.relay_controller
        pins = relay_controller.pins  # [26, 20, 21]
        try:
            import RPi.GPIO as GPIO
            GPIO_AVAILABLE = True
        except ImportError:
            GPIO_AVAILABLE = False
        status = {}
        if GPIO_AVAILABLE:
            for idx, pin in enumerate(pins):
                # Active-low: LOW (0) = ON, HIGH (1) = OFF
                value = GPIO.input(pin)
                status[f"relay{idx+1}"] = "ON" if value == 0 else "OFF"
        else:
            # If not on Pi, simulate status
            for idx in range(3):
                status[f"relay{idx+1}"] = "UNKNOWN"
        return jsonify({"success": True, "status": status}), 200
    except Exception as e:
        logger.error(f"Error in /api/relay-status: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500 

@api.route('/relay/<int:relay_number>/<action>', methods=['POST'])
def relay_control(relay_number, action):
    """
    Control individual relays. 
    relay_number: 1, 2, or 3
    action: 'on' or 'off'
    """
    try:
        if relay_number not in [1, 2, 3]:
            return jsonify({"success": False, "error": "Invalid relay number. Must be 1, 2, or 3."}), 400
        
        if action not in ['on', 'off']:
            return jsonify({"success": False, "error": "Invalid action. Must be 'on' or 'off'."}), 400
        
        relay_controller = current_app.relay_controller
        
        if action == 'on':
            success = relay_controller.turn_on(relay_number)
        else:  # action == 'off'
            success = relay_controller.turn_off(relay_number)
        
        if success:
            return jsonify({
                "success": True, 
                "relay": relay_number, 
                "action": action,
                "message": f"Relay {relay_number} turned {action.upper()}"
            }), 200
        else:
            return jsonify({
                "success": False, 
                "error": f"Failed to turn {action} relay {relay_number}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in /api/relay/{relay_number}/{action}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@api.route('/readers', methods=['GET'])
def get_readers():
    """Get all readers with enhanced status and activity information"""
    try:
        db = get_db()
        readers = db.execute('''
            SELECT r.id, r.reader_ip, r.type, r.mac_address, l.lane_name, loc.name as location_name
            FROM readers r
            JOIN lanes l ON r.lane_id = l.id
            JOIN locations loc ON l.location_id = loc.id
            ORDER BY r.id
        ''').fetchall()
        
        readers_list = []
        for reader in readers:
            reader_id = reader['id']
            
            # Get activity data for last 24 hours
            activity_data = db.execute("""
                SELECT 
                    COUNT(*) as total_events,
                    MAX(al.timestamp) as last_event_time
                FROM access_logs al
                WHERE al.reader_id = ? AND al.timestamp >= datetime('now', '-24 hours')
            """, (reader_id,)).fetchone()
            
            total_events = activity_data[0] or 0
            last_event_time = activity_data[1]
            
            # Improved status logic
            if total_events > 0:
                status = "online"
            else:
                # Check if there's any activity in last 7 days
                week_activity = db.execute("""
                    SELECT COUNT(*) FROM access_logs 
                    WHERE reader_id = ? AND timestamp >= datetime('now', '-7 days')
                """, (reader_id,)).fetchone()[0]
                
                if week_activity > 0:
                    status = "idle"
                else:
                    status = "offline"
            
            # Calculate time since last event
            if last_event_time:
                from datetime import datetime, timezone
                last_event_dt = datetime.strptime(last_event_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
                time_diff = now_utc - last_event_dt
                minutes_ago = int(time_diff.total_seconds() / 60)
                hours_ago = int(time_diff.total_seconds() / 3600)
                days_ago = int(time_diff.total_seconds() / 86400)
                
                if minutes_ago < 60:
                    last_event_str = f"{minutes_ago} min ago"
                elif hours_ago < 24:
                    last_event_str = f"{hours_ago} hours ago"
                else:
                    last_event_str = f"{days_ago} days ago"
            else:
                last_event_str = "No events yet"
            
            reader_dict = {
                'id': reader['id'],
                'reader_ip': reader['reader_ip'],
                'type': reader['type'],
                'mac_address': reader['mac_address'],
                'lane_name': reader['lane_name'],
                'location_name': reader['location_name'],
                'status': status,
                'last_event': last_event_str,
                'events_24h': total_events
            }
            readers_list.append(reader_dict)
        
        return jsonify({'success': True, 'readers': readers_list})
    except Exception as e:
        logging.exception(f"Error getting readers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/relay/all/<action>', methods=['POST'])
def relay_control_all(action):
    """
    Control all relays at once.
    action: 'on' or 'off'
    """
    try:
        if action not in ['on', 'off']:
            return jsonify({"success": False, "error": "Invalid action. Must be 'on' or 'off'."}), 400
        
        relay_controller = current_app.relay_controller
        results = []
        
        for relay_num in [1, 2, 3]:
            if action == 'on':
                success = relay_controller.turn_on(relay_num)
            else:  # action == 'off'
                success = relay_controller.turn_off(relay_num)
            results.append({"relay": relay_num, "success": success})
        
        all_success = all(result["success"] for result in results)
        
        return jsonify({
            "success": all_success,
            "action": action,
            "results": results,
            "message": f"All relays turned {action.upper()}" if all_success else "Some relays failed to turn " + action.upper()
        }), 200 if all_success else 500
            
    except Exception as e:
        logger.error(f"Error in /api/relay/all/{action}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500 

@api.route('/fcm-tokens', methods=['GET'])
def get_fcm_tokens():
    """Get all FCM tokens for push notification users"""
    try:
        db = get_db()
        
        # Get FCM tokens with user information based on actual table structure
        rows = db.execute('''
            SELECT 
                ft.id,
                ft.token,
                ft.username,
                ft.device_type,
                ft.browser,
                ft.os,
                ft.created_at,
                ft.last_used,
                ft.is_active,
                ku.name,
                ku.contact_number as contact
            FROM fcm_tokens ft
            LEFT JOIN kyc_users ku ON ku.contact_number = ft.username
            WHERE ft.is_active = 1
            ORDER BY ft.created_at DESC
        ''').fetchall()
        
        tokens = []
        for row in rows:
            # Extract user info from username if it's a dictionary string
            username = row[2]
            user_name = row[9] or 'Unknown User'
            contact = row[10] or 'N/A'
            
            # If username is a dictionary string, try to extract info
            if username and username.startswith('{') and username.endswith('}'):
                try:
                    import ast
                    user_dict = ast.literal_eval(username)
                    if isinstance(user_dict, dict):
                        user_name = user_dict.get('kyc_user_name', user_name)
                        contact = user_dict.get('kyc_user_contact', contact)
                except:
                    pass
            
            tokens.append({
                'id': row[0],
                'fcm_token': row[1],
                'username': username,
                'device_type': row[3] or 'Unknown',
                'browser': row[4] or 'Unknown',
                'os': row[5] or 'Unknown',
                'created_at': row[6],
                'last_active': row[7],
                'status': 'active' if row[8] else 'inactive',
                'name': user_name,
                'contact': contact
            })
        
        return jsonify({
            'success': True,
            'tokens': tokens
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/restart-controller', methods=['POST'])
def restart_controller():
    """Restart the controller (reboot system)"""
    try:
        logger.info("Controller restart requested")
        
        # Check if running as root or has sudo privileges
        try:
            # Test sudo access
            test_result = subprocess.run(['sudo', '-n', 'true'], capture_output=True, text=True, timeout=5)
            if test_result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': 'Insufficient privileges to restart controller'
                }), 403
        except Exception as e:
            logger.error(f"Error checking sudo privileges: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Unable to verify system privileges'
            }), 500
        
        # Execute sudo reboot command
        result = subprocess.run(['sudo', 'reboot'], capture_output=True, text=True, timeout=30)
        
        logger.info("Controller restart command executed successfully")
        return jsonify({
            'success': True,
            'message': 'Controller restart initiated'
        })
        
    except subprocess.TimeoutExpired:
        logger.warning("Controller restart command timed out")
        return jsonify({
            'success': True,
            'message': 'Controller restart initiated (timeout)'
        })
    except Exception as e:
        logger.error(f"Error in restart-controller endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/restart-application', methods=['POST'])
def restart_application():
    """Restart the Fastag application service"""
    try:
        # Execute sudo systemctl restart fastag command
        result = subprocess.run(['sudo', 'systemctl', 'restart', 'fastag'], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Application restart initiated'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to restart application: {result.stderr}'
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': True,
            'message': 'Application restart initiated (timeout)'
        })
    except Exception as e:
        logger.error(f"Error in restart-application endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/restart-readers', methods=['POST'])
def restart_readers():
    """Restart the RFID readers service"""
    try:
        # Execute sudo systemctl restart rfid_readers.service command
        result = subprocess.run(['sudo', 'systemctl', 'restart', 'rfid_readers.service'], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'RFID readers restart initiated'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to restart readers: {result.stderr}'
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': True,
            'message': 'RFID readers restart initiated (timeout)'
        })
    except Exception as e:
        logger.error(f"Error in restart-readers endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/network-info', methods=['GET'])
def get_network_info():
    """Get network interface information using ifconfig/ipconfig"""
    try:
        interfaces = []
        
        if platform.system() == "Linux":
            # Use ifconfig command for Linux/Raspberry Pi
            ifconfig_paths = ['/sbin/ifconfig', '/usr/sbin/ifconfig', 'ifconfig']
            ifconfig_found = None
            
            # Find ifconfig executable
            for path in ifconfig_paths:
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        ifconfig_found = path
                        break
                except:
                    continue
            
            if ifconfig_found:
                try:
                    result = subprocess.run([ifconfig_found], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        current_interface = None
                        for line in result.stdout.split('\n'):
                            line = line.strip()
                            if line and not line.startswith('lo:'):  # Skip loopback
                                if ':' in line and not line.startswith(' '):
                                    # Interface name
                                    current_interface = line.split(':')[0].strip()
                                    interfaces.append({
                                        'name': current_interface,
                                        'ip': 'N/A',
                                        'mac': 'N/A',
                                        'status': 'UP'
                                    })
                                elif line.startswith('inet ') and current_interface:
                                    # IP address
                                    ip = line.split()[1]
                                    for iface in interfaces:
                                        if iface['name'] == current_interface:
                                            iface['ip'] = ip
                                            break
                                elif line.startswith('ether ') and current_interface:
                                    # MAC address
                                    mac = line.split()[1]
                                    for iface in interfaces:
                                        if iface['name'] == current_interface:
                                            iface['mac'] = mac
                                            break
                except subprocess.TimeoutExpired:
                    logger.error("Timeout getting network info")
                except Exception as e:
                    logger.error(f"Error getting network info: {e}")
            else:
                # Fallback: try to get network info from /proc/net/dev and /sys/class/net
                try:
                    # Read /proc/net/dev for interface names
                    with open('/proc/net/dev', 'r') as f:
                        lines = f.readlines()[2:]  # Skip header lines
                        for line in lines:
                            if ':' in line:
                                interface_name = line.split(':')[0].strip()
                                if interface_name not in ['lo']:  # Skip loopback
                                    interfaces.append({
                                        'name': interface_name,
                                        'ip': 'N/A',
                                        'mac': 'N/A',
                                        'status': 'UP'
                                    })
                    
                    # Try to get IP addresses using hostname
                    try:
                        import socket
                        hostname = socket.gethostname()
                        ip = socket.gethostbyname(hostname)
                        if interfaces:
                            interfaces[0]['ip'] = ip
                    except:
                        pass
                        
                except Exception as e:
                    logger.error(f"Error in fallback network info: {e}")
                
        elif platform.system() == "Windows":
            # Use ipconfig for Windows
            try:
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    current_interface = None
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('IPv6'):
                            if 'adapter' in line.lower() and ':' in line:
                                # Interface name
                                current_interface = line.split(':')[0].strip()
                                interfaces.append({
                                    'name': current_interface,
                                    'ip': 'N/A',
                                    'mac': 'N/A',
                                    'status': 'UP'
                                })
                            elif 'IPv4' in line and current_interface:
                                # IP address
                                ip = line.split(':')[1].strip()
                                for iface in interfaces:
                                    if iface['name'] == current_interface:
                                        iface['ip'] = ip
                                        break
                            elif 'Physical Address' in line and current_interface:
                                # MAC address
                                mac = line.split(':')[1].strip()
                                for iface in interfaces:
                                    if iface['name'] == current_interface:
                                        iface['mac'] = mac
                                        break
            except subprocess.TimeoutExpired:
                logger.error("Timeout getting network info")
            except Exception as e:
                logger.error(f"Error getting network info: {e}")
        
        # Filter out interfaces without IP addresses
        interfaces = [iface for iface in interfaces if iface['ip'] != 'N/A']
        
        return jsonify({
            'success': True,
            'interfaces': interfaces
        })
        
    except Exception as e:
        logger.error(f"Error in network-info endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/database-info', methods=['GET'])
def get_database_info():
    """Get database file information"""
    try:
        # Use the correct database path for RPi
        db_path = '/home/ubuntu/Fastag/instance/fastag.db'
        
        if os.path.exists(db_path):
            # Get file size
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / (1024 * 1024)
            
            # Get last modified time
            mtime = os.path.getmtime(db_path)
            last_modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({
                'success': True,
                'db_file': db_path,
                'db_size': f"{size_mb:.2f} MB",
                'last_modified': last_modified
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Database file not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error in database-info endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/download-database', methods=['GET'])
def download_database():
    """Download database file"""
    try:
        from flask import send_file
        # Use the correct database path for RPi
        db_path = '/home/ubuntu/Fastag/instance/fastag.db'
        
        if os.path.exists(db_path):
            return send_file(
                db_path,
                as_attachment=True,
                download_name=f'fastag_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Database file not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error in download-database endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 