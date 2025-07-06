#!/bin/bash

# Restore original Nginx configuration
# Run this if Option 2 broke the website

set -e

echo "🔄 Restoring Original Nginx Configuration"
echo "========================================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

NGINX_CONFIG="/etc/nginx/sites-available/fastag"
BACKUP_FILES=()

echo "📁 Looking for backup files..."
for backup in "$NGINX_CONFIG".backup.*; do
    if [ -f "$backup" ]; then
        BACKUP_FILES+=("$backup")
        echo "Found backup: $backup"
    fi
done

if [ ${#BACKUP_FILES[@]} -eq 0 ]; then
    echo "❌ No backup files found"
    echo "Creating a new configuration with static file handling..."
    
    # Create a working configuration
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
    
    # Static files - serve directly from nginx for better performance
    location /static/ {
        alias /home/ubuntu/Fastag/fastag/static/;
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
else
    # Use the most recent backup
    LATEST_BACKUP="${BACKUP_FILES[-1]}"
    echo "🔄 Restoring from: $LATEST_BACKUP"
    cp "$LATEST_BACKUP" "$NGINX_CONFIG"
fi

echo "🧪 Testing Nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

echo "🔄 Restarting Nginx..."
systemctl restart nginx

echo "🧪 Testing website..."
sleep 2
if curl -s -I http://localhost | head -1; then
    echo "✅ Website is now accessible"
else
    echo "❌ Website still not accessible"
fi

echo ""
echo "🎯 Next steps:"
echo "1. Test your website: https://fastag.onebee.in"
echo "2. If static files still don't work, run the permission fix:"
echo "   sudo chown -R ubuntu:www-data /home/ubuntu/Fastag/fastag/static/"
echo "   sudo chmod -R 755 /home/ubuntu/Fastag/fastag/static/"
echo "   sudo chmod 644 /home/ubuntu/Fastag/fastag/static/*"
echo "   sudo systemctl restart nginx" 