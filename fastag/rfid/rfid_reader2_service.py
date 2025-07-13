import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import time
import requests
import sqlite3
from datetime import datetime
from collections import defaultdict
import ctypes
from ctypes import *
import logging

# Use absolute DB path in instance folder
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'fastag.db'))
print('Using DB:', DB_PATH)

def setup_logging(log_file):
    """Setup logging for RFID reader service"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class RFIDReader:
    def __init__(self, ip_address, reader_id, lane_id, device_id, dll_path="./libSWNetClientApi.so"):
        self.ip_address = ip_address
        self.reader_id = reader_id
        self.lane_id = lane_id
        self.device_id = device_id
        self.dll_path = dll_path
        self.objdll = None
        self.is_connected = False
        self.connection_attempts = 0
        self.max_connection_attempts = 5
        self.last_connection_check = time.time()
        self.connection_check_interval = 30
        self.buffer_clear_threshold = 5

    def connect(self):
        try:
            if not self.ip_address:
                logger.error(f"Reader {self.reader_id}: ✗ IP address is None or empty")
                self.connection_attempts += 1
                return False
            if not os.path.exists(self.dll_path):
                logger.error(f"Reader {self.reader_id}: ✗ Library file not found: {self.dll_path}")
                logger.error(f"Reader {self.reader_id}: Current directory: {os.getcwd()}")
                self.connection_attempts += 1
                return False
            self.objdll = ctypes.cdll.LoadLibrary(self.dll_path)
            logger.info(f"Reader {self.reader_id}: ✓ Library loaded successfully")
            logger.info(f"Reader {self.reader_id}: Connecting to {self.ip_address} with 60000ms timeout...")
            result = self.objdll.SWNet_OpenDevice(self.ip_address.encode(), 60000)
            logger.info(f"Reader {self.reader_id}: Connection result: {result}")
            if result == 1:
                logger.info(f"Reader {self.reader_id}: ✓ Connected to {self.ip_address}")
                self.objdll.SWNet_ClearTagBuf()
                logger.info(f"Reader {self.reader_id}: ✓ Tag buffer cleared")
                self.is_connected = True
                self.connection_attempts = 0
                self.last_connection_check = time.time()
                return True
            else:
                logger.error(f"Reader {self.reader_id}: ✗ Connection failed with return code {result}")
                self.connection_attempts += 1
                self.is_connected = False
                return False
        except Exception as e:
            logger.error(f"Reader {self.reader_id}: ✗ Connection error: {str(e)}")
            self.connection_attempts += 1
            self.is_connected = False
            return False

    def disconnect(self):
        self.connected = False
        self.dll = None
        self.handle = None

    def read_tags(self):
        if not self.is_connected or not self.objdll:
            return []
        try:
            arrBuffer = bytes(9182)
            iTagLength = ctypes.c_int(0)
            iTagNumber = ctypes.c_int(0)
            ret = self.objdll.SWNet_GetTagBuf(arrBuffer, ctypes.byref(iTagLength), ctypes.byref(iTagNumber))
            tags = []
            seen_tags = set()
            if iTagNumber.value > 0:
                logger.debug(f"Reader {self.reader_id}: Found {iTagNumber.value} tag readings")
                iIndex = int(0)
                iLength = int(0)
                bPackLength = ctypes.c_byte(0)
                for iIndex in range(0, iTagNumber.value):
                    bPackLength = arrBuffer[iLength]
                    tag_type = arrBuffer[1 + iLength + 0]
                    antenna = arrBuffer[1 + iLength + 1]
                    tag_id = ""
                    for i in range(2, bPackLength - 1):
                        tag_id += f"{arrBuffer[1 + iLength + i]:02X}"
                    rssi = arrBuffer[1 + iLength + bPackLength - 1]
                    if tag_id not in seen_tags:
                        seen_tags.add(tag_id)
                        logger.info(f"Reader {self.reader_id}: Unique tag detected - ID: {tag_id}, Type: {tag_type}, Antenna: {antenna}, RSSI: {rssi}")
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
                    iLength = iLength + bPackLength + 1
                logger.debug(f"Reader {self.reader_id}: Processed {len(tags)} unique tags from {iTagNumber.value} readings")
            else:
                logger.debug(f"Reader {self.reader_id}: No tags detected")
            return tags
        except Exception as e:
            logger.error(f"Reader {self.reader_id}: ✗ Error reading tags: {str(e)}")
            self.is_connected = False
            return []

logger = setup_logging('logs/rfid_reader2.log')

def load_reader_config(reader_id=2):
    """Load reader configuration from database"""
    try:
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
            WHERE r.id = ?
        """, (reader_id,))
        reader_data = c.fetchone()
        conn.close()
        
        if reader_data:
            return {
                'reader_id': reader_data[0],
                'reader_ip': reader_data[1],
                'mac_address': reader_data[2],
                'type': reader_data[3],
                'lane_id': reader_data[4],
                'lane_name': reader_data[5],
                'location_name': reader_data[6]
            }
        else:
            logger.error(f"Reader {reader_id} not found in database")
            return None
    except Exception as e:
        logger.error(f"Error loading reader configuration: {e}")
        return None

def strip_leading_zeros(ip):
    return '.'.join(str(int(octet)) for octet in ip.split('.'))

# Load configuration from database
config = load_reader_config(2)
if not config:
    logger.error("Failed to load reader configuration. Exiting.")
    exit(1)

READER_IP = strip_leading_zeros(config['reader_ip'])
LANE_ID = config['lane_id']
DEVICE_ID = config['reader_id']

# Determine DLL path based on reader type
if config['type'] == 'entry':
    DLL_PATH = os.path.join(os.path.dirname(__file__), "libSWNetClientApi1.so")
elif config['type'] == 'exit':
    DLL_PATH = os.path.join(os.path.dirname(__file__), "libSWNetClientApi2.so")
else:
    DLL_PATH = os.path.join(os.path.dirname(__file__), f"libSWNetClientApi{config['reader_id']}.so")

logger.info(f"Reader {config['reader_id']} configuration loaded:")
logger.info(f"  - IP: {READER_IP}")
logger.info(f"  - Type: {config['type']}")
logger.info(f"  - Lane: {config['lane_name']} (ID: {LANE_ID})")
logger.info(f"  - Location: {config['location_name']}")
logger.info(f"  - DLL: {DLL_PATH}")

reader = RFIDReader(READER_IP, config['reader_id'], LANE_ID, DEVICE_ID, dll_path=DLL_PATH)

if not reader.connect():
    logger.error("Failed to connect to Reader 2")
    exit(1)

logger.info("Reader 2 service started")

# Add cooldown, cross-lane, and access logging logic
COOLDOWN_SECONDS = 10
CROSS_LANE_SECONDS = 20
MAX_DB_RECORDS = 3
last_db_insert = defaultdict(lambda: {'time': 0, 'count': 0})
tag_cooldowns = {}
tag_cooldown_duration = 3
processed_tags = set()

# Relay control (use RelayController from relay_controller.py)
from fastag.rfid.relay_controller import RelayController
relay_controller = RelayController()

def activate_all_relays():
    relay_number = 2  # Only use relay 2 for reader 2
    logger.info(f"Turning ON relay {relay_number} (GPIO pin {relay_controller.pins[relay_number-1]})...")
    relay_controller.turn_on(relay_number)
    time.sleep(2)
    logger.info(f"Turning OFF relay {relay_number} (GPIO pin {relay_controller.pins[relay_number-1]})...")
    relay_controller.turn_off(relay_number)

# Helper functions

def can_insert_db(tag_id, lane_id):
    now = time.time()
    key = (tag_id, lane_id)
    info = last_db_insert[key]
    if info['count'] >= MAX_DB_RECORDS:
        return False
    if now - info['time'] < COOLDOWN_SECONDS:
        return False
    return True

def update_db_insert(tag_id, lane_id):
    now = time.time()
    key = (tag_id, lane_id)
    last_db_insert[key]['time'] = now
    last_db_insert[key]['count'] += 1

def cross_lane_recent(tag_id, current_lane_id):
    now = time.time()
    for (tid, lid), info in last_db_insert.items():
        if tid == tag_id and lid != current_lane_id:
            if now - info['time'] < CROSS_LANE_SECONDS:
                return True
    return False

def is_tag_in_cooldown(tag_id):
    if tag_id in tag_cooldowns:
        last_access = tag_cooldowns[tag_id]
        time_since_last = time.time() - last_access
        if time_since_last < tag_cooldown_duration:
            return True, tag_cooldown_duration - time_since_last
    return False, 0

def update_tag_cooldown(tag_id):
    tag_cooldowns[tag_id] = time.time()

def log_access(tag_id, user, status, reason=None):
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("""
            INSERT INTO access_logs (user_id, device_id, created_at, access_time, status, tag_id, reader_id, lane_id, access_result, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user['id'] if user else None,
            DEVICE_ID,
            datetime.now(),
            datetime.now(),
            status,
            tag_id,
            DEVICE_ID,  # reader_id
            LANE_ID,
            status,
            reason
        ))
        conn.commit()
        conn.close()
        logger.info(f"Access log created: {status} for tag {tag_id}")
        update_db_insert(tag_id, LANE_ID)
    except Exception as e:
        logger.error(f"Error logging access: {str(e)}")

def clear_buffer(reader):
    try:
        if reader.is_connected and reader.objdll:
            reader.objdll.SWNet_ClearTagBuf()
            logger.info(f"Reader {reader.reader_id}: Tag buffer cleared")
    except Exception as e:
        logger.warning(f"Reader {reader.reader_id}: Error clearing buffer: {e}")

def check_tag_in_db(tag_id):
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        # Use kyc_users table (current project schema)
        c.execute("SELECT id, name, vehicle_number FROM kyc_users WHERE fastag_id=?", (tag_id,))
        row = c.fetchone()
        conn.close()
        if row:
            user_id, name, vehicle_number = row
            logger.info(f"DB check: tag {tag_id} found for user {name}")
            return user_id, name, vehicle_number
        else:
            logger.info(f"DB check: tag {tag_id} not found in kyc_users")
            return None, None, None
    except Exception as e:
        logger.error(f"DB error for tag {tag_id}: {e}")
        return None, None, None

try:
    while True:
        logger.info(f"Polling for tags at IP: {READER_IP} (Connected: {reader.is_connected})")
        tags = reader.read_tags()
        now = time.time()
        if tags:
            for tag in tags:
                tag_id = tag['tag_id']
                # Cooldown check
                in_cooldown, remaining = is_tag_in_cooldown(tag_id)
                if in_cooldown:
                    logger.info(f"Tag {tag_id} is in cooldown - {remaining:.1f}s remaining")
                    clear_buffer(reader)
                    continue
                # Deduplication check
                if not can_insert_db(tag_id, LANE_ID):
                    logger.info(f"DB insert skipped for tag={tag_id} lane={LANE_ID} (cooldown or max records reached)")
                    clear_buffer(reader)
                    continue
                # Cross-lane check
                if cross_lane_recent(tag_id, LANE_ID):
                    log_access(tag_id, None, 'denied', reason='cross_lane_blocked')
                    update_tag_cooldown(tag_id)
                    update_db_insert(tag_id, LANE_ID)
                    logger.info(f"Tag {tag_id} seen in another lane within {CROSS_LANE_SECONDS}s, access not granted.")
                    clear_buffer(reader)
                    continue
                # DB check
                user_id, name, vehicle_number = check_tag_in_db(tag_id)
                user = {'id': user_id, 'name': name, 'vehicle_number': vehicle_number} if user_id else None
                if user_id:
                    log_access(tag_id, user, 'granted')
                    update_tag_cooldown(tag_id)
                    update_db_insert(tag_id, LANE_ID)
                    activate_all_relays()
                    logger.info(f"Access granted for tag {tag_id}")
                else:
                    log_access(tag_id, None, 'denied', reason='not_found')
                    update_tag_cooldown(tag_id)
                    update_db_insert(tag_id, LANE_ID)
                    logger.info(f"Access denied for tag {tag_id}")
                clear_buffer(reader)
        else:
            logger.info("No tags detected.")
        time.sleep(0.1)
except KeyboardInterrupt:
    logger.info("Shutting down Reader 2 service...")
finally:
    reader.disconnect()
    logger.info("Reader 2 service stopped.") 