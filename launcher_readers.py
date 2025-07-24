#!/usr/bin/env python3
import os
import subprocess
import signal
import time
import psutil

# List of service files to always start
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

# Helper: start both service files
def start_services():
    for svc in SERVICE_FILES:
        if os.path.exists(svc):
            print(f"Starting {svc}...")
            subprocess.Popen(['python3', svc])
        else:
            print(f"Service file {svc} not found!")

if __name__ == "__main__":
    print("[Launcher] Stopping all running RFID reader services...")
    stop_all_services()
    print("[Launcher] Starting required services...")
    start_services()
    print("[Launcher] Done.")
    # Block forever so systemd service stays alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("[Launcher] Received KeyboardInterrupt, exiting...")
        stop_all_services()
        print("[Launcher] Exited cleanly.") 