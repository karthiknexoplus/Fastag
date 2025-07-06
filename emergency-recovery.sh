#!/bin/bash

# Emergency Recovery Script for Fastag
# Run this if the website stops working after deployment

set -e

echo "🚨 Emergency Recovery for Fastag"
echo "================================"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

echo "🔍 Step 1: Checking current status..."
echo "Gunicorn status:"
sudo systemctl status fastag --no-pager || echo "Gunicorn not running"

echo ""
echo "Nginx status:"
sudo systemctl status nginx --no-pager || echo "Nginx not running"

echo ""
echo "🔧 Step 2: Restarting services..."
sudo systemctl restart fastag
sleep 3
sudo systemctl restart nginx
sleep 3

echo ""
echo "🧪 Step 3: Testing services..."

# Test Gunicorn
echo "Testing Gunicorn..."
if curl -s -I "http://localhost:8000" | grep -q "200 OK\|302 Found"; then
    echo "✅ Gunicorn is working"
else
    echo "❌ Gunicorn is not working"
    echo "Checking Gunicorn logs..."
    sudo journalctl -u fastag --no-pager -n 20
fi

# Test Nginx
echo "Testing Nginx..."
if curl -s -I "http://localhost" | grep -q "200 OK\|302 Found"; then
    echo "✅ Nginx is working"
else
    echo "❌ Nginx is not working"
    echo "Checking Nginx configuration..."
    sudo nginx -t
    echo "Checking Nginx logs..."
    sudo tail -n 20 /var/log/nginx/fastag_error.log
fi

# Test static files
echo "Testing static files..."
if curl -s -I "http://localhost/static/logo.png" | grep -q "200 OK"; then
    echo "✅ Static files are working"
else
    echo "❌ Static files are not working"
    echo "Fixing static files..."
    sudo mkdir -p /var/www/fastag_static
    sudo cp -r /home/ubuntu/Fastag/fastag/static/* /var/www/fastag_static/ 2>/dev/null || echo "Static files already copied"
    sudo chown -R www-data:www-data /var/www/fastag_static
    sudo chmod -R 755 /var/www/fastag_static
    sudo chmod 644 /var/www/fastag_static/*
fi

echo ""
echo "🔧 Step 4: Creating simple working Nginx config..."

# Create a simple, working Nginx config
sudo tee /etc/nginx/sites-available/fastag > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Logs
    access_log /var/log/nginx/fastag_access.log;
    error_log /var/log/nginx/fastag_error.log;
    
    # Static files
    location /static/ {
        alias /var/www/fastag_static/;
        expires 30d;
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Test and reload Nginx
echo "Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx configuration has errors"
    sudo nginx -t
fi

echo ""
echo "🧪 Step 5: Final testing..."
sleep 3

# Final tests
echo "Testing website access..."
if curl -s -I "http://localhost" | head -1; then
    echo "✅ Website is accessible"
else
    echo "❌ Website is not accessible"
fi

echo "Testing static files..."
if curl -s -I "http://localhost/static/logo.png" | grep -q "200 OK"; then
    echo "✅ Static files are accessible"
else
    echo "❌ Static files are not accessible"
fi

echo ""
echo "🎯 Emergency recovery completed!"
echo "If issues persist, check the logs:"
echo "  sudo journalctl -u fastag -f"
echo "  sudo tail -f /var/log/nginx/fastag_error.log" 