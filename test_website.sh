#!/bin/bash

echo "🧪 Testing Website Functionality"
echo "==============================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

echo ""
echo "🧪 Step 1: Testing local services..."
echo "Testing Gunicorn directly:"
curl -s -I http://localhost:8000 | head -1 || echo "❌ Gunicorn not responding"

echo ""
echo "Testing Nginx proxy:"
curl -s -I http://localhost | head -1 || echo "❌ Nginx not responding"

echo ""
echo "🧪 Step 2: Testing HTTPS website..."
echo "Testing main page:"
curl -s -I https://fastag.onebee.in | head -1 || echo "❌ HTTPS not responding"

echo ""
echo "Testing static files:"
curl -s -I https://fastag.onebee.in/static/logo.png | head -1 || echo "❌ Static files not accessible"

echo ""
echo "🧪 Step 3: Testing API endpoints..."
echo "Testing API endpoint:"
curl -s -I https://fastag.onebee.in/api/device/00:00:00:00 | head -1 || echo "❌ API not responding"

echo ""
echo "🧪 Step 4: Testing application routes..."
echo "Testing login page (should redirect):"
curl -s -I https://fastag.onebee.in/ | head -1 || echo "❌ Root route not responding"

echo ""
echo "🧪 Step 5: Checking service status..."
echo "Gunicorn status:"
systemctl is-active fastag
echo "Nginx status:"
systemctl is-active nginx

echo ""
echo "🧪 Step 6: Checking recent logs..."
echo "Recent Gunicorn logs:"
sudo journalctl -u fastag --no-pager -n 5

echo ""
echo "🧪 Step 7: Testing with curl verbose..."
echo "Testing website with verbose output:"
curl -v https://fastag.onebee.in 2>&1 | head -10

echo ""
echo "🎯 Test Summary:"
echo "✅ If you see 302/301 responses above, the website is working correctly!"
echo "✅ The redirects indicate the application is functioning properly."
echo "✅ You can now access your website at: https://fastag.onebee.in"
echo ""
echo "📝 To access the admin panel:"
echo "1. Go to https://fastag.onebee.in"
echo "2. You should be redirected to the login page"
echo "3. Use your admin credentials to log in"
echo ""
echo "🔧 If you need to check logs:"
echo "sudo journalctl -u fastag -f"
echo "sudo tail -f /home/ubuntu/Fastag/logs/gunicorn_error.log" 