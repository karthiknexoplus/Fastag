#!/bin/bash

# Fastag Internal Server Error Troubleshooting Script
# Run this on your EC2 instance to diagnose and fix issues

set -e

echo "🔍 Fastag Internal Server Error Troubleshooting"
echo "================================================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

FASTAG_DIR="/home/ubuntu/Fastag"
PYTHON_EXEC=""

echo "📁 Checking Fastag installation..."
if [ ! -d "$FASTAG_DIR" ]; then
    echo "❌ Fastag directory not found at $FASTAG_DIR"
    exit 1
fi

echo "✅ Fastag directory found"

# Check Python virtual environment
echo "🐍 Checking Python virtual environment..."
if [ -f "$FASTAG_DIR/venv/bin/python3" ]; then
    PYTHON_EXEC="$FASTAG_DIR/venv/bin/python3"
elif [ -f "$FASTAG_DIR/venv/bin/python" ]; then
    PYTHON_EXEC="$FASTAG_DIR/venv/bin/python"
else
    echo "❌ Python virtual environment not found"
    echo "Recreating virtual environment..."
    cd "$FASTAG_DIR"
    sudo -u ubuntu /usr/bin/python3 -m venv venv
    if [ -f "venv/bin/python3" ]; then
        PYTHON_EXEC="venv/bin/python3"
    else
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

echo "✅ Using Python: $PYTHON_EXEC"

# Check if requirements are installed
echo "📚 Checking Python dependencies..."
cd "$FASTAG_DIR"
if ! sudo -u ubuntu "$PYTHON_EXEC" -c "import flask" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    sudo -u ubuntu "$PYTHON_EXEC" -m pip install -r requirements.txt
else
    echo "✅ Python dependencies are installed"
fi

# Check database
echo "🗄️ Checking database..."
if [ ! -f "$FASTAG_DIR/instance/fastag.db" ]; then
    echo "🗄️ Initializing database..."
    sudo -u ubuntu "$PYTHON_EXEC" init_database.py
else
    echo "✅ Database exists"
fi

# Test database connection
echo "🧪 Testing database connection..."
if ! sudo -u ubuntu "$PYTHON_EXEC" -c "
from fastag import create_app
app = create_app()
with app.app_context():
    from fastag.utils.db import get_db
    db = get_db()
    print('✅ Database connection successful')
" 2>/dev/null; then
    echo "❌ Database connection failed"
    echo "Reinitializing database..."
    sudo -u ubuntu "$PYTHON_EXEC" init_database.py
fi

# Check file permissions
echo "🔐 Checking file permissions..."
chown -R ubuntu:ubuntu "$FASTAG_DIR"
chmod -R 755 "$FASTAG_DIR"
chmod 644 "$FASTAG_DIR/instance/fastag.db"

# Fix static files permissions
echo "🖼️ Fixing static files permissions..."
chown -R ubuntu:www-data "$FASTAG_DIR/fastag/static/"
chmod -R 755 "$FASTAG_DIR/fastag/static/"
chmod 644 "$FASTAG_DIR/fastag/static/"*

# Check logs directory
echo "📝 Setting up logs directory..."
mkdir -p "$FASTAG_DIR/logs"
chown ubuntu:ubuntu "$FASTAG_DIR/logs"
chmod 755 "$FASTAG_DIR/logs"

# Test Flask application
echo "🧪 Testing Flask application..."
cd "$FASTAG_DIR"
if ! sudo -u ubuntu "$PYTHON_EXEC" -c "
from fastag import create_app
app = create_app()
print('✅ Flask application loads successfully')
" 2>/dev/null; then
    echo "❌ Flask application failed to load"
    echo "Checking for import errors..."
    sudo -u ubuntu "$PYTHON_EXEC" -c "from fastag import create_app" 2>&1
    exit 1
fi

# Check systemd service
echo "⚙️ Checking systemd service..."
if [ ! -f "/etc/systemd/system/fastag.service" ]; then
    echo "📋 Creating systemd service..."
    cp "$FASTAG_DIR/fastag.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable fastag
else
    echo "✅ Systemd service exists"
fi

# Check service status
echo "📊 Checking service status..."
systemctl status fastag --no-pager || true

# Restart service
echo "🔄 Restarting Fastag service..."
systemctl restart fastag
sleep 3

# Check if service is running
if systemctl is-active --quiet fastag; then
    echo "✅ Fastag service is running"
else
    echo "❌ Fastag service failed to start"
    echo "📝 Service logs:"
    journalctl -u fastag --no-pager -n 20
    exit 1
fi

# Check Nginx
echo "🌐 Checking Nginx..."
if ! nginx -t; then
    echo "❌ Nginx configuration error"
    exit 1
fi

systemctl restart nginx

# Test local access
echo "🧪 Testing local access..."
sleep 2
if curl -s -I http://localhost:8000 | grep -q "200 OK\|302 Found"; then
    echo "✅ Application responds locally"
else
    echo "❌ Application not responding locally"
    echo "📝 Recent application logs:"
    journalctl -u fastag --no-pager -n 10
fi

# Test through Nginx
echo "🧪 Testing through Nginx..."
if curl -s -I http://localhost | grep -q "200 OK\|302 Found"; then
    echo "✅ Nginx proxy working"
else
    echo "❌ Nginx proxy not working"
    echo "📝 Nginx error logs:"
    tail -n 10 /var/log/nginx/fastag_error.log 2>/dev/null || echo "No error logs found"
fi

echo ""
echo "🔍 Additional troubleshooting steps:"
echo "1. Check application logs: sudo journalctl -u fastag -f"
echo "2. Check Nginx logs: sudo tail -f /var/log/nginx/fastag_error.log"
echo "3. Test application directly: curl http://localhost:8000"
echo "4. Check firewall: sudo ufw status"

echo ""
echo "🌐 Your application should now be accessible at:"
echo "   http://your-domain-or-ip"
echo ""
echo "If you still get errors, check the logs above for specific error messages." 