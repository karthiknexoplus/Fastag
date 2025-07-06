#!/bin/bash

echo "🔍 Diagnosing Static Files Issue"
echo "================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

echo ""
echo "📋 Step 1: Checking static files location..."
if [ -d "/var/www/fastag_static" ]; then
    echo "✅ Static files directory exists"
    ls -la /var/www/fastag_static/
    echo ""
    echo "📁 Files in static directory:"
    find /var/www/fastag_static -type f | head -10
else
    echo "❌ Static files directory not found"
fi

echo ""
echo "📋 Step 2: Checking file permissions..."
if [ -d "/var/www/fastag_static" ]; then
    echo "Permissions:"
    ls -ld /var/www/fastag_static/
    echo ""
    echo "Owner:"
    stat -c "%U:%G" /var/www/fastag_static/
fi

echo ""
echo "📋 Step 3: Checking Nginx configuration..."
if [ -f "/etc/nginx/sites-available/fastag" ]; then
    echo "✅ Nginx config exists"
    echo ""
    echo "Static files section:"
    grep -A 10 "location /static/" /etc/nginx/sites-available/fastag || echo "No static location found"
else
    echo "❌ Nginx config not found"
fi

echo ""
echo "📋 Step 4: Testing static file access..."
echo "Testing via localhost:"
curl -I http://localhost/static/logo.png 2>/dev/null | head -1 || echo "Failed to access via localhost"

echo ""
echo "📋 Step 5: Checking Nginx error logs..."
echo "Recent errors:"
sudo tail -10 /var/log/nginx/fastag_error.log 2>/dev/null || echo "No error log found"

echo ""
echo "📋 Step 6: Checking if Nginx is serving the site..."
echo "Nginx status:"
systemctl status nginx --no-pager -l

echo ""
echo "📋 Step 7: Testing HTTPS static access..."
echo "Testing HTTPS static file:"
curl -I https://fastag.onebee.in/static/logo.png 2>/dev/null | head -1 || echo "Failed to access via HTTPS"

echo ""
echo "🎯 Summary:"
echo "If static files are still not accessible, the issue might be:"
echo "1. File permissions (should be www-data:www-data)"
echo "2. Nginx configuration syntax"
echo "3. SSL certificate issues"
echo "4. Firewall blocking access" 