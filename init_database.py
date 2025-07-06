#!/usr/bin/env python3

import sqlite3
import os

# Database path - create in instance directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'fastag.db')

def init_database():
    """Initialize the database with all required tables"""
    
    # Ensure instance directory exists
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"Created directory: {db_dir}")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
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
    ''')
    
    # Add some sample data
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", 
                   ('admin', 'admin123'))
    
    cursor.execute("INSERT OR IGNORE INTO locations (name, address, site_id) VALUES (?, ?, ?)", 
                   ('Central Parking', '123 Main St', 'CP001'))
    
    cursor.execute("INSERT OR IGNORE INTO lanes (location_id, lane_name) VALUES (?, ?)", 
                   (1, 'Main Entry'))
    
    cursor.execute("INSERT OR IGNORE INTO readers (lane_id, mac_address, type, reader_ip) VALUES (?, ?, ?, ?)", 
                   (1, '00:00:00:00', 'entry', '192.168.1.100'))
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")
    print("Sample data added:")
    print("- User: admin/admin123")
    print("- Location: Central Parking (CP001)")
    print("- Lane: Main Entry")
    print("- Reader: 00:00:00:00 (entry)")

if __name__ == '__main__':
    init_database() 