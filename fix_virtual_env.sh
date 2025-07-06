#!/bin/bash

echo "🔧 Fixing Virtual Environment and Dependencies"
echo "============================================="

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
echo "🔧 Step 2: Checking virtual environment..."
cd /home/ubuntu/Fastag

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found, creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

echo ""
echo "🔧 Step 3: Activating virtual environment and installing dependencies..."
source venv/bin/activate
echo "✅ Virtual environment activated: $VIRTUAL_ENV"

echo "Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "🔧 Step 4: Testing with virtual environment..."
# Test Flask import
python3 -c "import flask; print('✅ Flask imported successfully')" 2>&1 || echo "❌ Flask import failed"

# Test Gunicorn import
python3 -c "import gunicorn; print('✅ Gunicorn imported successfully')" 2>&1 || echo "❌ Gunicorn import failed"

echo ""
echo "🔧 Step 5: Testing app import with virtual environment..."
python3 -c "from fastag import app; print('✅ App import successful')" 2>&1 || {
    echo "❌ App import failed"
    echo "Testing create_app import:"
    python3 -c "from fastag import create_app; app = create_app(); print('✅ create_app works')" 2>&1 || echo "❌ create_app also failed"
}

echo ""
echo "🔧 Step 6: Testing database connection..."
python3 -c "
from fastag import app
with app.app_context():
    from fastag.utils.db import get_db
    db = get_db()
    print('✅ Database connection successful')
    # Test a simple query
    try:
        result = db.execute('SELECT COUNT(*) FROM locations').fetchone()
        print(f'✅ Database query successful: {result[0]} locations found')
    except Exception as e:
        print(f'⚠️  Database query failed: {e}')
" 2>&1 || echo "❌ Database connection failed"

echo ""
echo "🔧 Step 7: Testing Gunicorn with virtual environment..."
# Test Gunicorn startup with proper virtual environment
timeout 10s ./venv/bin/gunicorn --bind 127.0.0.1:8001 wsgi:app --workers 1 --timeout 30 || {
    echo "❌ Gunicorn startup failed"
    echo "Testing with create_app directly:"
    timeout 10s ./venv/bin/gunicorn --bind 127.0.0.1:8002 "fastag:create_app()" --workers 1 --timeout 30 || echo "❌ Direct create_app also failed"
}

echo ""
echo "🔧 Step 8: Updating systemd service to use virtual environment..."
# Create a proper systemd service that uses the virtual environment
sudo tee /etc/systemd/system/fastag.service > /dev/null << 'EOF'
[Unit]
Description=Fastag Gunicorn Application
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/Fastag
Environment=PATH=/home/ubuntu/Fastag/venv/bin
ExecStart=/home/ubuntu/Fastag/venv/bin/gunicorn --bind 127.0.0.1:8000 wsgi:app --workers 2 --timeout 60 --access-logfile /home/ubuntu/Fastag/logs/gunicorn_access.log --error-logfile /home/ubuntu/Fastag/logs/gunicorn_error.log
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "🔧 Step 9: Creating logs directory..."
mkdir -p /home/ubuntu/Fastag/logs
chown ubuntu:ubuntu /home/ubuntu/Fastag/logs

echo ""
echo "🔧 Step 10: Reloading systemd and starting services..."
systemctl daemon-reload
systemctl enable fastag
systemctl start fastag
sleep 5

echo ""
echo "🔧 Step 11: Starting Nginx..."
systemctl start nginx

echo ""
echo "🔧 Step 12: Testing services..."
echo "Testing Gunicorn:"
curl -I http://localhost:8000 2>/dev/null | head -1 || echo "Gunicorn not responding"

echo "Testing Nginx:"
curl -I http://localhost 2>/dev/null | head -1 || echo "Nginx not responding"

echo ""
echo "🔧 Step 13: Testing website..."
echo "Testing HTTPS:"
curl -I https://fastag.onebee.in 2>/dev/null | head -1 || echo "HTTPS not responding"

echo ""
echo "🎯 Fix completed!"
echo "If the issue persists, check the logs:"
echo "sudo journalctl -u fastag -f"
echo "sudo tail -f /home/ubuntu/Fastag/logs/gunicorn_error.log" 