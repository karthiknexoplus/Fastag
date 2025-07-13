from rfid_common import RFIDReader, setup_logging
import time
import requests
import sqlite3
from datetime import datetime
from collections import defaultdict
import os

logger = setup_logging('logs/rfid_reader2.log')
READER_IP = "192.168.60.251"
DLL_PATH = "./libSWNetClientApi2.so"
# Use absolute DB path in instance folder
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance', 'access_control.db'))
print('Using DB:', DB_PATH)
LANE_ID = 2
DEVICE_ID = 2

reader = RFIDReader(READER_IP, 2, LANE_ID, DEVICE_ID, dll_path=DLL_PATH)

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

def log_access(tag_id, user_id, status):
    if can_insert_db(tag_id, LANE_ID):
        try:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("""
                INSERT INTO access_logs (user_id, lane_id, device_id, tag_id, access_time, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, LANE_ID, DEVICE_ID, tag_id, datetime.now(), status, datetime.now()
            ))
            conn.commit()
            conn.close()
            update_db_insert(tag_id, LANE_ID)
            logger.info(f"Access log written: tag={tag_id}, user_id={user_id}, status={status}")
        except Exception as e:
            logger.error(f"Failed to log access for tag {tag_id}: {e}")
    else:
        logger.info(f"DB insert skipped for tag={tag_id} lane={LANE_ID} (cooldown or max records reached)")

def check_tag_in_db(tag_id):
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id, name, vehicle_number FROM vehicle_users WHERE fastag_id=?", (tag_id,))
        row = c.fetchone()
        conn.close()
        if row:
            user_id, name, vehicle_number = row
            logger.info(f"DB check: tag {tag_id} found for user {name}")
            return user_id
        else:
            logger.info(f"DB check: tag {tag_id} not found in vehicle_users")
            return None
    except Exception as e:
        logger.error(f"DB error for tag {tag_id}: {e}")
        return None

try:
    while True:
        logger.info("Polling for tags...")
        tags = reader.read_tags()
        now = time.time()
        if tags:
            for tag in tags:
                tag_id = tag['tag_id']
                logger.info(f"Tag detected: {tag_id} (Antenna: {tag['antenna']}, RSSI: {tag['rssi']})")
                user_id = check_tag_in_db(tag_id)
                # Cross-lane check
                if cross_lane_recent(tag_id, LANE_ID):
                    log_access(tag_id, user_id, 'cross_lane_blocked')
                    logger.info(f"Tag {tag_id} seen in another lane within {CROSS_LANE_SECONDS}s, access not granted.")
                    continue
                if user_id:
                    log_access(tag_id, user_id, 'granted')
                    activate_all_relays()
                else:
                    log_access(tag_id, None, 'denied')
                    logger.info(f"Access denied for tag {tag_id}")
        else:
            logger.info("No tags detected.")
        time.sleep(0.1)
except KeyboardInterrupt:
    logger.info("Shutting down Reader 2 service...")
finally:
    reader.disconnect()
    logger.info("Reader 2 service stopped.") 