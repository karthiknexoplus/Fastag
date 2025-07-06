#!/bin/bash

# Fix Nginx syntax error in proxy_set_header directive
# Run this to fix the SSL certificate renewal issue

set -e

echo "🔧 Fixing Nginx Syntax Error"
echo "============================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

NGINX_CONFIG="/etc/nginx/sites-available/fastag"

echo "🔍 Step 1: Checking current Nginx configuration..."
echo "📋 Current configuration syntax:"
nginx -t 2>&1 || echo "Configuration has errors (expected)"

echo ""
echo "🔍 Step 2: Checking line 48 (the error location)..."
if [ -f "$NGINX_CONFIG" ]; then
    echo "📋 Line 48:"
    sed -n '48p' "$NGINX_CONFIG"
    echo ""
    echo "📋 Lines around 48:"
    sed -n '45,52p' "$NGINX_CONFIG"
else
    echo "❌ Nginx config not found"
    exit 1
fi

echo ""
echo "🔧 Step 3: Fixing the proxy_set_header directives..."

# Create a corrected configuration
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

echo "✅ Nginx configuration fixed"

echo ""
echo "🔧 Step 4: Testing Nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is now valid"
else
    echo "❌ Nginx configuration still has errors"
    nginx -t 2>&1
    exit 1
fi

echo ""
echo "🔄 Step 5: Restarting Nginx..."
systemctl restart nginx

echo ""
echo "🧪 Step 6: Testing SSL certificate renewal..."
if certbot renew --dry-run; then
    echo "✅ SSL certificate renewal test successful"
else
    echo "❌ SSL certificate renewal test failed"
    echo "📝 Check the logs for more details"
fi

echo ""
echo "🎯 Fix completed!"
echo "Your Nginx configuration is now valid and SSL renewal should work." 