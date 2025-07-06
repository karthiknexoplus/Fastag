#!/bin/bash

# Fix Database Connection Issues
# Run this to diagnose and fix database problems

set -e

echo "🔧 Fixing Database Connection Issues"
echo "==================================="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

cd /home/ubuntu/Fastag

echo "🔍 Step 1: Checking current database status..."
echo "Database file:"
ls -la instance/fastag.db

echo ""
echo "Database permissions:"
sudo chown ubuntu:ubuntu instance/fastag.db
sudo chmod 644 instance/fastag.db

echo ""
echo "🔍 Step 2: Testing database connection..."
source venv/bin/activate

# Test database connection
python3 -c "
import sqlite3
import os

# Test direct database access
db_path = '/home/ubuntu/Fastag/instance/fastag.db'
print(f'Testing database: {db_path}')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
    tables = cursor.fetchall()
    print(f'✅ Database accessible - Found {len(tables)} tables:')
    for table in tables:
        print(f'   - {table[0]}')
    
    # Check users table
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    print(f'✅ Users in database: {user_count}')
    
    # Check locations table
    cursor.execute('SELECT COUNT(*) FROM locations')
    location_count = cursor.fetchone()[0]
    print(f'✅ Locations in database: {location_count}')
    
    conn.close()
    print('✅ Database connection test successful')
    
except Exception as e:
    print(f'❌ Database error: {e}')
    exit(1)
"

echo ""
echo "🔍 Step 3: Testing Flask app database connection..."
python3 -c "
from fastag import create_app
app = create_app()

with app.app_context():
    from fastag.utils.db import get_db
    try:
        db = get_db()
        print('✅ Flask database connection successful')
        
        # Test a simple query
        result = db.execute('SELECT COUNT(*) FROM users').fetchone()
        print(f'✅ User count query successful: {result[0]} users')
        
    except Exception as e:
        print(f'❌ Flask database error: {e}')
        import traceback
        traceback.print_exc()
"

echo ""
echo "🔧 Step 4: Re-initializing database if needed..."
python3 init_database.py

echo ""
echo "🔧 Step 5: Restarting services..."
sudo systemctl restart fastag
sleep 3

echo ""
echo "🧪 Step 6: Testing login functionality..."
echo "Testing login page..."
if curl -s -I "http://localhost:8000/login" | grep -q "200 OK"; then
    echo "✅ Login page is accessible"
else
    echo "❌ Login page is not accessible"
fi

echo ""
echo "🎯 Database fix completed!"
echo ""
echo "📝 Next steps:"
echo "1. Try logging in with any username/password"
echo "2. Try signing up with a new account"
echo "3. If still getting errors, check the logs:"
echo "   sudo journalctl -u fastag -f" 