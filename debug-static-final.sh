#!/bin/bash

# Final comprehensive debug script for static files
# Run this to get detailed information about the static files issue

set -e

echo "🔍 Final Static Files Debug"
echo "============================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

FASTAG_DIR="/home/ubuntu/Fastag"
STATIC_DIR="$FASTAG_DIR/fastag/static"

echo "📁 Checking static files directory..."
if [ ! -d "$STATIC_DIR" ]; then
    echo "❌ Static files directory not found"
    exit 1
fi

echo "✅ Static files directory found"

echo ""
echo "🔍 Step 1: File existence and permissions"
echo "=========================================="

echo "📋 Static files in directory:"
ls -la "$STATIC_DIR"

echo ""
echo "🔍 Step 2: Directory tree permissions"
echo "====================================="

echo "📁 Parent directory permissions:"
ls -la "$FASTAG_DIR" | head -3
ls -la "$FASTAG_DIR/fastag/" | head -3

echo ""
echo "🔍 Step 3: Nginx user and group"
echo "==============================="

echo "👤 Nginx user info:"
id www-data

echo ""
echo "👥 Current file ownership:"
stat -c "%U:%G %a %n" "$STATIC_DIR"
stat -c "%U:%G %a %n" "$STATIC_DIR"/*

echo ""
echo "🔍 Step 4: Testing file access"
echo "=============================="

echo "🧪 Testing as nginx user:"
sudo -u www-data test -r "$STATIC_DIR/logo.png" && echo "✅ nginx can read logo.png" || echo "❌ nginx cannot read logo.png"
sudo -u www-data test -r "$STATIC_DIR/branding.jpg" && echo "✅ nginx can read branding.jpg" || echo "❌ nginx cannot read branding.jpg"

echo ""
echo "🔍 Step 5: Nginx configuration"
echo "=============================="

echo "📋 Current Nginx static location block:"
grep -A 10 "location /static/" /etc/nginx/sites-available/fastag

echo ""
echo "🔍 Step 6: Testing different access methods"
echo "==========================================="

echo "🧪 Testing localhost access:"
curl -s -I http://localhost/static/logo.png | head -1

echo ""
echo "🧪 Testing direct file access:"
sudo -u www-data cat "$STATIC_DIR/logo.png" > /dev/null && echo "✅ Direct file access works" || echo "❌ Direct file access fails"

echo ""
echo "🔍 Step 7: SELinux check (if applicable)"
echo "========================================"

if command -v sestatus >/dev/null 2>&1; then
    echo "🔒 SELinux status:"
    sestatus
else
    echo "ℹ️ SELinux not installed"
fi

echo ""
echo "🔍 Step 8: Alternative fixes to try"
echo "==================================="

echo "🔄 Trying alternative permission fix..."
chown -R www-data:www-data "$STATIC_DIR"
chmod -R 755 "$STATIC_DIR"
chmod 644 "$STATIC_DIR"/*

echo ""
echo "📋 Updated permissions:"
ls -la "$STATIC_DIR"

echo ""
echo "🧪 Testing after alternative fix:"
sleep 2
if curl -s -I http://localhost/static/logo.png | grep -q "200 OK"; then
    echo "✅ Static files now work with www-data ownership"
else
    echo "❌ Still not working, trying next fix..."
    
    echo ""
    echo "🔄 Trying symbolic link approach..."
    # Create a symbolic link in /tmp that nginx can access
    ln -sf "$STATIC_DIR" /tmp/fastag_static
    chmod 755 /tmp/fastag_static
    
    echo "📋 Testing symbolic link:"
    ls -la /tmp/fastag_static/
    
    echo ""
    echo "🧪 Testing symbolic link access:"
    if curl -s -I http://localhost/static/logo.png | grep -q "200 OK"; then
        echo "✅ Symbolic link approach works"
    else
        echo "❌ Symbolic link approach failed"
    fi
fi

echo ""
echo "🎯 Manual testing commands:"
echo "curl -v http://localhost/static/logo.png"
echo "curl -v https://fastag.onebee.in/static/logo.png"
echo ""
echo "📝 Check nginx error logs:"
echo "sudo tail -f /var/log/nginx/fastag_error.log" 