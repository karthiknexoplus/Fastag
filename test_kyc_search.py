#!/usr/bin/env python3
"""
Test script to verify KYC search functionality
"""
import sqlite3
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastag import create_app
from fastag.utils.db import get_db

def test_kyc_search():
    """Test the KYC search functionality"""
    print("🔍 Testing KYC Search Functionality")
    print("=" * 50)
    
        # Create app context
    app = create_app()
    with app.app_context():
        # Test database connection
        try:
            db = get_db()
            print("✅ Database connection successful")
            
            # Check if kyc_users table exists and has data
            users = db.execute('SELECT COUNT(*) FROM kyc_users').fetchone()
            total_users = users[0] if users else 0
            print(f"📊 Total KYC users in database: {total_users}")
            
            if total_users == 0:
                print("⚠️  No KYC users found in database!")
                print("💡 Add some KYC users first through the web interface")
                return
            
            # Show some sample users
            sample_users = db.execute('SELECT name, fastag_id, vehicle_number FROM kyc_users LIMIT 5').fetchall()
            print("\n📋 Sample KYC users:")
            for user in sample_users:
                print(f"  - {user[0]} | {user[1]} | {user[2]}")
            
            # Test search functionality
            print("\n🔎 Testing search functionality:")
            test_queries = ['Kar', 'KA', 'test', 'user']
            
            for query in test_queries:
                results = db.execute('''
                    SELECT fastag_id, name, vehicle_number
                    FROM kyc_users
                    WHERE name LIKE ? OR vehicle_number LIKE ?
                    ORDER BY name ASC
                    LIMIT 5
                ''', (f'%{query}%', f'%{query}%')).fetchall()
                
                print(f"  Search for '{query}': {len(results)} results")
                for result in results:
                    print(f"    - {result[1]} | {result[0]} | {result[2]}")
            
            print("\n✅ KYC search test completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_kyc_search() 