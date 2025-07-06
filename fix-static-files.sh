#!/bin/bash

# Fix Static Files After SSL Setup
# This script fixes the static files issue that occurs after SSL certificate setup

set -e

echo "🔧 Fixing Static Files After SSL Setup"
echo "======================================"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

echo "🔍 Step 1: Checking current Nginx configuration..."
echo "Current Nginx config:"
sudo cat /etc/nginx/sites-available/fastag

echo ""
echo "🔍 Step 2: Checking static files directory..."
ls -la /var/www/fastag_static/

echo ""
echo "🔍 Step 3: Testing static files access..."
echo "Testing via HTTP:"
curl -I "http://fastag.onebee.in/static/logo.png" 2>/dev/null | head -1 || echo "HTTP static files not accessible"

echo "Testing via HTTPS:"
curl -I "https://fastag.onebee.in/static/logo.png" 2>/dev/null | head -1 || echo "HTTPS static files not accessible"

echo ""
echo "🔧 Step 4: Creating correct Nginx configuration with SSL and static files..."

# Create a proper Nginx config that includes both SSL and static files
sudo tee /etc/nginx/sites-available/fastag > /dev/null << 'EOF'
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
    
    # Static files - serve from /var/www/fastag_static (guaranteed access)
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

echo "✅ Nginx configuration updated"

echo ""
echo "🔧 Step 5: Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    sudo nginx -t
    exit 1
fi

echo ""
echo "🔄 Step 6: Reloading Nginx..."
sudo systemctl reload nginx

echo ""
echo "🧪 Step 7: Testing static files after fix..."
sleep 3

echo "Testing static files via HTTPS:"
if curl -s -I "https://fastag.onebee.in/static/logo.png" | grep -q "200 OK"; then
    echo "✅ Static files are now accessible via HTTPS"
else
    echo "❌ Static files are still not accessible via HTTPS"
    echo "Checking Nginx error logs..."
    sudo tail -n 10 /var/log/nginx/fastag_error.log
fi

echo ""
echo "🎯 Static files fix completed!"
echo "Your website should now be fully functional with static files working." 