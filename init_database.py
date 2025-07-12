#!/usr/bin/env python3

import sqlite3
import os
import hashlib
import secrets
import sys

# Database path - create in instance directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'fastag.db')

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def add_column_if_not_exists(cursor, table, column, coltype):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        print(f"Adding missing column '{column}' to '{table}'...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")

def print_schema_summary(cursor):
    print("\n📋 Database Schema Summary:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = cursor.fetchall()
        col_list = ', '.join([f"{col[1]} ({col[2]})" for col in cols])
        print(f"  - {table}: {col_list}")

def add_missing_columns():
    import sqlite3
    db_path = 'instance/fastag.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Get current columns
    c.execute("PRAGMA table_info(access_logs)")
    columns = [row[1] for row in c.fetchall()]
    # Add user_id if missing
    if 'user_id' not in columns:
        c.execute("ALTER TABLE access_logs ADD COLUMN user_id INTEGER;")
    # Add device_id if missing
    if 'device_id' not in columns:
        c.execute("ALTER TABLE access_logs ADD COLUMN device_id INTEGER;")
    # Add created_at if missing
    if 'created_at' not in columns:
        c.execute("ALTER TABLE access_logs ADD COLUMN created_at TIMESTAMP;")
    conn.commit()
    conn.close()

def init_database():
    try:
        db_dir = os.path.dirname(DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created directory: {db_dir}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Create all required tables
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
            CREATE TABLE IF NOT EXISTS user_logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                login_method TEXT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT,
                details TEXT,
                action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        ''')
        # Example: Add missing column migration (add more as needed)
        # add_column_if_not_exists(cursor, 'kyc_users', 'email', 'TEXT')
        # add_column_if_not_exists(cursor, 'access_logs', 'extra_info', 'TEXT')
        # Print summary
        print_schema_summary(cursor)
        # Check if any users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Users in database: {user_count}")
        cursor.execute("SELECT COUNT(*) FROM locations")
        location_count = cursor.fetchone()[0]
        print(f"✅ Locations in database: {location_count}")
        conn.commit()
        conn.close()
        print("\n🎉 Database initialized and migrated successfully!")
        print("📝 You can now sign up for a new account and add data through the web interface")
    except Exception as e:
        print(f"❌ Database initialization/migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_database()
    add_missing_columns() 