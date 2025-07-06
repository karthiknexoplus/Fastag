#!/bin/bash

# Debug script for Option 2 (Flask/Gunicorn handling static files)
# Run this on your EC2 instance to diagnose the issue

set -e

echo "🔍 Debugging Option 2 - Flask/Gunicorn Static Files"
echo "===================================================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

FASTAG_DIR="/home/ubuntu/Fastag"
NGINX_CONFIG="/etc/nginx/sites-available/fastag"

echo "📁 Checking Fastag installation..."
if [ ! -d "$FASTAG_DIR" ]; then
    echo "❌ Fastag directory not found at $FASTAG_DIR"
    exit 1
fi

echo "✅ Fastag directory found"

echo ""
echo "🔍 Step 1: Checking service status"
echo "=================================="

echo "📊 Fastag service status:"
systemctl status fastag --no-pager || echo "Service not found"

echo ""
echo "📊 Nginx service status:"
systemctl status nginx --no-pager || echo "Service not found"

echo ""
echo "🔍 Step 2: Checking application logs"
echo "===================================="

echo "📝 Recent Fastag logs:"
journalctl -u fastag --no-pager -n 10 || echo "No logs found"

echo ""
echo "📝 Recent Nginx error logs:"
tail -n 10 /var/log/nginx/fastag_error.log 2>/dev/null || echo "No error logs found"

echo ""
echo "🔍 Step 3: Testing connectivity"
echo "==============================="

echo "🧪 Testing Gunicorn directly (port 8000):"
if curl -s -I http://localhost:8000 | head -1; then
    echo "✅ Gunicorn is responding"
else
    echo "❌ Gunicorn is not responding"
fi

echo ""
echo "🧪 Testing Nginx proxy (port 80):"
if curl -s -I http://localhost | head -1; then
    echo "✅ Nginx proxy is working"
else
    echo "❌ Nginx proxy is not working"
fi

echo ""
echo "🔍 Step 4: Checking Nginx configuration"
echo "======================================="

echo "📋 Current Nginx configuration:"
if [ -f "$NGINX_CONFIG" ]; then
    cat "$NGINX_CONFIG"
else
    echo "❌ Nginx configuration file not found"
fi

echo ""
echo "🧪 Testing Nginx configuration:"
if nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
fi

echo ""
echo "🔍 Step 5: Checking file permissions"
echo "===================================="

echo "📁 Application directory permissions:"
ls -la "$FASTAG_DIR" | head -5

echo ""
echo "📁 Static files permissions:"
ls -la "$FASTAG_DIR/fastag/static/" 2>/dev/null || echo "Static directory not found"

echo ""
echo "🔍 Step 6: Checking Python environment"
echo "======================================"

echo "🐍 Python virtual environment:"
ls -la "$FASTAG_DIR/venv/bin/python*" 2>/dev/null || echo "Python environment not found"

echo ""
echo "📚 Testing Python imports:"
cd "$FASTAG_DIR"
if sudo -u ubuntu venv/bin/python3 -c "from fastag import create_app; print('✅ Flask app imports successfully')" 2>/dev/null; then
    echo "✅ Flask application can be imported"
else
    echo "❌ Flask application import failed"
fi

echo ""
echo "🔍 Step 7: Manual fixes to try"
echo "=============================="

echo "🔄 Restarting services..."
systemctl restart fastag
sleep 3
systemctl restart nginx
sleep 2

echo ""
echo "🧪 Testing after restart:"
if curl -s -I http://localhost:8000 | head -1; then
    echo "✅ Gunicorn working after restart"
else
    echo "❌ Gunicorn still not working"
fi

if curl -s -I http://localhost | head -1; then
    echo "✅ Nginx working after restart"
else
    echo "❌ Nginx still not working"
fi

echo ""
echo "🎯 If still not working, try these manual fixes:"
echo ""
echo "1. Check if Gunicorn is actually running:"
echo "   sudo netstat -tlnp | grep 8000"
echo ""
echo "2. Check if there are any Python errors:"
echo "   sudo -u ubuntu $FASTAG_DIR/venv/bin/python3 -c 'from fastag import create_app; app = create_app()'"
echo ""
echo "3. Restart everything manually:"
echo "   sudo systemctl stop fastag"
echo "   sudo systemctl start fastag"
echo "   sudo systemctl restart nginx"
echo ""
echo "4. Check firewall:"
echo "   sudo ufw status"
echo ""
echo "5. Test with a simple curl:"
echo "   curl -v http://localhost:8000" 