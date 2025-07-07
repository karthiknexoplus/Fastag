#!/usr/bin/python
# -*- coding: UTF-8 -*-
import ctypes
import time
import platform
import threading
import sys
import os
from ctypes import *
import sqlite3
import json
import logging
import queue
from concurrent.futures import ThreadPoolExecutor
import asyncio
import requests
from collections import defaultdict
from datetime import datetime

# Try to import RPi.GPIO, but handle gracefully if not available
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("RPi.GPIO not available - running in simulation mode")

# Add the current directory to Python path to import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use the correct database path that matches deploy.sh
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'fastag.db'))
print('Using DB:', DB_PATH)

# Setup logging
def setup_logging():
    """Setup comprehensive logging for RFID service"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Custom colored formatter
    class ColoredFormatter(logging.Formatter):
        """Custom formatter with colors"""
        
        # Color codes
        COLORS = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
            'RESET': '\033[0m'      # Reset
        }
        
        def format(self, record):
            # Add color to levelname
            if record.levelname in self.COLORS:
                record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            
            # Add color to message based on content
            if '✓' in record.getMessage():
                record.msg = f"\033[32m{record.msg}\033[0m"  # Green for success
            elif '✗' in record.getMessage():
                record.msg = f"\033[31m{record.msg}\033[0m"  # Red for errors
            elif '⚠️' in record.getMessage():
                record.msg = f"\033[33m{record.msg}\033[0m"  # Yellow for warnings
            elif '💓' in record.getMessage():
                record.msg = f"\033[35m{record.msg}\033[0m"  # Magenta for heartbeat
            elif '🚗' in record.getMessage():
                record.msg = f"\033[36m{record.msg}\033[0m"  # Cyan for vehicle events
            elif '🔑' in record.getMessage():
                record.msg = f"\033[34m{record.msg}\033[0m"  # Blue for access events
            
            return super().format(record)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)  # Changed from INFO to WARNING to reduce log overhead
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler (no colors in file)
    file_handler = logging.FileHandler('logs/rfid.log')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(file_formatter)
    try:
        os.chmod('logs/rfid.log', 0o664)
    except Exception as e:
        pass  # Ignore if file does not exist yet or permission denied
    
    # Console handler (with colors)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(colored_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_reader_type_from_db(reader_id, db_path):
    """Get reader type from database"""
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT type FROM readers WHERE id = ?", (reader_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 'unknown'
    except Exception as e:
        return 'unknown'

logger = setup_logging()

# Try to import Flask components, but handle gracefully if not available
try:
    from app import app, db, VehicleUser, AccessLog, Lane, Device
    from fastag.utils.db import get_db
    # Patch SQLAlchemy URI to use absolute path
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
    FLASK_AVAILABLE = True
    logger.info("Flask components imported successfully")
except ImportError as e:
    logger.warning(f"Flask components not available: {e}")
    logger.info("RFID service will run in standalone mode")
    FLASK_AVAILABLE = False
    # Create dummy classes for standalone mode
    class DummyApp:
        def app_context(self):
            return DummyContext()
    
    class DummyContext:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    
    class DummyDB:
        def session(self):
            return DummySession()
    
    class DummySession:
        def add(self, obj):
            pass
        def commit(self):
            pass
        def rollback(self):
            pass
    
    class DummyUser:
        def __init__(self):
            self.id = None
            self.name = "Unknown"
            self.vehicle_number = "Unknown"
    
    class DummyAccessLog:
        def __init__(self, **kwargs):
            pass
    
    # Create dummy instances
    app = DummyApp()
    db = DummyDB()
    VehicleUser = type('VehicleUser', (), {})
    AccessLog = DummyAccessLog
    Lane = type('Lane', (), {})
    Device = type('Device', (), {})

    # Standalone mode: real sqlite3 access
    def verify_tag_in_db_sqlite(tag_id):
        import sqlite3
        try:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            c = conn.cursor()
            # Use kyc_users table (current project schema)
            c.execute("SELECT id, name, vehicle_number FROM kyc_users WHERE fastag_id=?", (tag_id,))
            row = c.fetchone()
            conn.close()
            if row:
                user_id, name, vehicle_number = row
                return {'found': True, 'user': {'id': user_id, 'name': name, 'vehicle_number': vehicle_number}, 'message': f"Access granted for vehicle {vehicle_number} - {name}"}
            else:
                return {'found': False, 'message': f"Tag {tag_id} not found in database"}
        except Exception as e:
            logger.error(f"✗ Database error: {str(e)}")
            return {'found': False, 'message': f"Database error: {str(e)}"}

    def log_access_sqlite(tag_id, user, status, reader_id, lane_id, device_id):
        import sqlite3
        try:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            c = conn.cursor()
            # Use current project's access_logs table schema
            c.execute("""
                INSERT INTO access_logs (tag_id, reader_id, lane_id, access_result, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tag_id, reader_id, lane_id, status, None, datetime.now()))
            conn.commit()
            conn.close()
            logger.debug(f"✓ Access log created: {status} for tag {tag_id}")
        except Exception as e:
            logger.error(f"✗ Error logging access: {str(e)}")

class RFIDReader:
    def __init__(self, ip_address, reader_id, lane_id, device_id, dll_path="./libSWNetClientApi.so", db_path=None):
        self.ip_address = ip_address
        self.reader_id = reader_id
        self.lane_id = lane_id
        self.device_id = device_id
        self.dll_path = dll_path
        self.objdll = None
        self.is_connected = False
        self.running = False
        self.last_heartbeat = time.time()
        self.connection_attempts = 0
        self.max_connection_attempts = 5
        self.last_connection_check = time.time()
        self.connection_check_interval = 30  # Increased from 10 to 30 seconds
        self.buffer_clear_threshold = 5  # Reduced from 10 to 5
        # --- Per-reader logging ---
        if db_path is not None:
            reader_type = get_reader_type_from_db(reader_id, db_path)
            log_path = os.path.join('logs', f'{reader_type}_reader.log')
            self.logger = setup_logging(log_path)
            self.logger.info(f"Per-reader log started for Reader {reader_id} (type: {reader_type})")
        else:
            self.logger = logger  # fallback to global logger
        self.logger.info(f"Reader {reader_id} initialized - IP: {ip_address}, Lane: {lane_id}, Device: {device_id}, DLL: {dll_path}")
        
    def connect(self):
        try:
            # Validate IP address
            if not self.ip_address:
                self.logger.error(f"Reader {self.reader_id}: ✗ IP address is None or empty")
                self.connection_attempts += 1
                return False
            
            # Check if library file exists
            if not os.path.exists(self.dll_path):
                self.logger.error(f"Reader {self.reader_id}: ✗ Library file not found: {self.dll_path}")
                self.logger.error(f"Reader {self.reader_id}: Current directory: {os.getcwd()}")
                self.connection_attempts += 1
                return False
            
            self.logger.info(f"Reader {self.reader_id}: Loading library {self.dll_path} ...")
            self.objdll = cdll.LoadLibrary(self.dll_path)
            self.logger.info(f"Reader {self.reader_id}: ✓ Library loaded successfully")
            
            # SKIP network connectivity test (port 80/ping)
            self.logger.info(f"Reader {self.reader_id}: Skipping network connectivity test, proceeding to open device...")
            
            # Connect using the exact method from working example
            self.logger.info(f"Reader {self.reader_id}: Connecting to {self.ip_address} with 60000ms timeout...")
            result = self.objdll.SWNet_OpenDevice(self.ip_address.encode(), 60000)
            
            self.logger.info(f"Reader {self.reader_id}: Connection result: {result}")
            
            if result == 1:
                self.logger.info(f"Reader {self.reader_id}: ✓ Connected to {self.ip_address}")
                self.logger.info(f"Reader {self.reader_id}: Clearing tag buffer...")
                self.objdll.SWNet_ClearTagBuf()
                self.logger.info(f"Reader {self.reader_id}: ✓ Tag buffer cleared")
                self.is_connected = True
                self.connection_attempts = 0
                self.last_connection_check = time.time()  # Reset connection check timer
                return True
            else:
                self.logger.error(f"Reader {self.reader_id}: ✗ Connection failed with return code {result}")
                self.logger.error(f"Reader {self.reader_id}: This usually means the device is not responding or not in network mode")
                self.connection_attempts += 1
                self.is_connected = False
                return False
            
        except Exception as e:
            self.logger.error(f"Reader {self.reader_id}: ✗ Connection error: {str(e)}")
            self.connection_attempts += 1
            self.is_connected = False
            return False
    
    def test_network_connectivity(self):
        """Test basic network connectivity to the reader IP"""
        try:
            import socket
            import subprocess
            
            # Test 1: Socket connection to port 80
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((self.ip_address, 80))
                sock.close()
                
                if result == 0:
                    self.logger.debug(f"Reader {self.reader_id}: Socket connection successful")
                else:
                    self.logger.warning(f"Reader {self.reader_id}: Socket connection failed (error code: {result})")
                    return False
            except Exception as e:
                self.logger.warning(f"Reader {self.reader_id}: Socket test failed: {e}")
                return False
            
            # Test 2: Ping
            try:
                ping_result = subprocess.run(['ping', '-c', '2', '-W', '3', self.ip_address], 
                                           capture_output=True, text=True, timeout=10)
                if ping_result.returncode == 0:
                    self.logger.debug(f"Reader {self.reader_id}: Ping successful")
                else:
                    self.logger.warning(f"Reader {self.reader_id}: Ping failed")
                    return False
            except Exception as e:
                self.logger.warning(f"Reader {self.reader_id}: Ping test failed: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Reader {self.reader_id}: Network connectivity test failed: {e}")
            return False
    
    def reconnect(self):
        """Attempt to reconnect to the reader"""
        if self.connection_attempts < self.max_connection_attempts:
            self.logger.info(f"Reader {self.reader_id}: Attempting to reconnect (attempt {self.connection_attempts + 1}/{self.max_connection_attempts})...")
            
            # Disconnect first if connected
            if self.is_connected:
                self.disconnect()
            
            # Wait a moment before reconnecting
            time.sleep(2)
            
            # Try to connect
            if self.connect():
                self.logger.info(f"Reader {self.reader_id}: ✓ Reconnection successful")
                return True
            else:
                self.logger.error(f"Reader {self.reader_id}: ✗ Reconnection failed")
                return False
        else:
            self.logger.error(f"Reader {self.reader_id}: ✗ Max reconnection attempts reached ({self.max_connection_attempts})")
            return False
    
    def disconnect(self):
        if self.objdll:
            try:
                self.logger.info(f"Reader {self.reader_id}: Disconnecting...")
                self.objdll.SWNet_CloseDevice()
                self.is_connected = False
                self.logger.info(f"Reader {self.reader_id}: ✓ Disconnected")
            except Exception as e:
                self.logger.error(f"Reader {self.reader_id}: ✗ Disconnect error: {str(e)}")
    
    def check_connection_status(self):
        """Check if the reader is still connected and log status"""
        if not self.is_connected:
            return False
            
        try:
            # Try a simple operation to check connection
            arrBuffer = bytes(9182)
            iTagLength = c_int(0)
            iTagNumber = c_int(0)
            ret = self.objdll.SWNet_GetTagBuf(arrBuffer, byref(iTagLength), byref(iTagNumber))
            if ret == 1:
                self.logger.debug(f"Reader {self.reader_id}: Connection status - OK")
                return True
            else:
                self.logger.warning(f"Reader {self.reader_id}: Connection status - FAILED (return code: {ret})")
                self.is_connected = False
                return False
        except Exception as e:
            self.logger.warning(f"Reader {self.reader_id}: Connection check failed - {str(e)}")
            self.is_connected = False
            return False
    
    def clear_buffer_safely(self):
        """Clear reader buffer without disconnecting"""
        if not self.is_connected:
            self.logger.warning(f"Reader {self.reader_id}: Cannot clear buffer - not connected")
            return False
        
        try:
            self.logger.debug(f"Reader {self.reader_id}: Clearing buffer safely...")  # Changed to debug
            self.objdll.SWNet_ClearTagBuf()
            self.logger.debug(f"Reader {self.reader_id}: ✓ Buffer cleared successfully")  # Changed to debug
            return True
        except Exception as e:
            self.logger.error(f"Reader {self.reader_id}: ✗ Error clearing buffer: {str(e)}")
            # If buffer clearing fails, mark connection as lost
            self.is_connected = False
            return False
    
    def read_tags(self):
        if not self.is_connected:
            return []
        
        try:
            arrBuffer = bytes(9182)
            iTagLength = c_int(0)
            iTagNumber = c_int(0)
            
            ret = self.objdll.SWNet_GetTagBuf(arrBuffer, byref(iTagLength), byref(iTagNumber))
            
            tags = []
            seen_tags = set()  # Track unique tags in this reading cycle
            
            if iTagNumber.value > 0:
                self.logger.debug(f"Reader {self.reader_id}: Found {iTagNumber.value} tag readings")  # Changed to debug
                iIndex = int(0)
                iLength = int(0)
                bPackLength = c_byte(0)
                
                for iIndex in range(0, iTagNumber.value):
                    bPackLength = arrBuffer[iLength]
                    
                    # Extract tag type
                    tag_type = arrBuffer[1 + iLength + 0]
                    
                    # Extract antenna
                    antenna = arrBuffer[1 + iLength + 1]
                    
                    # Extract tag ID (following the exact pattern from working example)
                    tag_id = ""
                    for i in range(2, bPackLength - 1):
                        tag_id += f"{arrBuffer[1 + iLength + i]:02X}"
                    
                    # Extract RSSI
                    rssi = arrBuffer[1 + iLength + bPackLength - 1]
                    
                    # Only process unique tags in this reading cycle
                    if tag_id not in seen_tags:
                        seen_tags.add(tag_id)
                        self.logger.info(f"Reader {self.reader_id}: Unique tag detected - ID: {tag_id}, Type: {tag_type}, Antenna: {antenna}, RSSI: {rssi}")
                        
                        tags.append({
                            'tag_id': tag_id,
                            'tag_type': tag_type,
                            'antenna': antenna,
                            'rssi': rssi,
                            'reader_id': self.reader_id,
                            'lane_id': self.lane_id,
                            'device_id': self.device_id,
                            'timestamp': datetime.now()
                        })
                    else:
                        self.logger.debug(f"Reader {self.reader_id}: Duplicate tag {tag_id} in same reading cycle - skipping")
                    
                    iLength = iLength + bPackLength + 1
                
                self.logger.debug(f"Reader {self.reader_id}: Processed {len(tags)} unique tags from {iTagNumber.value} readings")  # Changed to debug
            else:
                # Log when no tags are found (less frequently to avoid spam)
                if hasattr(self, '_last_no_tags_log') and time.time() - self._last_no_tags_log < 10:  # Increased from 5 to 10 seconds
                    pass  # Don't log too frequently
                else:
                    self.logger.debug(f"Reader {self.reader_id}: No tags detected")
                    self._last_no_tags_log = time.time()
            
            return tags
        except Exception as e:
            self.logger.error(f"Reader {self.reader_id}: ✗ Error reading tags: {str(e)}")
            self.is_connected = False
            return []

class RelayController:
    def __init__(self):
        self.logger = logging.getLogger('RelayController')
        self.pins = [26, 20, 21]  # CH1, CH2, CH3
        self.logger.info("Initializing GPIO for relay control...")
        self.init_gpio()
        # Safety measure: ensure all relays are OFF on startup
        self.turn_off_all()
        self.logger.info("🔌 Safety check: All relays confirmed OFF on startup")
    
    def init_gpio(self):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO is not available, skipping GPIO initialization.")
            return
        try:
            self.logger.info("Setting up GPIO mode (BCM)...")
            GPIO.setmode(GPIO.BCM)
            self.logger.info("Configuring relay pins (Active-High)...")
            for pin in self.pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, False)  # Initialize to OFF state (LOW for active-high)
            self.logger.info("✓ GPIO initialized successfully (Active-High configuration)")
        except Exception as e:
            self.logger.error(f"✗ GPIO initialization error: {str(e)}")
    
    def turn_on(self, relay_number):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO is not available, cannot turn on relay.")
            return False
        try:
            if 1 <= relay_number <= 3:
                pin = self.pins[relay_number - 1]
                self.logger.info(f"Turning ON relay {relay_number} (GPIO pin {pin})...")
                GPIO.output(pin, True)  # HIGH for active-high relays (turns ON)
                self.logger.info(f"✓ Relay {relay_number} turned ON")
                return True
            else:
                self.logger.error(f"✗ Invalid relay number: {relay_number}")
                return False
        except Exception as e:
            self.logger.error(f"✗ Error turning on relay {relay_number}: {str(e)}")
            return False
    
    def turn_off(self, relay_number):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO is not available, cannot turn off relay.")
            return False
        try:
            if 1 <= relay_number <= 3:
                pin = self.pins[relay_number - 1]
                self.logger.info(f"Turning OFF relay {relay_number} (GPIO pin {pin})...")
                GPIO.output(pin, False)  # LOW for active-high relays (turns OFF)
                self.logger.info(f"✓ Relay {relay_number} turned OFF")
                return True
            else:
                self.logger.error(f"✗ Invalid relay number: {relay_number}")
                return False
        except Exception as e:
            self.logger.error(f"✗ Error turning off relay {relay_number}: {str(e)}")
            return False
    
    def turn_off_all(self):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO is not available, cannot turn off all relays.")
            return
        try:
            self.logger.info("Turning OFF all relays...")
            for pin in self.pins:
                GPIO.output(pin, False)  # LOW for active-high relays (turns OFF)
            self.logger.info("✓ All relays turned OFF")
        except Exception as e:
            self.logger.error(f"✗ Error turning off all relays: {str(e)}")
    
    def cleanup(self):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO is not available, skipping GPIO cleanup.")
            return
        try:
            self.logger.info("Cleaning up GPIO...")
            self.turn_off_all()
            GPIO.cleanup()
            self.logger.info("✓ GPIO cleanup completed")
        except Exception as e:
            self.logger.error(f"✗ GPIO cleanup error: {str(e)}")

class RFIDService:
    def __init__(self):
        self.readers = []
        self.relay_controller = RelayController()
        self.running = False
        self.processed_tags = set()  # To avoid duplicate processing
        self.heartbeat_interval = 60  # Increased from 30 to 60 seconds
        self.last_heartbeat = time.time()
        self.app = app
        self.tag_cooldowns = {}  # {tag_id: last_access_time}
        self.tag_cooldown_duration = 3  # 3 seconds cooldown (was 10)
        self.db_queue = queue.Queue()
        self.db_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="DBWorker")
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 30  # Cleanup every 30 seconds instead of every second
        # --- Cooldown and cross-lane logic ---
        self.COOLDOWN_SECONDS = 10
        self.CROSS_LANE_SECONDS = 20
        self.MAX_DB_RECORDS = 3
        self.last_db_insert = defaultdict(lambda: {'time': 0, 'count': 0})  # (tag_id, lane_id): {time, count}
        
        self.logger.info("RFID Service initialized")
        
    def setup_readers(self):
        self.logger.info("Setting up RFID readers from database...")
        
        try:
            if FLASK_AVAILABLE:
                # Use Flask database
                with self.app.app_context():
                    db = get_db()
                    # Query readers with their lane and location information
                    readers_data = db.execute("""
                        SELECT 
                            r.id as reader_id,
                            r.reader_ip,
                            r.mac_address,
                            r.type,
                            r.lane_id,
                            l.lane_name,
                            loc.name as location_name
                        FROM readers r
                        JOIN lanes l ON r.lane_id = l.id
                        JOIN locations loc ON l.location_id = loc.id
                        ORDER BY r.id
                    """).fetchall()
            else:
                # Standalone mode - use direct sqlite3 access
                conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                c = conn.cursor()
                c.execute("""
                    SELECT 
                        r.id as reader_id,
                        r.reader_ip,
                        r.mac_address,
                        r.type,
                        r.lane_id,
                        l.lane_name,
                        loc.name as location_name
                    FROM readers r
                    JOIN lanes l ON r.lane_id = l.id
                    JOIN locations loc ON l.location_id = loc.id
                    ORDER BY r.id
                """)
                readers_data = c.fetchall()
                conn.close()
            
            if not readers_data:
                self.logger.warning("No readers found in database.")
                return
            
            # Clear existing readers
            self.readers = []
            
            for reader_data in readers_data:
                reader_id = reader_data['reader_id']
                reader_ip = reader_data['reader_ip']
                lane_id = reader_data['lane_id']
                reader_type = reader_data['type']
                lane_name = reader_data['lane_name']
                location_name = reader_data['location_name']
                
                # Determine DLL path based on reader type or ID
                if reader_type == 'entry':
                    dll_path = "./libSWNetClientApi1.so"
                elif reader_type == 'exit':
                    dll_path = "./libSWNetClientApi2.so"
                else:
                    # Fallback based on reader ID
                    dll_path = f"./libSWNetClientApi{reader_id}.so"
                
                # Create RFID reader instance
                reader = RFIDReader(
                    ip_address=reader_ip,
                    reader_id=reader_id,
                    lane_id=lane_id,
                    device_id=reader_id,  # Use reader_id as device_id
                    dll_path=dll_path
                )
                
                self.readers.append(reader)
                self.logger.info(f"✓ Configured Reader {reader_id}: {reader_ip} ({reader_type}) - Lane: {lane_name} at {location_name}")
            
            self.logger.info(f"✓ Setup {len(self.readers)} readers from database")
            
        except Exception as e:
            self.logger.error(f"✗ Error loading readers from database: {str(e)}")
            self.readers = []
    
    def connect_readers(self):
        self.logger.info("Connecting to RFID readers...")
        for reader in self.readers:
            if reader.connect():
                self.logger.info(f"✓ Reader {reader.reader_id} connected successfully")
            else:
                self.logger.error(f"✗ Reader {reader.reader_id} failed to connect")
    
    def verify_tag_in_database(self, tag_id):
        self.logger.debug(f"Verifying tag {tag_id} in database...")
        if FLASK_AVAILABLE:
            # Use Flask database
            with self.app.app_context():
                try:
                    # Check if tag exists in kyc_users table (current project schema)
                    db = get_db()
                    user = db.execute('SELECT * FROM kyc_users WHERE fastag_id = ?', (tag_id,)).fetchone()
                    if user:
                        self.logger.info(f"✓ Tag {tag_id} found in database")
                        self.logger.debug(f"  - Vehicle: {user['vehicle_number']}")
                        self.logger.debug(f"  - Owner: {user['name']}")
                        return {
                            'found': True,
                            'user': user,
                            'message': f"Access granted for vehicle {user['vehicle_number']} - {user['name']}"
                        }
                    else:
                        self.logger.warning(f"✗ Tag {tag_id} not found in database")
                        return {
                            'found': False,
                            'message': f"Access denied - Tag {tag_id} not found in database"
                        }
                except Exception as e:
                    self.logger.error(f"✗ Database error: {str(e)}")
                    return {
                        'found': False,
                        'message': f"Database error: {str(e)}"
                    }
        else:
            # Standalone mode - use real sqlite3 access
            return verify_tag_in_db_sqlite(tag_id)
    
    def can_insert_db(self, tag_id, lane_id):
        now = time.time()
        key = (tag_id, lane_id)
        info = self.last_db_insert[key]
        if info['count'] >= self.MAX_DB_RECORDS:
            return False
        if now - info['time'] < self.COOLDOWN_SECONDS:
            return False
        return True

    def update_db_insert(self, tag_id, lane_id):
        now = time.time()
        key = (tag_id, lane_id)
        self.last_db_insert[key]['time'] = now
        self.last_db_insert[key]['count'] += 1

    def cross_lane_recent(self, tag_id, current_lane_id):
        now = time.time()
        for (tid, lid), info in self.last_db_insert.items():
            if tid == tag_id and lid != current_lane_id:
                if now - info['time'] < self.CROSS_LANE_SECONDS:
                    return True
        return False

    def log_access_async(self, tag_id, user, status, reader_id, lane_id, device_id):
        def _log_access():
            # Only insert in DB if allowed by cooldown/cross-lane logic
            if self.can_insert_db(tag_id, lane_id):
                if FLASK_AVAILABLE:
                    with self.app.app_context():
                        try:
                            db = get_db()
                            # Use current project's access_logs table schema
                            db.execute("""
                                INSERT INTO access_logs (tag_id, reader_id, lane_id, access_result, reason, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (tag_id, reader_id, lane_id, status, None, datetime.now()))
                            db.commit()
                            self.update_db_insert(tag_id, lane_id)
                            self.logger.debug(f"✓ Access log created: {status} for tag {tag_id}")
                        except Exception as e:
                            self.logger.error(f"✗ Error logging access: {str(e)}")
                else:
                    log_access_sqlite(tag_id, user, status, reader_id, lane_id, device_id)
                    self.update_db_insert(tag_id, lane_id)
            else:
                self.logger.info(f"DB insert skipped for tag={tag_id} lane={lane_id} (cooldown or max records reached)")
        self.db_executor.submit(_log_access)
    
    def process_tag(self, tag_data):
        tag_id = tag_data['tag_id']
        reader_id = tag_data['reader_id']
        lane_id = tag_data['lane_id']
        device_id = tag_data['device_id']
        reader = next((r for r in self.readers if r.reader_id == reader_id), None)
        if not reader:
            self.logger.error(f"Reader object for reader_id {reader_id} not found!")
            return
        # --- Cross-lane check ---
        if self.cross_lane_recent(tag_id, lane_id):
            self.log_access_async(tag_id, None, 'cross_lane_blocked', reader_id, lane_id, device_id)
            self.logger.info(f"Tag {tag_id} seen in another lane within {self.CROSS_LANE_SECONDS}s, access not granted.")
            return
        # ✅ CRITICAL: Check cooldown FIRST before any processing
        in_cooldown, remaining_time = self.is_tag_in_cooldown(tag_id)
        if in_cooldown:
            self.logger.warning(f"⚠️ Tag {tag_id} is in cooldown - {remaining_time:.1f}s remaining")
            self.logger.info("⚠️ Barrier will NOT open - cooldown period active")
            self.logger.info("=" * 50)
            
            # ✅ NEW: Clear buffer immediately for cooldown tags to prevent repeated processing
            self.logger.debug(f"Reader {reader_id}: Clearing buffer for cooldown tag...")  # Changed to debug
            self.clear_reader_buffer(reader_id)
            return
        
        # Create unique key to avoid duplicate processing
        unique_key = f"{tag_id}_{reader_id}_{int(time.time())}"
        if unique_key in self.processed_tags:
            self.logger.debug(f"Skipping duplicate tag processing: {tag_id}")
            return
        
        self.processed_tags.add(unique_key)
        
        self.logger.info("=" * 50)
        self.logger.info("PROCESSING TAG")
        self.logger.info("=" * 50)
        self.logger.info(f"Tag ID: {tag_id}")
        self.logger.info(f"Reader: {reader_id}")
        self.logger.info(f"Lane: {lane_id}")
        self.logger.info(f"Device: {device_id}")
        self.logger.info(f"Timestamp: {tag_data['timestamp']}")
        self.logger.info(f"Tag Type: {tag_data['tag_type']}")
        self.logger.info(f"Antenna: {tag_data['antenna']}")
        self.logger.info(f"RSSI: {tag_data['rssi']}")
        
        # Verify tag in database
        result = self.verify_tag_in_database(tag_id)
        
        if result['found']:
            user = result['user']
            self.logger.info(f"✓ {result['message']}")
            
            # ✅ NEW: Update cooldown for this tag BEFORE opening barrier
            self.update_tag_cooldown(tag_id)
            self.logger.debug(f"✓ Tag {tag_id} cooldown updated - next access allowed in {self.tag_cooldown_duration}s")  # Changed to debug
            
            # Log successful access (async)
            self.log_access_async(tag_id, user, 'granted', reader_id, lane_id, device_id)
            
            # Turn all relays ON together
            self.logger.info("Activating barrier control...")
            self.logger.info("Turning all relays ON...")
            for relay_num in range(1, 5):  # Relays 1-4
                self.relay_controller.turn_on(relay_num)
            
            # Keep all relays ON for 2 seconds
            self.logger.info("Keeping all relays ON for 2 seconds...")
            time.sleep(2)
            
            # Turn all relays OFF together
            self.logger.info("Turning all relays OFF...")
            for relay_num in range(1, 5):  # Relays 1-4
                self.relay_controller.turn_off(relay_num)
            
            self.logger.info("✓ All relays cycle completed")
            self.logger.info("✓ Access granted - Barrier opened")
            
            # ✅ NEW: Clear reader buffer after successful access
            self.logger.debug(f"Reader {reader_id}: Clearing buffer to prevent old tag processing...")  # Changed to debug
            if reader.clear_buffer_safely():
                self.logger.debug(f"Reader {reader_id}: ✓ Buffer cleared successfully")  # Changed to debug
            else:
                self.logger.warning(f"Reader {reader_id}: ⚠️ Buffer clearing failed, but access was granted")
            
            # Fetch and cache vehicle number for denied tag_id
            if tag_id and str(tag_id).startswith('34161'):
                try:
                    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                    c = conn.cursor()
                    # Check if already cached
                    c.execute("SELECT vehicle_number FROM tag_vehicle_cache WHERE tag_id=?", (tag_id,))
                    row = c.fetchone()
                    if not row or not row[0]:
                        url = 'https://netc-acq.airtelbank.com:9443/MTMSPG/GetTagDetails'
                        params = {'SearchType': 'TagId', 'SearchValue': tag_id}
                        headers = {
                            'Cookie': 'TS019079a3=01e33451e733cecd29c7729a72c1442509a53f2b9fb40a5401f1e5e193b3b41366044039d88dde62f00c5c41a38c36914e1f1a6cd4'
                        }
                        try:
                            resp = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
                            if resp.status_code == 200:
                                data = resp.json()
                                tag_list = data.get('npcitagDetails', [])
                                if tag_list:
                                    vehicle_number = tag_list[0].get('VRN')
                                    if row:
                                        c.execute("UPDATE tag_vehicle_cache SET vehicle_number=?, last_updated=CURRENT_TIMESTAMP WHERE tag_id=?", (vehicle_number, tag_id))
                                    else:
                                        c.execute("INSERT INTO tag_vehicle_cache (tag_id, vehicle_number) VALUES (?, ?)", (tag_id, vehicle_number))
                                    conn.commit()
                                    self.logger.info(f"Cached vehicle number for denied tag {tag_id}: {vehicle_number}")
                        except Exception as e:
                            self.logger.error(f"Failed to fetch vehicle number for tag {tag_id}: {e}")
                    conn.close()
                except Exception as e:
                    self.logger.error(f"Failed to cache vehicle number for tag {tag_id}: {e}")
            
        else:
            self.logger.warning(f"✗ {result['message']} (Reader {reader_id})")
            
            # Log denied access (async)
            self.log_access_async(tag_id, None, 'denied', reader_id, lane_id, device_id)
            self.logger.info("✗ Access denied - Barrier remains closed")

            # Fetch and cache vehicle number for denied tag_id
            if tag_id and str(tag_id).startswith('34161'):
                try:
                    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                    c = conn.cursor()
                    # Check if already cached
                    c.execute("SELECT vehicle_number FROM tag_vehicle_cache WHERE tag_id=?", (tag_id,))
                    row = c.fetchone()
                    if not row or not row[0]:
                        url = 'https://netc-acq.airtelbank.com:9443/MTMSPG/GetTagDetails'
                        params = {'SearchType': 'TagId', 'SearchValue': tag_id}
                        headers = {
                            'Cookie': 'TS019079a3=01e33451e733cecd29c7729a72c1442509a53f2b9fb40a5401f1e5e193b3b41366044039d88dde62f00c5c41a38c36914e1f1a6cd4'
                        }
                        try:
                            resp = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
                            if resp.status_code == 200:
                                data = resp.json()
                                tag_list = data.get('npcitagDetails', [])
                                if tag_list:
                                    vehicle_number = tag_list[0].get('VRN')
                                    if row:
                                        c.execute("UPDATE tag_vehicle_cache SET vehicle_number=?, last_updated=CURRENT_TIMESTAMP WHERE tag_id=?", (vehicle_number, tag_id))
                                    else:
                                        c.execute("INSERT INTO tag_vehicle_cache (tag_id, vehicle_number) VALUES (?, ?)", (tag_id, vehicle_number))
                                    conn.commit()
                                    self.logger.info(f"Cached vehicle number for denied tag {tag_id}: {vehicle_number}")
                        except Exception as e:
                            self.logger.error(f"Failed to fetch vehicle number for tag {tag_id}: {e}")
                    conn.close()
                except Exception as e:
                    self.logger.error(f"Failed to cache vehicle number for tag {tag_id}: {e}")
            
            # ✅ NEW: Also clear buffer for denied access to prevent repeated processing
            self.logger.debug(f"Reader {reader_id}: Clearing buffer after denied access...")  # Changed to debug
            if reader.clear_buffer_safely():
                self.logger.debug(f"Reader {reader_id}: ✓ Buffer cleared after denied access")  # Changed to debug
            else:
                self.logger.warning(f"Reader {reader_id}: ⚠️ Buffer clearing failed after denied access")
        
        self.logger.info("=" * 50)
    
    def send_heartbeat(self):
        """Send heartbeat message to show service is running"""
        current_time = time.time()
        if current_time - self.last_heartbeat >= self.heartbeat_interval:
            connected_readers = sum(1 for reader in self.readers if reader.is_connected)
            total_readers = len(self.readers)
            self.logger.info(f"💓 HEARTBEAT: RFID Service running - {connected_readers}/{total_readers} readers connected")
            self.logger.info(f"💓 HEARTBEAT: Monitoring for tags... (Last heartbeat: {datetime.now().strftime('%H:%M:%S')})")
            self.last_heartbeat = current_time
    
    def check_reader_connections(self):
        """Check and attempt to reconnect disconnected readers"""
        for current_reader in self.readers:
            if not current_reader.is_connected:
                self.logger.info(f"Reader {current_reader.reader_id}: Connection lost, attempting to reconnect...")
                if current_reader.reconnect():
                    self.logger.info(f"Reader {current_reader.reader_id}: ✓ Reconnected successfully")
                else:
                    self.logger.warning(f"Reader {current_reader.reader_id}: ✗ Reconnection failed")
    
    def reader_thread(self, current_reader):
        self.logger.info(f"Starting reader thread for Reader {current_reader.reader_id}")
        
        while self.running:
            try:
                if current_reader.is_connected:
                    tags = current_reader.read_tags()
                    
                    # ✅ NEW: Clear buffer if too many unique tags are found (indicates buffer buildup)
                    if len(tags) > current_reader.buffer_clear_threshold:  # Use reader's threshold
                        self.logger.warning(f"Reader {current_reader.reader_id}: Too many unique tags in buffer ({len(tags)}), clearing...")
                        current_reader.clear_buffer_safely()
                        continue
                    
                    for tag in tags:
                        self.process_tag(tag)
                    
                    # Check connection status periodically (every 30 seconds)
                    current_time = time.time()
                    if current_time - current_reader.last_connection_check >= current_reader.connection_check_interval:
                        if not current_reader.check_connection_status():
                            self.logger.warning(f"Reader {current_reader.reader_id}: Connection lost during monitoring")
                            current_reader.is_connected = False
                        current_reader.last_connection_check = current_time
                else:
                    # Reader is disconnected, try to reconnect
                    self.logger.info(f"Reader {current_reader.reader_id}: Attempting to reconnect...")
                    if current_reader.reconnect():
                        self.logger.info(f"Reader {current_reader.reader_id}: ✓ Reconnected successfully")
                        current_reader.last_connection_check = time.time()  # Reset connection check timer
                    else:
                        self.logger.error(f"Reader {current_reader.reader_id}: ✗ Reconnection failed")
                        time.sleep(3)  # Reduced from 5 to 3 seconds
                
                time.sleep(0.05)  # Reduced from 0.1 to 0.05 seconds for faster response
            except Exception as e:
                self.logger.error(f"Reader {current_reader.reader_id} thread error: {str(e)}")
                # Mark connection as lost on any error
                current_reader.is_connected = False
                time.sleep(0.5)  # Reduced from 1 to 0.5 seconds
        
        self.logger.info(f"Reader {current_reader.reader_id} thread stopped")
    
    def start(self):
        self.logger.info("=" * 60)
        self.logger.info("STARTING RFID SERVICE")
        self.logger.info("=" * 60)
        self.running = True
        
        # Setup and connect readers
        self.setup_readers()
        self.connect_readers()
        
        # Start reader threads
        threads = []
        for reader in self.readers:
            thread = threading.Thread(target=self.reader_thread, args=(reader,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            self.logger.info(f"✓ Started thread for Reader {reader.reader_id}")
        
        self.logger.info(f"✓ RFID Service started with {len(threads)} reader threads")
        self.logger.info("RFID Service is now running and monitoring for tags...")
        self.logger.info("=" * 60)
        
        try:
            # Keep main thread alive with heartbeat and connection monitoring
            while self.running:
                # Send heartbeat
                self.send_heartbeat()
                
                # Check reader connections
                self.check_reader_connections()
                
                # ✅ NEW: Cleanup expired cooldowns periodically (less frequent)
                current_time = time.time()
                if current_time - self.last_cleanup_time >= self.cleanup_interval:
                    self.cleanup_expired_cooldowns()
                    self.cleanup_processed_tags()
                    self.last_cleanup_time = current_time
                
                time.sleep(2)  # Increased from 1 to 2 seconds to reduce CPU usage
        except KeyboardInterrupt:
            self.logger.info("\nShutting down RFID Service...")
            self.stop()
    
    def stop(self):
        self.logger.info("Stopping RFID Service...")
        self.running = False
        
        # Shutdown database executor
        self.db_executor.shutdown(wait=True)
        
        # Disconnect readers
        for reader in self.readers:
            reader.disconnect()
        
        # Cleanup GPIO
        self.relay_controller.cleanup()
        
        self.logger.info("✓ RFID Service stopped")

    def is_tag_in_cooldown(self, tag_id):
        """Check if a tag is still in cooldown period"""
        if tag_id in self.tag_cooldowns:
            last_access = self.tag_cooldowns[tag_id]
            time_since_last = time.time() - last_access
            if time_since_last < self.tag_cooldown_duration:
                remaining_cooldown = self.tag_cooldown_duration - time_since_last
                self.logger.info(f"Tag {tag_id} is in cooldown - {remaining_cooldown:.1f}s remaining")
                return True, remaining_cooldown
        return False, 0
    
    def update_tag_cooldown(self, tag_id):
        """Update the cooldown timestamp for a tag"""
        self.tag_cooldowns[tag_id] = time.time()
        self.logger.info(f"Tag {tag_id} cooldown updated - next access allowed in {self.tag_cooldown_duration}s")
    
    def cleanup_expired_cooldowns(self):
        """Remove expired cooldown entries to prevent memory buildup"""
        current_time = time.time()
        expired_tags = []
        for tag_id, last_access in self.tag_cooldowns.items():
            if current_time - last_access > self.tag_cooldown_duration:
                expired_tags.append(tag_id)
        
        for tag_id in expired_tags:
            del self.tag_cooldowns[tag_id]
        
        if expired_tags:
            self.logger.debug(f"Cleaned up {len(expired_tags)} expired cooldown entries")
    
    def cleanup_processed_tags(self):
        """Clean up processed tags set to prevent memory buildup"""
        if len(self.processed_tags) > 1000:  # Clean up if more than 1000 entries
            # Keep only recent entries (last 100)
            recent_tags = set()
            current_time = time.time()
            
            # Convert processed_tags to list and keep only recent ones
            for tag_key in list(self.processed_tags)[-100:]:
                recent_tags.add(tag_key)
            
            removed_count = len(self.processed_tags) - len(recent_tags)
            self.processed_tags = recent_tags
            
            if removed_count > 0:
                self.logger.debug(f"Cleaned up {removed_count} old processed tag entries")
    
    def clear_reader_buffer(self, reader_id):
        """Clear reader buffer using library function"""
        try:
            # Find the reader
            reader = next((r for r in self.readers if r.reader_id == reader_id), None)
            if not reader:
                self.logger.error(f"Reader {reader_id} not found for buffer clearing")
                return False
            
            if not reader.is_connected:
                self.logger.warning(f"Reader {reader_id} is not connected, cannot clear buffer")
                return False
            
            self.logger.info(f"Reader {reader_id}: Clearing buffer using library function...")
            
            # Use the library's clear function
            reader.objdll.SWNet_ClearTagBuf()
            self.logger.info(f"Reader {reader_id}: ✓ Buffer cleared successfully")
            return True
                
        except Exception as e:
            self.logger.error(f"Reader {reader_id}: ✗ Error during buffer clearing: {str(e)}")
            return False

def main():
    logger.info("One Bee RFID Service Starting...")
    service = RFIDService()
    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("\nReceived interrupt signal")
    finally:
        service.stop()

if __name__ == "__main__":
    main() 