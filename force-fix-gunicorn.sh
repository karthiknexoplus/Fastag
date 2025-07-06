#!/bin/bash

# Force Fix Gunicorn - Show Exact Error
# This will show us exactly why Gunicorn is crashing

set -e

echo "🔧 Force Fixing Gunicorn"
echo "========================"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

cd /home/ubuntu/Fastag

echo "🔍 Step 1: Stopping all services..."
sudo systemctl stop fastag
sudo systemctl stop nginx

echo ""
echo "🔍 Step 2: Checking file permissions..."
sudo chown -R ubuntu:ubuntu /home/ubuntu/Fastag
sudo chmod -R 755 /home/ubuntu/Fastag
sudo chmod 644 /home/ubuntu/Fastag/instance/fastag.db

echo ""
echo "🔍 Step 3: Testing Flask app directly..."
source venv/bin/activate

echo "Testing Flask app import and startup..."
python3 -c "
import sys
import traceback

try:
    print('Importing Flask app...')
    from fastag import create_app
    print('✅ Flask app imported successfully')
    
    print('Creating app instance...')
    app = create_app()
    print('✅ App instance created successfully')
    
    print('Testing app context...')
    with app.app_context():
        print('✅ App context works')
        from fastag.utils.db import get_db
        print('✅ Database module imported')
        
        db = get_db()
        print('✅ Database connection successful')
        
        result = db.execute('SELECT COUNT(*) FROM users').fetchone()
        print(f'✅ Database query successful: {result[0]} users')
        
    print('✅ All Flask tests passed!')
    
except Exception as e:
    print(f'❌ Flask error: {e}')
    print('Full traceback:')
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "🔍 Step 4: Testing Gunicorn startup manually..."
echo "Starting Gunicorn in foreground to see errors..."

# Start Gunicorn in foreground to see the exact error
timeout 30s gunicorn --bind 127.0.0.1:8000 --workers 1 --timeout 30 --log-level debug 'fastag:create_app()' || echo "Gunicorn startup failed (expected)"

echo ""
echo "🔍 Step 5: Checking for missing dependencies..."
python3 -c "
import sys
required_modules = [
    'flask',
    'werkzeug',
    'sqlite3',
    'gunicorn'
]

for module in required_modules:
    try:
        __import__(module)
        print(f'✅ {module} is available')
    except ImportError as e:
        print(f'❌ {module} is missing: {e}')
"

echo ""
echo "🔍 Step 6: Checking database file..."
ls -la instance/fastag.db
file instance/fastag.db

echo ""
echo "🔍 Step 7: Testing database directly..."
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('instance/fastag.db')
    cursor = conn.cursor()
    cursor.execute('SELECT sqlite_version()')
    version = cursor.fetchone()
    print(f'✅ SQLite version: {version[0]}')
    
    cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
    tables = cursor.fetchall()
    print(f'✅ Tables found: {len(tables)}')
    for table in tables:
        print(f'   - {table[0]}')
    
    conn.close()
except Exception as e:
    print(f'❌ Database error: {e}')
"

echo ""
echo "🔍 Step 8: Creating a simple test Gunicorn config..."
cat > test_gunicorn.conf.py << 'EOF'
bind = "127.0.0.1:8000"
workers = 1
worker_class = "sync"
timeout = 30
loglevel = "debug"
accesslog = "-"
errorlog = "-"
EOF

echo ""
echo "🔍 Step 9: Testing with simple config..."
timeout 30s gunicorn --config test_gunicorn.conf.py 'fastag:create_app()' || echo "Simple config also failed"

echo ""
echo "🔍 Step 10: Checking system resources..."
echo "Memory usage:"
free -h

echo ""
echo "Disk space:"
df -h

echo ""
echo "🎯 Force fix completed!"
echo "The output above should show the exact error causing Gunicorn to crash." 