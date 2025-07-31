#!/usr/bin/env python3
"""
Migrate existing FCM tokens from JSON files to the database.
This script will read tokens from fcm_tokens.json and push_subscriptions.json
and add them to the fcm_tokens table in the database.
"""
import json
import sqlite3
import os
from datetime import datetime

DATABASE_PATH = 'instance/fastag.db'

def migrate_tokens():
    """Migrate tokens from JSON files to database"""
    
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        print("Please run database initialization first.")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    migrated_count = 0
    
    # Migrate from fcm_tokens.json
    fcm_tokens_path = 'fcm_tokens.json'
    if os.path.exists(fcm_tokens_path):
        print(f"Migrating tokens from {fcm_tokens_path}...")
        try:
            with open(fcm_tokens_path, 'r') as f:
                tokens = json.load(f)
            
            for token in tokens:
                if token and token.strip():
                    # Check if token already exists
                    cursor.execute('SELECT id FROM fcm_tokens WHERE token = ?', (token,))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO fcm_tokens 
                            (token, username, device_type, browser, os, is_active, created_at, last_used)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            token, 'migrated_user', 'unknown', 'unknown', 'unknown', 
                            1, datetime.now(), datetime.now()
                        ))
                        migrated_count += 1
                        print(f"  ✓ Migrated token: {token[:20]}...")
                    else:
                        print(f"  - Token already exists: {token[:20]}...")
        except Exception as e:
            print(f"Error migrating from {fcm_tokens_path}: {e}")
    
    # Migrate from push_subscriptions.json
    push_subs_path = 'push_subscriptions.json'
    if os.path.exists(push_subs_path):
        print(f"Migrating subscriptions from {push_subs_path}...")
        try:
            with open(push_subs_path, 'r') as f:
                subscriptions = json.load(f)
            
            for sub in subscriptions:
                endpoint = sub.get('endpoint', '')
                if endpoint:
                    # Check if subscription already exists
                    cursor.execute('SELECT id FROM fcm_tokens WHERE subscription_endpoint = ?', (endpoint,))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO fcm_tokens 
                            (username, device_type, browser, os, subscription_endpoint, 
                             subscription_keys, is_active, created_at, last_used)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            'migrated_user', 'unknown', 'unknown', 'unknown', endpoint,
                            json.dumps(sub.get('keys', {})), 1, datetime.now(), datetime.now()
                        ))
                        migrated_count += 1
                        print(f"  ✓ Migrated subscription: {endpoint[:50]}...")
                    else:
                        print(f"  - Subscription already exists: {endpoint[:50]}...")
        except Exception as e:
            print(f"Error migrating from {push_subs_path}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Migration completed! Migrated {migrated_count} tokens/subscriptions to database.")
    
    # Show statistics
    show_database_stats()

def show_database_stats():
    """Show current database statistics"""
    if not os.path.exists(DATABASE_PATH):
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        total = cursor.execute('SELECT COUNT(*) FROM fcm_tokens').fetchone()[0]
        active = cursor.execute('SELECT COUNT(*) FROM fcm_tokens WHERE is_active = 1').fetchone()[0]
        inactive = cursor.execute('SELECT COUNT(*) FROM fcm_tokens WHERE is_active = 0').fetchone()[0]
        
        print(f"\n📊 Database Statistics:")
        print(f"  Total tokens: {total}")
        print(f"  Active tokens: {active}")
        print(f"  Inactive tokens: {inactive}")
        
        # Show device breakdown
        device_stats = cursor.execute('''
            SELECT device_type, COUNT(*) 
            FROM fcm_tokens 
            WHERE is_active = 1 
            GROUP BY device_type
        ''').fetchall()
        
        if device_stats:
            print(f"\n📱 Device Types:")
            for device_type, count in device_stats:
                print(f"  {device_type}: {count}")
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 Starting FCM token migration...")
    migrate_tokens() 