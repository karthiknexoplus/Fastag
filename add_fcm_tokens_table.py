#!/usr/bin/env python3
"""
Add fcm_tokens table to existing database on Raspberry Pi.
This script will safely add the table without affecting existing data.
"""
import sqlite3
import os

DATABASE_PATH = 'instance/fastag.db'

def add_fcm_tokens_table():
    """Add fcm_tokens table to existing database"""
    
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        print("Please ensure the database exists first.")
        return False
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if fcm_tokens table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fcm_tokens'")
        if cursor.fetchone():
            print("✅ fcm_tokens table already exists!")
            return True
        
        # Create the fcm_tokens table
        cursor.execute('''
            CREATE TABLE fcm_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                username TEXT,
                user_agent TEXT,
                device_type TEXT,
                browser TEXT,
                os TEXT,
                ip_address TEXT,
                subscription_endpoint TEXT,
                subscription_keys TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ Successfully created fcm_tokens table!")
        
        # Verify the table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fcm_tokens'")
        if cursor.fetchone():
            print("✅ Table verification successful!")
            
            # Show table structure
            cursor.execute("PRAGMA table_info(fcm_tokens)")
            columns = cursor.fetchall()
            print("\n📋 Table structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            return True
        else:
            print("❌ Table creation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error creating fcm_tokens table: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def check_database_tables():
    """Check what tables exist in the database"""
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📊 Database tables ({len(tables)} total):")
        for table in tables:
            print(f"  - {table[0]}")
            
    except Exception as e:
        print(f"Error checking tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Adding fcm_tokens table to existing database...")
    
    # Show current database state
    check_database_tables()
    
    # Add the table
    success = add_fcm_tokens_table()
    
    if success:
        print("\n✅ Database update completed successfully!")
        print("🎉 You can now enable push notifications in your PWA!")
    else:
        print("\n❌ Database update failed!")
        print("Please check the error messages above.") 