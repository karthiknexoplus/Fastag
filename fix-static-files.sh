#!/bin/bash

echo "🔧 Quick fix for static files not loading..."

# Backup current config
sudo cp /etc/nginx/sites-available/fastag /etc/nginx/sites-available/fastag.backup.$(date +%Y%m%d_%H%M%S)

# Create a clean nginx config without conflicts
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

# Test nginx config
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    
    # Reload nginx
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
    
    # Test static files
    echo "🧪 Testing static files..."
    sleep 2
    
    # Test logo
    if curl -s -I "https://fastag.onebee.in/static/logo.png" | grep -q "200 OK"; then
        echo "✅ Logo is accessible"
    else
        echo "❌ Logo not accessible"
    fi
    
    # Test branding image
    if curl -s -I "https://fastag.onebee.in/static/branding.jpg" | grep -q "200 OK"; then
        echo "✅ Branding image is accessible"
    else
        echo "❌ Branding image not accessible"
    fi
    
    echo ""
    echo "🌐 Test your site: https://fastag.onebee.in"
    echo "📊 Test API: https://fastag.onebee.in/api/device/00:00:00:00"
    echo ""
    echo "If images still don't load, check:"
    echo "1. Browser cache (Ctrl+F5 or Cmd+Shift+R)"
    echo "2. Check browser developer tools (F12) for errors"
    echo "3. Check nginx error logs: sudo tail -f /var/log/nginx/fastag_error.log"
    
else
    echo "❌ Nginx configuration error"
    echo "Restoring backup..."
    sudo cp /etc/nginx/sites-available/fastag.backup.* /etc/nginx/sites-available/fastag
    sudo systemctl reload nginx
fi 