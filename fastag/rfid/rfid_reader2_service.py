import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
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
        self.connected = False
        self.dll = None
        self.handle = None

    def connect(self):
        try:
            self.dll = ctypes.CDLL(self.dll_path)
            # Simulate connection logic (replace with actual hardware logic)
            self.connected = True
            return True
        except Exception as e:
            print(f"RFIDReader connect error: {e}")
            self.connected = False
            return False

    def disconnect(self):
        self.connected = False
        self.dll = None
        self.handle = None

    def read_tags(self):
        # Simulate reading tags (replace with actual hardware logic)
        # Return a list of dicts: [{'tag_id': ..., 'antenna': ..., 'rssi': ...}, ...]
        # For demo, return empty list
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

# Load configuration from database
config = load_reader_config(2)
if not config:
    logger.error("Failed to load reader configuration. Exiting.")
    exit(1)

READER_IP = config['reader_ip']
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

RELAY_CONTROL_URL = "http://localhost:5000/api/barrier-control"

COOLDOWN_SECONDS = 10  # Cooldown window for same tag/lane
CROSS_LANE_SECONDS = 20  # Cross-lane block window
MAX_DB_RECORDS = 3  # Max DB records per tag/lane per session

# Track last DB insert time and count for each (tag_id, lane_id)
last_db_insert = defaultdict(lambda: {'time': 0, 'count': 0})

def can_insert_db(tag_id, lane_id):
    now = time.time()
    key = (tag_id, lane_id)
    info = last_db_insert[key]
    # If already 3 records, do not insert
    if info['count'] >= MAX_DB_RECORDS:
        return False
    # If last insert <10s ago, do not insert
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

def activate_all_relays():
    try:
        payload = {
            "lane_id": LANE_ID,
            "device_id": DEVICE_ID,
            "action": "open",
            "timestamp": datetime.now().isoformat()
        }
        response = requests.post(RELAY_CONTROL_URL, json=payload, timeout=2)
        if response.status_code == 200:
            logger.info("Barrier open command sent via Flask API")
        else:
            logger.error(f"API error: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"Failed to activate relays via API: {e}")

def log_access(tag_id, status, reason=None):
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        # Use current project's access_logs table schema
        c.execute("""
            INSERT INTO access_logs (tag_id, reader_id, lane_id, access_result, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tag_id, 2, LANE_ID, status, reason, datetime.now()))
        conn.commit()
        conn.close()
        logger.info(f"Access logged: {status} for tag {tag_id}")
    except Exception as e:
        logger.error(f"Error logging access for tag {tag_id}: {e}")

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
        logger.info("Polling for tags...")
        tags = reader.read_tags()
        now = time.time()
        if tags:
            for tag in tags:
                tag_id = tag['tag_id']
                logger.info(f"Tag detected: {tag_id} (Antenna: {tag['antenna']}, RSSI: {tag['rssi']})")
                user_id, name, vehicle_number = check_tag_in_db(tag_id)
                # Cross-lane check
                if cross_lane_recent(tag_id, LANE_ID):
                    log_access(tag_id, 'denied', reason='cross_lane_blocked')
                    logger.info(f"Tag {tag_id} seen in another lane within {CROSS_LANE_SECONDS}s, access not granted.")
                    continue
                if user_id:
                    log_access(tag_id, 'granted')
                    activate_all_relays()
                else:
                    log_access(tag_id, 'denied', reason='not_found')
                    logger.info(f"Access denied for tag {tag_id}")
        else:
            logger.info("No tags detected.")
        time.sleep(0.1)
except KeyboardInterrupt:
    logger.info("Shutting down Reader 2 service...")
finally:
    reader.disconnect()
    logger.info("Reader 2 service stopped.") 