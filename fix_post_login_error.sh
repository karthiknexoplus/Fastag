#!/bin/bash

echo "🔧 Fixing Post-Login Internal Server Error"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

echo ""
echo "🔍 Step 1: Checking recent error logs..."
echo "Recent Gunicorn error logs:"
sudo journalctl -u fastag --no-pager -n 20

echo ""
echo "Recent application logs:"
sudo tail -20 /home/ubuntu/Fastag/logs/gunicorn_error.log 2>/dev/null || echo "No gunicorn error log found"

echo ""
echo "🔍 Step 2: Checking database..."
cd /home/ubuntu/Fastag
source venv/bin/activate

echo "Testing database connection:"
python3 -c "
from fastag import app
with app.app_context():
    from fastag.utils.db import get_db
    db = get_db()
    print('✅ Database connection successful')
    
    # Check if tables exist
    tables = db.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
    print(f'✅ Found {len(tables)} tables: {[t[0] for t in tables]}')
    
    # Check users table
    try:
        users = db.execute('SELECT COUNT(*) FROM users').fetchone()
        print(f'✅ Users table: {users[0]} users found')
    except Exception as e:
        print(f'❌ Users table error: {e}')
    
    # Check locations table
    try:
        locations = db.execute('SELECT COUNT(*) FROM locations').fetchall()
        print(f'✅ Locations table: {locations[0][0]} locations found')
    except Exception as e:
        print(f'❌ Locations table error: {e}')
" 2>&1

echo ""
echo "🔍 Step 3: Testing authentication routes..."
python3 -c "
from fastag import app
with app.test_client() as client:
    # Test login page
    response = client.get('/login')
    print(f'✅ Login page: {response.status_code}')
    
    # Test home page (should redirect to login)
    response = client.get('/')
    print(f'✅ Root page: {response.status_code}')
    
    # Test with session
    with client.session_transaction() as sess:
        sess['user'] = 'admin'
    
    response = client.get('/')
    print(f'✅ Root page with session: {response.status_code}')
" 2>&1

echo ""
echo "🔍 Step 4: Checking route imports..."
python3 -c "
from fastag import app
print('✅ App created successfully')

# Test each blueprint import
try:
    from fastag.routes.auth import auth_bp
    print('✅ Auth blueprint imported')
except Exception as e:
    print(f'❌ Auth blueprint error: {e}')

try:
    from fastag.routes.locations import locations_bp
    print('✅ Locations blueprint imported')
except Exception as e:
    print(f'❌ Locations blueprint error: {e}')

try:
    from fastag.routes.lanes import lanes_bp
    print('✅ Lanes blueprint imported')
except Exception as e:
    print(f'❌ Lanes blueprint error: {e}')

try:
    from fastag.routes.readers import readers_bp
    print('✅ Readers blueprint imported')
except Exception as e:
    print(f'❌ Readers blueprint error: {e}')

try:
    from fastag.routes.api import api
    print('✅ API blueprint imported')
except Exception as e:
    print(f'❌ API blueprint error: {e}')
" 2>&1

echo ""
echo "🔧 Step 5: Checking and fixing database schema..."
python3 -c "
from fastag import app
with app.app_context():
    from fastag.utils.db import get_db, init_db
    db = get_db()
    
    # Check if database needs initialization
    try:
        result = db.execute('SELECT COUNT(*) FROM users').fetchone()
        print(f'✅ Database has {result[0]} users')
    except Exception as e:
        print(f'⚠️  Database needs initialization: {e}')
        print('Initializing database...')
        init_db()
        print('✅ Database initialized')
" 2>&1

echo ""
echo "🔧 Step 6: Creating test admin user..."
python3 -c "
from fastag import app
with app.app_context():
    from fastag.utils.db import get_db
    db = get_db()
    
    # Check if admin user exists
    admin = db.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if admin:
        print('✅ Admin user exists')
    else:
        print('⚠️  Creating admin user...')
        db.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                  ('admin', 'admin123', 'admin'))
        db.commit()
        print('✅ Admin user created (username: admin, password: admin123)')
" 2>&1

echo ""
echo "🔧 Step 7: Restarting services..."
systemctl restart fastag
sleep 5

echo ""
echo "🔧 Step 8: Testing website after restart..."
echo "Testing login page:"
curl -s -I https://fastag.onebee.in/login | head -1 || echo "❌ Login page not accessible"

echo ""
echo "🎯 Fix completed!"
echo "Try logging in with:"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo "If issues persist, check:"
echo "sudo journalctl -u fastag -f"
echo "sudo tail -f /home/ubuntu/Fastag/logs/gunicorn_error.log" 