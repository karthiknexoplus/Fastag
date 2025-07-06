#!/usr/bin/env python3
"""
Test script to verify RFID setup works correctly
"""

import os
import sqlite3
import sys

def test_database_connection():
    """Test database connection and table creation"""
    print("🔍 Testing database connection...")
    
    # Check if database exists
    db_path = os.path.abspath(os.path.join('instance', 'fastag.db'))
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Please run init_database.py first")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if access_logs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='access_logs'")
        if not cursor.fetchone():
            print("❌ access_logs table not found")
            return False
        
        # Check if kyc_users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kyc_users'")
        if not cursor.fetchone():
            print("❌ kyc_users table not found")
            return False
        
        # Check if readers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='readers'")
        if not cursor.fetchone():
            print("❌ readers table not found")
            return False
        
        print("✅ All required tables exist")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_rfid_imports():
    """Test RFID service imports"""
    print("🔍 Testing RFID service imports...")
    
    try:
        # Test main RFID service
        sys.path.append('fastag/rfid')
        from fastag.rfid.rfid_service import RFIDService
        print("✅ Main RFID service imports successfully")
        
        # Test reader services
        from fastag.rfid.rfid_reader1_service import RFIDReader as Reader1
        from fastag.rfid.rfid_reader2_service import RFIDReader as Reader2
        print("✅ Reader services import successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_paths():
    """Test database paths in RFID services"""
    print("🔍 Testing database paths...")
    
    # Check main service path
    main_db_path = os.path.abspath(os.path.join('fastag', 'rfid', '..', '..', 'instance', 'fastag.db'))
    if not os.path.exists(main_db_path):
        print(f"❌ Main service database path not found: {main_db_path}")
        return False
    
    # Check reader service paths
    reader1_db_path = os.path.abspath(os.path.join('fastag', 'rfid', '..', '..', 'instance', 'fastag.db'))
    reader2_db_path = os.path.abspath(os.path.join('fastag', 'rfid', '..', '..', 'instance', 'fastag.db'))
    
    if not os.path.exists(reader1_db_path):
        print(f"❌ Reader 1 database path not found: {reader1_db_path}")
        return False
    
    if not os.path.exists(reader2_db_path):
        print(f"❌ Reader 2 database path not found: {reader2_db_path}")
        return False
    
    print("✅ All database paths are correct")
    return True

def test_logging_directories():
    """Test logging directory creation"""
    print("🔍 Testing logging directories...")
    
    try:
        # Test main service logging
        os.makedirs('logs', exist_ok=True)
        if not os.path.exists('logs'):
            print("❌ Could not create logs directory")
            return False
        
        # Test reader service logging
        reader_logs_dir = os.path.join('fastag', 'rfid', 'logs')
        os.makedirs(reader_logs_dir, exist_ok=True)
        if not os.path.exists(reader_logs_dir):
            print("❌ Could not create reader logs directory")
            return False
        
        print("✅ Logging directories created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Logging directory error: {e}")
        return False

def main():
    print("🧪 RFID Setup Test")
    print("=" * 30)
    
    tests = [
        test_database_connection,
        test_rfid_imports,
        test_database_paths,
        test_logging_directories
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RFID setup is ready.")
        print("\n📝 Next steps:")
        print("1. Add reader configurations to database")
        print("2. Add KYC users to database")
        print("3. Start RFID services")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 