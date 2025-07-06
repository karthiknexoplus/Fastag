#!/usr/bin/env python3
"""
Simple test script to verify the Fastag Flask application
"""
import os
import sys
from fastag import create_app

def test_app():
    """Test that the app can be created and basic functionality works"""
    try:
        # Create the app
        app = create_app()
        print("✅ App created successfully")
        
        # Test database connection
        with app.app_context():
            from fastag.utils.db import get_db
            db = get_db()
            print("✅ Database connection successful")
            
            # Test tables exist
            tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [table['name'] for table in tables]
            expected_tables = ['users', 'activity_log', 'locations', 'lanes', 'readers']
            
            for table in expected_tables:
                if table in table_names:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")
            
            print(f"\n📊 Found {len(table_names)} tables: {', '.join(table_names)}")
        
        print("\n🎉 All tests passed! The app is ready to run.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_app()
    sys.exit(0 if success else 1) 