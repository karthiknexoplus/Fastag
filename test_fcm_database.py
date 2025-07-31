#!/usr/bin/env python3
"""
Test FCM database functionality to identify issues.
"""
import sqlite3
import os
import json

DATABASE_PATH = 'instance/fastag.db'

def test_database_connection():
    """Test basic database connection"""
    print("🔍 Testing database connection...")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found at {DATABASE_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"✅ Database connection successful (SQLite {version})")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_fcm_tokens_table():
    """Test fcm_tokens table access"""
    print("\n🔍 Testing fcm_tokens table...")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fcm_tokens'")
        if not cursor.fetchone():
            print("❌ fcm_tokens table does not exist!")
            print("Please run: python3 add_fcm_tokens_table.py")
            return False
        
        print("✅ fcm_tokens table exists")
        
        # Test table structure
        cursor.execute("PRAGMA table_info(fcm_tokens)")
        columns = cursor.fetchall()
        print(f"✅ Table has {len(columns)} columns")
        
        # Test insert operation
        test_token = "test_token_123"
        cursor.execute('''
            INSERT OR REPLACE INTO fcm_tokens 
            (token, username, device_type, browser, os, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (test_token, 'test_user', 'desktop', 'chrome', 'linux', 1))
        
        conn.commit()
        print("✅ Test insert successful")
        
        # Test select operation
        cursor.execute('SELECT COUNT(*) FROM fcm_tokens WHERE is_active = 1')
        count = cursor.fetchone()[0]
        print(f"✅ Active tokens count: {count}")
        
        # Clean up test data
        cursor.execute('DELETE FROM fcm_tokens WHERE token = ?', (test_token,))
        conn.commit()
        print("✅ Test cleanup successful")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ fcm_tokens table test failed: {e}")
        return False

def test_json_files():
    """Test JSON file operations"""
    print("\n🔍 Testing JSON file operations...")
    
    # Test fcm_tokens.json
    fcm_tokens_path = 'fcm_tokens.json'
    try:
        if os.path.exists(fcm_tokens_path):
            with open(fcm_tokens_path, 'r') as f:
                tokens = json.load(f)
            print(f"✅ fcm_tokens.json exists with {len(tokens)} tokens")
        else:
            print("ℹ️  fcm_tokens.json does not exist (will be created when needed)")
    except Exception as e:
        print(f"❌ Error reading fcm_tokens.json: {e}")
    
    # Test push_subscriptions.json
    push_subs_path = 'push_subscriptions.json'
    try:
        if os.path.exists(push_subs_path):
            with open(push_subs_path, 'r') as f:
                subs = json.load(f)
            print(f"✅ push_subscriptions.json exists with {len(subs)} subscriptions")
        else:
            print("ℹ️  push_subscriptions.json does not exist (will be created when needed)")
    except Exception as e:
        print(f"❌ Error reading push_subscriptions.json: {e}")

def show_database_info():
    """Show database information"""
    print("\n📊 Database Information:")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"Total tables: {len(tables)}")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")
        
        conn.close()
    except Exception as e:
        print(f"Error getting database info: {e}")

if __name__ == "__main__":
    print("🧪 Testing FCM database functionality...")
    
    # Run all tests
    db_ok = test_database_connection()
    table_ok = test_fcm_tokens_table() if db_ok else False
    test_json_files()
    show_database_info()
    
    print("\n" + "="*50)
    if db_ok and table_ok:
        print("✅ All tests passed! FCM functionality should work correctly.")
        print("🎉 You can now enable push notifications in your PWA.")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        if not db_ok:
            print("💡 Make sure the database exists and is accessible.")
        if not table_ok:
            print("💡 Run: python3 add_fcm_tokens_table.py") 