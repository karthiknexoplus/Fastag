#!/bin/bash

echo "🔧 Quick Fix for Internal Server Error"
echo "======================================"

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
echo "🔧 Step 2: Checking application files..."
cd /home/ubuntu/Fastag

# Check if all required files exist
if [ ! -f "wsgi.py" ]; then
    echo "❌ wsgi.py not found"
    exit 1
fi

if [ ! -f "fastag/__init__.py" ]; then
    echo "❌ fastag/__init__.py not found"
    exit 1
fi

echo "✅ Application files found"

echo ""
echo "🔧 Step 3: Checking Python environment..."
# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  No virtual environment found, using system Python"
fi

echo ""
echo "🔧 Step 4: Installing/updating dependencies..."
pip install -r requirements.txt

echo ""
echo "🔧 Step 5: Testing application import..."
python3 -c "from fastag import app; print('✅ App imports successfully')" 2>&1 || {
    echo "❌ App import failed"
    echo "Testing individual imports..."
    python3 -c "import flask; print('Flask OK')" 2>&1 || echo "Flask import failed"
    python3 -c "import gunicorn; print('Gunicorn OK')" 2>&1 || echo "Gunicorn import failed"
    exit 1
}

echo ""
echo "🔧 Step 6: Testing Gunicorn startup..."
# Test if Gunicorn can start the app
timeout 10s gunicorn --bind 127.0.0.1:8001 wsgi:app --workers 1 --timeout 30 || {
    echo "❌ Gunicorn startup failed"
    echo "Testing with debug mode..."
    python3 -c "from fastag import app; app.run(debug=True, host='127.0.0.1', port=8001)" &
    sleep 3
    curl -I http://localhost:8001 2>/dev/null | head -1 || echo "Debug mode also failed"
    pkill -f "python3.*app.run"
    exit 1
}

echo "✅ Gunicorn startup test passed"

echo ""
echo "🔧 Step 7: Creating working service configuration..."
# Create a working systemd service file
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
echo "🔧 Step 8: Creating logs directory..."
mkdir -p /home/ubuntu/Fastag/logs
chown ubuntu:ubuntu /home/ubuntu/Fastag/logs

echo ""
echo "🔧 Step 9: Reloading systemd and starting services..."
systemctl daemon-reload
systemctl enable fastag
systemctl start fastag
sleep 5

echo ""
echo "🔧 Step 10: Starting Nginx..."
systemctl start nginx

echo ""
echo "🔧 Step 11: Testing services..."
echo "Testing Gunicorn:"
curl -I http://localhost:8000 2>/dev/null | head -1 || echo "Gunicorn not responding"

echo "Testing Nginx:"
curl -I http://localhost 2>/dev/null | head -1 || echo "Nginx not responding"

echo ""
echo "🔧 Step 12: Testing website..."
echo "Testing HTTPS:"
curl -I https://fastag.onebee.in 2>/dev/null | head -1 || echo "HTTPS not responding"

echo ""
echo "🎯 Fix completed!"
echo "If the issue persists, run:"
echo "sudo ./emergency-recovery.sh" 