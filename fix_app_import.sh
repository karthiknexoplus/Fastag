#!/bin/bash

echo "🔧 Fixing App Import Issue"
echo "=========================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

echo ""
echo "🔧 Step 1: Stopping services..."
systemctl stop fastag
systemctl stop nginx

echo ""
echo "🔧 Step 2: Checking current app structure..."
cd /home/ubuntu/Fastag

echo "Testing app import:"
python3 -c "from fastag import app; print('✅ App import successful')" 2>&1 || {
    echo "❌ App import failed"
    echo "Testing create_app import:"
    python3 -c "from fastag import create_app; app = create_app(); print('✅ create_app works')" 2>&1 || echo "❌ create_app also failed"
}

echo ""
echo "🔧 Step 3: Testing database connection..."
python3 -c "
from fastag import app
with app.app_context():
    from fastag.utils.db import get_db
    db = get_db()
    print('✅ Database connection successful')
    # Test a simple query
    result = db.execute('SELECT COUNT(*) FROM locations').fetchone()
    print(f'✅ Database query successful: {result[0]} locations found')
" 2>&1 || echo "❌ Database connection failed"

echo ""
echo "🔧 Step 4: Testing routes..."
python3 -c "
from fastag import app
with app.test_client() as client:
    response = client.get('/')
    print(f'✅ Root route: {response.status_code}')
    response = client.get('/locations')
    print(f'✅ Locations route: {response.status_code}')
" 2>&1 || echo "❌ Route testing failed"

echo ""
echo "🔧 Step 5: Testing Gunicorn startup..."
timeout 10s gunicorn --bind 127.0.0.1:8001 wsgi:app --workers 1 --timeout 30 || {
    echo "❌ Gunicorn startup failed"
    echo "Testing with create_app directly:"
    timeout 10s gunicorn --bind 127.0.0.1:8002 "fastag:create_app()" --workers 1 --timeout 30 || echo "❌ Direct create_app also failed"
}

echo ""
echo "🔧 Step 6: Creating working wsgi.py..."
# Create a working wsgi.py that handles both import methods
sudo tee wsgi.py > /dev/null << 'EOF'
try:
    from fastag import app
except ImportError:
    from fastag import create_app
    app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
EOF

echo ""
echo "🔧 Step 7: Testing the new wsgi.py..."
python3 -c "from wsgi import app; print('✅ wsgi.py import successful')" 2>&1 || echo "❌ wsgi.py import failed"

echo ""
echo "🔧 Step 8: Starting services..."
systemctl start fastag
sleep 5
systemctl start nginx

echo ""
echo "🔧 Step 9: Testing services..."
echo "Testing Gunicorn:"
curl -I http://localhost:8000 2>/dev/null | head -1 || echo "Gunicorn not responding"

echo "Testing Nginx:"
curl -I http://localhost 2>/dev/null | head -1 || echo "Nginx not responding"

echo ""
echo "🔧 Step 10: Testing website..."
echo "Testing HTTPS:"
curl -I https://fastag.onebee.in 2>/dev/null | head -1 || echo "HTTPS not responding"

echo ""
echo "🎯 Fix completed!"
echo "If the issue persists, check the logs:"
echo "sudo journalctl -u fastag -f" 