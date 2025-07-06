#!/bin/bash

# Quick fix to ensure Nginx uses the correct static files path
# Run this to fix the permission denied errors

set -e

echo "🔧 Quick Nginx Static Files Fix"
echo "==============================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

NGINX_CONFIG="/etc/nginx/sites-available/fastag"

echo "🔍 Step 1: Checking current Nginx configuration..."
echo "📋 Current static files path in config:"
grep -A 5 "location /static/" "$NGINX_CONFIG" || echo "Static location not found"

echo ""
echo "🔧 Step 2: Fixing static files path..."
# Replace the old path with the correct path
sudo sed -i 's|alias /home/ubuntu/Fastag/fastag/static/;|alias /var/www/fastag_static/;|' "$NGINX_CONFIG"

echo "✅ Static files path updated"

echo ""
echo "🔍 Step 3: Verifying the fix..."
echo "📋 Updated static files path in config:"
grep -A 5 "location /static/" "$NGINX_CONFIG" || echo "Static location not found"

echo ""
echo "🔧 Step 4: Testing Nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

echo ""
echo "🔄 Step 5: Restarting Nginx..."
systemctl restart nginx

echo ""
echo "🧪 Step 6: Testing static files..."
sleep 2
if curl -s -I http://localhost/static/logo.png | grep -q "200 OK"; then
    echo "✅ Static files are now accessible via HTTP"
else
    echo "❌ Static files still not accessible via HTTP"
fi

if curl -s -I https://fastag.onebee.in/static/logo.png | grep -q "200 OK"; then
    echo "✅ Static files are now accessible via HTTPS"
else
    echo "❌ Static files still not accessible via HTTPS"
fi

echo ""
echo "🎯 Fix completed!"
echo "Static files should now be accessible at:"
echo "   http://localhost/static/logo.png"
echo "   https://fastag.onebee.in/static/logo.png" 