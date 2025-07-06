#!/bin/bash

echo "🔍 Fastag Application Log Checker"
echo "================================="
echo ""

# Check if we're in the right directory
if [ ! -f "wsgi.py" ]; then
    echo "❌ Error: wsgi.py not found. Make sure you're in the Fastag directory."
    exit 1
fi

echo "📊 Checking application logs..."
echo ""

# Check systemd service logs
echo "=== Systemd Service Logs ==="
echo "sudo journalctl -u fastag -n 20 --no-pager"
sudo journalctl -u fastag -n 20 --no-pager
echo ""

# Check application logs
echo "=== Application Logs ==="
if [ -f "logs/fastag.log" ]; then
    echo "tail -n 20 logs/fastag.log"
    tail -n 20 logs/fastag.log
else
    echo "❌ Application log file not found: logs/fastag.log"
fi
echo ""

# Check Nginx logs
echo "=== Nginx Access Logs ==="
if [ -f "/var/log/nginx/fastag_access.log" ]; then
    echo "tail -n 10 /var/log/nginx/fastag_access.log"
    sudo tail -n 10 /var/log/nginx/fastag_access.log
else
    echo "❌ Nginx access log not found"
fi
echo ""

echo "=== Nginx Error Logs ==="
if [ -f "/var/log/nginx/fastag_error.log" ]; then
    echo "tail -n 10 /var/log/nginx/fastag_error.log"
    sudo tail -n 10 /var/log/nginx/fastag_error.log
else
    echo "❌ Nginx error log not found"
fi
echo ""

# Check service status
echo "=== Service Status ==="
echo "sudo systemctl status fastag"
sudo systemctl status fastag --no-pager
echo ""

echo "sudo systemctl status nginx"
sudo systemctl status nginx --no-pager
echo ""

# Check if application is listening
echo "=== Port Check ==="
echo "sudo netstat -tlnp | grep :8000"
sudo netstat -tlnp | grep :8000 || echo "❌ Nothing listening on port 8000"
echo ""

echo "sudo netstat -tlnp | grep :80"
sudo netstat -tlnp | grep :80 || echo "❌ Nothing listening on port 80"
echo ""

# Test local application
echo "=== Local Application Test ==="
echo "curl -I http://localhost:8000"
curl -I http://localhost:8000 2>/dev/null || echo "❌ Cannot connect to localhost:8000"
echo ""

echo "✅ Log check completed!"
echo ""
echo "💡 If you see errors above, they will help identify the issue."
echo "Common issues:"
echo "  - Database connection problems"
echo "  - Template rendering errors"
echo "  - Static file issues"
echo "  - Permission problems" 