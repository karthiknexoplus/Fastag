#!/bin/bash

echo "🚨 Emergency Recovery for Internal Server Error"
echo "=============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

echo ""
echo "🔍 Step 1: Checking service status..."
echo "Gunicorn status:"
systemctl status fastag --no-pager -l

echo ""
echo "Nginx status:"
systemctl status nginx --no-pager -l

echo ""
echo "🔍 Step 2: Checking application logs..."
echo "Recent Gunicorn logs:"
sudo journalctl -u fastag --no-pager -n 20

echo ""
echo "🔍 Step 3: Checking Nginx error logs..."
echo "Recent Nginx errors:"
sudo tail -20 /var/log/nginx/fastag_error.log 2>/dev/null || echo "No error log found"

echo ""
echo "🔍 Step 4: Testing Gunicorn directly..."
echo "Testing localhost:8000:"
curl -I http://localhost:8000 2>/dev/null | head -1 || echo "Gunicorn not responding"

echo ""
echo "🔍 Step 5: Checking application files..."
echo "Checking if application files exist:"
ls -la /home/ubuntu/Fastag/fastag/
echo ""
echo "Checking wsgi.py:"
ls -la /home/ubuntu/Fastag/wsgi.py

echo ""
echo "🔍 Step 6: Checking Python environment..."
echo "Python version:"
python3 --version
echo ""
echo "Checking if virtual environment is active:"
echo $VIRTUAL_ENV

echo ""
echo "🔍 Step 7: Checking dependencies..."
echo "Checking requirements.txt:"
ls -la /home/ubuntu/Fastag/requirements.txt
echo ""
echo "Checking if packages are installed:"
pip list | grep -E "(flask|gunicorn)" || echo "Packages not found"

echo ""
echo "🔍 Step 8: Testing application startup..."
echo "Testing application startup:"
cd /home/ubuntu/Fastag
python3 -c "from fastag import app; print('App imports successfully')" 2>&1 || echo "App import failed"

echo ""
echo "🔧 Step 9: Attempting to restart services..."
echo "Restarting Gunicorn:"
systemctl restart fastag
sleep 5

echo "Restarting Nginx:"
systemctl restart nginx
sleep 3

echo ""
echo "🔍 Step 10: Final status check..."
echo "Gunicorn status after restart:"
systemctl is-active fastag
echo "Nginx status after restart:"
systemctl is-active nginx

echo ""
echo "🧪 Step 11: Testing website..."
echo "Testing HTTPS:"
curl -I https://fastag.onebee.in 2>/dev/null | head -1 || echo "HTTPS not responding"

echo ""
echo "🎯 Recovery completed!"
echo "If the issue persists, check:"
echo "1. sudo journalctl -u fastag -f"
echo "2. sudo tail -f /var/log/nginx/fastag_error.log"
echo "3. Check if database is accessible"
echo "4. Verify all environment variables are set" 