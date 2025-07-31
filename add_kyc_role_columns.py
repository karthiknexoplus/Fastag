#!/usr/bin/env python3
"""
Add role and status columns to kyc_users table.
This script will add user_role and is_active columns to the existing kyc_users table.
"""
import sqlite3
import os

DATABASE_PATH = 'instance/fastag.db'

def add_kyc_role_columns():
    """Add user_role and is_active columns to kyc_users table"""
    
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        print("Please ensure the database exists first.")
        return False
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(kyc_users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        changes_made = False
        
        # Add user_role column if it doesn't exist
        if 'user_role' not in columns:
            cursor.execute('ALTER TABLE kyc_users ADD COLUMN user_role TEXT DEFAULT "tenant"')
            print("✅ Added user_role column to kyc_users table")
            changes_made = True
        else:
            print("✅ user_role column already exists")
        
        # Add is_active column if it doesn't exist
        if 'is_active' not in columns:
            cursor.execute('ALTER TABLE kyc_users ADD COLUMN is_active BOOLEAN DEFAULT 1')
            print("✅ Added is_active column to kyc_users table")
            changes_made = True
        else:
            print("✅ is_active column already exists")
        
        conn.commit()
        
        # Show current table structure
        cursor.execute("PRAGMA table_info(kyc_users)")
        columns = cursor.fetchall()
        print(f"\n📋 Current kyc_users table structure:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
        # Show sample data
        cursor.execute("SELECT id, name, user_role, is_active FROM kyc_users LIMIT 5")
        users = cursor.fetchall()
        print(f"\n👥 Sample KYC users:")
        for user in users:
            print(f"  - {user[1]} (Role: {user[2]}, Active: {user[3]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding columns: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Adding role and status columns to kyc_users table...")
    success = add_kyc_role_columns()
    
    if success:
        print("\n✅ KYC users table updated successfully!")
        print("🎉 You can now access the KYC management page.")
    else:
        print("\n❌ Failed to update kyc_users table.") 