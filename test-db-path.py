#!/usr/bin/env python3

import os
import sys

print("🔍 Database Path Test")
print("====================")

# Test config import
try:
    from config import Config
    print("✅ Config imported successfully")
    
    # Create config instance
    config = Config()
    print(f"✅ Config created")
    
    # Check database path
    db_path = config.DB_PATH
    print(f"📁 Database path: {db_path}")
    print(f"📁 Database directory: {os.path.dirname(db_path)}")
    print(f"📁 Current working directory: {os.getcwd()}")
    
    # Check if directory exists
    db_dir = os.path.dirname(db_path)
    if os.path.exists(db_dir):
        print(f"✅ Database directory exists: {db_dir}")
    else:
        print(f"❌ Database directory does not exist: {db_dir}")
        print("Creating directory...")
        os.makedirs(db_dir, exist_ok=True)
        print(f"✅ Database directory created: {db_dir}")
    
    # Check if database file exists
    if os.path.exists(db_path):
        print(f"✅ Database file exists: {db_path}")
        print(f"📊 File size: {os.path.getsize(db_path)} bytes")
    else:
        print(f"❌ Database file does not exist: {db_path}")
    
    # Test absolute path
    abs_path = os.path.abspath(db_path)
    print(f"🔗 Absolute path: {abs_path}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 