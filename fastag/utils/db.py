import sqlite3
import os
from flask import g, current_app
import logging

def get_db():
    if 'db' not in g:
        # Ensure the instance directory exists
        db_path = current_app.config['DB_PATH']
        db_dir = os.path.dirname(db_path)
        
        # Debug information
        print(f"DEBUG: Database path: {db_path}")
        print(f"DEBUG: Database directory: {db_dir}")
        print(f"DEBUG: Current working directory: {os.getcwd()}")
        
        if db_dir and not os.path.exists(db_dir):
            print(f"DEBUG: Creating directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
        
        print(f"DEBUG: Connecting to database: {db_path}")
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        init_db(g.db)
    return g.db

def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(db):
    """Initialize database with all required tables"""
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            site_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS lanes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            lane_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations (id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS readers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lane_id INTEGER NOT NULL,
            mac_address TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('entry', 'exit')),
            reader_ip TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lane_id) REFERENCES lanes (id) ON DELETE CASCADE,
            UNIQUE(lane_id, type)
        );

        CREATE TABLE IF NOT EXISTS kyc_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            fastag_id TEXT UNIQUE NOT NULL,
            vehicle_number TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_id TEXT NOT NULL,
            reader_id INTEGER NOT NULL,
            lane_id INTEGER NOT NULL,
            access_result TEXT NOT NULL CHECK (access_result IN ('granted', 'denied')),
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reader_id) REFERENCES readers (id),
            FOREIGN KEY (lane_id) REFERENCES lanes (id)
        );

        CREATE TABLE IF NOT EXISTS barrier_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            relay_number INTEGER NOT NULL,
            action TEXT NOT NULL CHECK (action IN ('opened', 'closed')),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user TEXT,
            lane_id INTEGER,
            lane_name TEXT,
            reader_id INTEGER,
            reader_ip TEXT,
            device_id INTEGER,
            source TEXT,
            FOREIGN KEY (lane_id) REFERENCES lanes (id),
            FOREIGN KEY (reader_id) REFERENCES readers (id)
        );

        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            model TEXT,
            manufacturer TEXT,
            android_version TEXT,
            approved INTEGER DEFAULT 0,
            username TEXT,
            password TEXT,
            assigned_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    db.commit() 

def log_user_login(username, login_method):
    db = get_db()
    db.execute(
        "INSERT INTO user_logins (username, login_method) VALUES (?, ?)",
        (username, login_method)
    )
    db.commit()

def log_user_action(username, action, details=""):
    db = get_db()
    db.execute(
        "INSERT INTO user_actions (username, action, details) VALUES (?, ?, ?)",
        (username, action, details)
    )
    db.commit() 

def log_barrier_event(relay_number, action, user=None, lane_id=None, lane_name=None, reader_id=None, reader_ip=None, device_id=None, source=None):
    print("[DEBUG] Inside log_barrier_event function")
    try:
        print(f"[DEBUG] log_barrier_event called: relay={relay_number}, action={action}, user={user}, lane_id={lane_id}, lane_name={lane_name}, reader_id={reader_id}, reader_ip={reader_ip}, device_id={device_id}, source={source}")
        db = get_db()
        db.execute(
            """
            INSERT INTO barrier_events (relay_number, action, user, lane_id, lane_name, reader_id, reader_ip, device_id, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (relay_number, action, user, lane_id, lane_name, reader_id, reader_ip, device_id, source)
        )
        db.commit()
        print("[DEBUG] log_barrier_event: insert committed")
    except Exception as e:
        print(f"[ERROR] log_barrier_event failed: {e}")
        logging.error(f"log_barrier_event failed: {e}") 