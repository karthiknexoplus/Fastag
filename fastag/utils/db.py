import sqlite3
import os
from flask import g, current_app

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
    ''')
    db.commit() 