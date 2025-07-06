#!/usr/bin/env python3
import os
import sqlite3
import subprocess
import signal
import time
import psutil
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fastag', 'rfid'))
from rfid_common import RFIDReader, setup_logging

# Path to DB and service scripts
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance', 'fastag.db'))
SERVICE_FILES = [
    'fastag/rfid/rfid_reader1_service.py',
    'fastag/rfid/rfid_reader2_service.py',
]

# Helper: find running service processes
def find_running_services():
    running = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = ' '.join(proc.info['cmdline'])
            for svc in SERVICE_FILES:
                if svc in cmd:
                    running.append((proc.pid, svc))
        except Exception:
            continue
    return running

# Helper: stop all running service processes
def stop_all_services():
    running = find_running_services()
    for pid, svc in running:
        print(f"Stopping {svc} (PID {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception as e:
            print(f"Could not stop {svc}: {e}")
    # Give time for processes to exit
    time.sleep(2)

# Helper: get readers from DB
def get_readers_from_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Check if readers table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='readers'")
    if not c.fetchone():
        print("❌ ERROR: 'readers' table does not exist in the database. Please run database initialization first.")
        conn.close()
        exit(1)
    c.execute("SELECT id FROM readers ORDER BY id ASC LIMIT 2")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

# Helper: start required service files
def start_services(reader_ids):
    for rid in reader_ids:
        svc = f"fastag/rfid/rfid_reader{rid}_service.py"
        if os.path.exists(svc):
            print(f"Starting {svc}...")
            subprocess.Popen(['python3', svc])
        else:
            print(f"Service file {svc} not found!")

if __name__ == "__main__":
    print("[Launcher] Stopping all running RFID reader services...")
    stop_all_services()
    print("[Launcher] Querying DB for active readers...")
    reader_ids = get_readers_from_db()
    print(f"[Launcher] Found readers: {reader_ids}")
    print("[Launcher] Starting required services...")
    start_services(reader_ids)
    print("[Launcher] Done.") 