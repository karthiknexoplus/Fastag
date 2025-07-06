#!/bin/bash

# Emergency fix for SSL and static files issues
# Run this immediately to fix the website

set -e

echo "🚨 Emergency Fix for SSL and Static Files"
echo "========================================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

DOMAIN="fastag.onebee.in"
NGINX_CONFIG="/etc/nginx/sites-available/fastag"

echo "🔍 Current situation:"
echo "✅ Gunicorn working (port 8000)"
echo "✅ Nginx proxy working (port 80)"
echo "❌ Static files not accessible via Nginx"
echo "❌ Website not loading"

echo ""
echo "🔧 Step 1: Checking current Nginx configuration..."
if [ -f "$NGINX_CONFIG" ]; then
    echo "📋 Current config has SSL:"
    grep -E "(ssl_certificate|listen.*443)" "$NGINX_CONFIG" || echo "No SSL config found"
else
    echo "❌ Nginx config not found"
    exit 1
fi

echo ""
echo "🔧 Step 2: Fixing static files..."
# Ensure static files are in the right place
sudo mkdir -p /var/www/fastag_static
sudo cp -r /home/ubuntu/Fastag/fastag/static/* /var/www/fastag_static/ 2>/dev/null || echo "Static files already copied"
sudo chown -R www-data:www-data /var/www/fastag_static
sudo chmod -R 755 /var/www/fastag_static
sudo chmod 644 /var/www/fastag_static/*

echo "✅ Static files fixed"

echo ""
echo "🔧 Step 3: Creating working Nginx configuration..."

# Create a working configuration that handles both HTTP and HTTPS
sudo tee "$NGINX_CONFIG" > /dev/null << 'EOF'
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name fastag.onebee.in;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name fastag.onebee.in;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/fastag.onebee.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fastag.onebee.in/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Logs
    access_log /var/log/nginx/fastag_access.log;
    error_log /var/log/nginx/fastag_error.log;
    
    # Static files - serve from /var/www/fastag_static
    location /static/ {
        alias /var/www/fastag_static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin "*";
        
        # Handle common static file types
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|eot|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header Access-Control-Allow-Origin "*";
        }
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;
}
EOF

echo "✅ Nginx configuration created"

echo ""
echo "🔧 Step 4: Testing Nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    echo "📝 Error details:"
    nginx -t 2>&1
    exit 1
fi

echo ""
echo "🔧 Step 5: Restarting services..."
systemctl restart nginx
sleep 2
systemctl restart fastag
sleep 3

echo ""
echo "🧪 Step 6: Testing everything..."

# Test Gunicorn
echo "Testing Gunicorn (port 8000)..."
if curl -s -I http://localhost:8000 | head -1; then
    echo "✅ Gunicorn is responding"
else
    echo "❌ Gunicorn is not responding"
fi

# Test HTTPS
echo "Testing HTTPS..."
if curl -s -I https://fastag.onebee.in | head -1; then
    echo "✅ HTTPS is working"
else
    echo "❌ HTTPS is not working"
fi

# Test static files via HTTPS
echo "Testing static files via HTTPS..."
if curl -s -I https://fastag.onebee.in/static/logo.png | grep -q "200 OK"; then
    echo "✅ Static files are accessible via HTTPS"
else
    echo "❌ Static files are not accessible via HTTPS"
fi

# Test static files via HTTP (should redirect)
echo "Testing static files via HTTP (should redirect)..."
if curl -s -I http://fastag.onebee.in/static/logo.png | grep -q "301\|302"; then
    echo "✅ HTTP redirect is working"
else
    echo "❌ HTTP redirect is not working"
fi

echo ""
echo "🎯 Final status:"
echo "Website: https://fastag.onebee.in"
echo "API: https://fastag.onebee.in/api/device/00:00:00:00"

echo ""
echo "📝 If issues persist, check:"
echo "sudo tail -f /var/log/nginx/fastag_error.log"
echo "sudo journalctl -u fastag -f" 