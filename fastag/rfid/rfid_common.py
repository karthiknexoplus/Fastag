import ctypes
import sys
import os
import logging
from datetime import datetime
import sqlite3

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