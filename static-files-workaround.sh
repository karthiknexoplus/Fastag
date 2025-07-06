#!/bin/bash

# Static files workaround - move files to /var/www/static
# This is a guaranteed solution for Nginx static file serving

set -e

echo "🔧 Static Files Workaround Solution"
echo "==================================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

FASTAG_DIR="/home/ubuntu/Fastag"
STATIC_DIR="$FASTAG_DIR/fastag/static"
NGINX_STATIC_DIR="/var/www/fastag_static"
NGINX_CONFIG="/etc/nginx/sites-available/fastag"

echo "📁 Creating Nginx-accessible static directory..."
mkdir -p "$NGINX_STATIC_DIR"

echo "📋 Copying static files..."
cp -r "$STATIC_DIR"/* "$NGINX_STATIC_DIR/"

echo "🔐 Setting proper permissions..."
chown -R www-data:www-data "$NGINX_STATIC_DIR"
chmod -R 755 "$NGINX_STATIC_DIR"
chmod 644 "$NGINX_STATIC_DIR"/*

echo "📋 Files in new location:"
ls -la "$NGINX_STATIC_DIR"

echo ""
echo "📝 Updating Nginx configuration..."
# Backup current config
cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"

# Create new config with updated static path
cat > "$NGINX_CONFIG" << 'EOF'
server {
    listen 80;
    server_name fastag.onebee.in;  # Update with your domain
    
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

echo "🧪 Testing Nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    echo "Restoring backup..."
    cp "$NGINX_CONFIG.backup."* "$NGINX_CONFIG"
    nginx -t
    exit 1
fi

echo "🔄 Restarting Nginx..."
systemctl restart nginx

echo ""
echo "🧪 Testing static file access..."
sleep 2

if curl -s -I http://localhost/static/logo.png | grep -q "200 OK"; then
    echo "✅ Static files now accessible via Nginx!"
else
    echo "❌ Static files still not accessible"
    echo "📝 Nginx error logs:"
    tail -n 5 /var/log/nginx/fastag_error.log 2>/dev/null || echo "No error logs found"
fi

echo ""
echo "🎯 Test your website:"
echo "https://fastag.onebee.in"
echo ""
echo "📝 If you need to update static files in the future:"
echo "sudo cp /home/ubuntu/Fastag/fastag/static/* /var/www/fastag_static/"
echo "sudo chown -R www-data:www-data /var/www/fastag_static/"
echo "sudo systemctl reload nginx" 