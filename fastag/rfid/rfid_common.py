import ctypes
import sys
import os
import logging
from datetime import datetime
import sqlite3
import requests
import time

# Logging setup (simple version for services)
def setup_logging(log_path):
    logger = logging.getLogger(log_path)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
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

def get_reader_type_from_db(reader_id, db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT type FROM readers WHERE id = ?", (reader_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]  # 'entry' or 'exit'
    return "unknown" 

def fetch_vehicle_details_from_acko(vehicle_number):
    """Fetch vehicle details from Acko API"""
    try:
        url = f'https://www.acko.com/api/app/vehicleInfo/?regNo={vehicle_number}'
        headers = {
            'Cookie': '__cf_bm=pGh50u94vAfct.OfbGLFFETRpGkG.c3kiX_7rg8j5Zo-1752374138-1.0.1.1-rWgkGF5d83kQHh.O.2NEe1WolLv.rKJyzup7ZRVTcezjH8t5Z.wJDDEoD.LZW3GRCFS2Dup2_InlxdHYx3rFrISKs8Cx6i156cMjOoJIhI0; trackerid=58db3079-80b0-40a3-b71e-0aa17adcd4ff; acko_visit=72id4bJOAC1NhUwxz9WHaQ'
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('registration_number'):
                return {
                    'owner_name': data.get('owner_name', ''),
                    'model_name': data.get('model_name', ''),
                    'fuel_type': data.get('fuel_type', ''),
                    'vehicle_type': data.get('vehicle_type_v2', ''),
                    'make_name': data.get('db_make_name', '')
                }
            else:
                logging.warning(f"No vehicle details found for {vehicle_number}")
                return None
        else:
            logging.error(f"Failed to fetch vehicle details for {vehicle_number}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logging.error(f"Error fetching vehicle details for {vehicle_number}: {e}")
        return None

def cache_vehicle_details(tag_id, vehicle_number, owner_name=None, model_name=None, fuel_type=None):
    """Cache vehicle details in database"""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        
        # Check if already exists
        c.execute("SELECT vehicle_number FROM tag_vehicle_cache WHERE tag_id=?", (tag_id,))
        row = c.fetchone()
        
        if row:
            # Update existing record
            c.execute("""
                UPDATE tag_vehicle_cache 
                SET vehicle_number=?, owner_name=?, model_name=?, fuel_type=?, last_updated=CURRENT_TIMESTAMP 
                WHERE tag_id=?
            """, (vehicle_number, owner_name, model_name, fuel_type, tag_id))
            logging.info(f"✓ Updated vehicle details for tag {tag_id}: {vehicle_number}")
        else:
            # Insert new record
            c.execute("""
                INSERT INTO tag_vehicle_cache (tag_id, vehicle_number, owner_name, model_name, fuel_type) 
                VALUES (?, ?, ?, ?, ?)
            """, (tag_id, vehicle_number, owner_name, model_name, fuel_type))
            logging.info(f"✓ Cached vehicle details for tag {tag_id}: {vehicle_number}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error caching vehicle details for tag {tag_id}: {e}")
        return False 