#!/bin/bash

# Diagnose Gunicorn Startup Issues
# Run this to see why Gunicorn is not responding

set -e

echo "🔍 Diagnosing Gunicorn Issues"
echo "============================="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

cd /home/ubuntu/Fastag

echo "🔍 Step 1: Checking Gunicorn service status..."
sudo systemctl status fastag --no-pager

echo ""
echo "🔍 Step 2: Checking recent Gunicorn logs..."
sudo journalctl -u fastag -n 20 --no-pager

echo ""
echo "🔍 Step 3: Checking if port 8000 is listening..."
sudo netstat -tlnp | grep :8000 || echo "❌ Port 8000 is not listening"

echo ""
echo "🔍 Step 4: Testing direct Gunicorn startup..."
echo "Stopping service first..."
sudo systemctl stop fastag

echo "Testing Gunicorn manually..."
cd /home/ubuntu/Fastag
source venv/bin/activate

# Test if the Flask app can be imported
echo "Testing Flask app import..."
python3 -c "
try:
    from fastag import create_app
    app = create_app()
    print('✅ Flask app imported successfully')
except Exception as e:
    print(f'❌ Flask app import error: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "Testing Gunicorn startup..."
timeout 10s gunicorn --bind 127.0.0.1:8000 --workers 1 --timeout 30 'fastag:create_app()' || echo "❌ Gunicorn startup failed"

echo ""
echo "🔍 Step 5: Checking for common issues..."

# Check if gunicorn config exists
if [ -f "gunicorn.conf.py" ]; then
    echo "✅ Gunicorn config file exists"
    echo "Contents:"
    cat gunicorn.conf.py
else
    echo "❌ Gunicorn config file missing"
fi

echo ""
echo "🔍 Step 6: Checking file permissions..."
ls -la /home/ubuntu/Fastag/
ls -la /home/ubuntu/Fastag/instance/

echo ""
echo "🔍 Step 7: Restarting service..."
sudo systemctl restart fastag
sleep 5

echo ""
echo "🔍 Step 8: Final test..."
if curl -s -I "http://localhost:8000" | head -1; then
    echo "✅ Gunicorn is now responding!"
else
    echo "❌ Gunicorn is still not responding"
    echo "Check the logs above for errors"
fi

echo ""
echo "🎯 Diagnosis completed!"
echo "If Gunicorn is still not working, the logs above will show the exact error." 