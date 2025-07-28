#!/usr/bin/env python3
"""
Add test KYC users to the database for testing search functionality
"""
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastag import create_app
from fastag.utils.db import get_db

def add_test_kyc_users():
    """Add test KYC users to the database"""
    print("➕ Adding Test KYC Users")
    print("=" * 50)
    
    # Test users data
    test_users = [
        {
            'name': 'Karthik Kumar',
            'fastag_id': '1234567890ABCDEF12345678',
            'vehicle_number': 'KA03KD1578',
            'contact_number': '9876543210',
            'address': 'Bangalore, Karnataka'
        },
        {
            'name': 'Karuna Sharma',
            'fastag_id': '2345678901BCDEF123456789',
            'vehicle_number': 'KA01AB1234',
            'contact_number': '8765432109',
            'address': 'Mysore, Karnataka'
        },
        {
            'name': 'Karan Singh',
            'fastag_id': '3456789012CDEF1234567890',
            'vehicle_number': 'KA02CD5678',
            'contact_number': '7654321098',
            'address': 'Mangalore, Karnataka'
        },
        {
            'name': 'Kavya Patel',
            'fastag_id': '4567890123DEF12345678901',
            'vehicle_number': 'KA04EF9012',
            'contact_number': '6543210987',
            'address': 'Hubli, Karnataka'
        },
        {
            'name': 'Krishna Reddy',
            'fastag_id': '5678901234EF123456789012',
            'vehicle_number': 'KA05GH3456',
            'contact_number': '5432109876',
            'address': 'Belgaum, Karnataka'
        }
    ]
    
    # Create app context
    app = create_app()
    with app.app_context():
        try:
            db = get_db()
            print("✅ Database connection successful")
            
            # Check existing users
            existing_count = db.execute('SELECT COUNT(*) FROM kyc_users').fetchone()[0]
            print(f"📊 Existing KYC users: {existing_count}")
            
            # Add test users
            added_count = 0
            for user in test_users:
                try:
                    db.execute('''
                        INSERT INTO kyc_users (name, fastag_id, vehicle_number, contact_number, address)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user['name'], user['fastag_id'], user['vehicle_number'], 
                          user['contact_number'], user['address']))
                    added_count += 1
                    print(f"✅ Added: {user['name']} | {user['vehicle_number']}")
                except Exception as e:
                    print(f"⚠️  Skipped {user['name']}: {e}")
            
            db.commit()
            print(f"\n🎉 Successfully added {added_count} test KYC users!")
            
            # Verify the users were added
            total_users = db.execute('SELECT COUNT(*) FROM kyc_users').fetchone()[0]
            print(f"📊 Total KYC users now: {total_users}")
            
            # Show all users
            print("\n📋 All KYC users in database:")
            users = db.execute('SELECT name, fastag_id, vehicle_number FROM kyc_users').fetchall()
            for user in users:
                print(f"  - {user[0]} | {user[1]} | {user[2]}")
            
            print("\n✅ Test users added successfully!")
            print("💡 Now you can test the search functionality in the watchlist page")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_test_kyc_users() 