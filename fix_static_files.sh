#!/bin/bash

echo "🔧 Quick Fix for Static Files"
echo "============================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

echo ""
echo "🔧 Step 1: Ensuring static files are properly copied..."
sudo mkdir -p /var/www/fastag_static
sudo cp -r /home/ubuntu/Fastag/fastag/static/* /var/www/fastag_static/ 2>/dev/null || echo "Static files already copied"

echo ""
echo "🔧 Step 2: Fixing permissions..."
sudo chown -R www-data:www-data /var/www/fastag_static
sudo chmod -R 755 /var/www/fastag_static
sudo find /var/www/fastag_static -type f -exec chmod 644 {} \;

echo ""
echo "🔧 Step 3: Creating improved Nginx configuration..."

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
    
    # Static files - improved configuration
    location /static/ {
        alias /var/www/fastag_static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin "*";
        
        # Ensure files are served with correct MIME types
        location ~* \.(css)$ {
            add_header Content-Type "text/css";
            expires 1y;
        }
        
        location ~* \.(js)$ {
            add_header Content-Type "application/javascript";
            expires 1y;
        }
        
        location ~* \.(png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
        }
        
        # Handle missing files
        try_files $uri =404;
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

echo ""
echo "🔧 Step 4: Testing Nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    nginx -t 2>&1
    exit 1
fi

echo ""
echo "🔧 Step 5: Restarting Nginx..."
sudo systemctl restart nginx
sleep 3

echo ""
echo "🔧 Step 6: Testing static files..."
echo "Testing localhost:"
curl -I http://localhost/static/logo.png 2>/dev/null | head -1 || echo "Failed via localhost"

echo "Testing HTTPS:"
curl -I https://fastag.onebee.in/static/logo.png 2>/dev/null | head -1 || echo "Failed via HTTPS"

echo ""
echo "🎯 Fix completed!"
echo "If static files are still not accessible, run:"
echo "sudo ./diagnose_static_files.sh" 