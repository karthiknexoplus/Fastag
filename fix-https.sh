#!/bin/bash

# Fix HTTPS/SSL issues for Fastag
# This script sets up SSL certificates and HTTPS

set -e

echo "🔒 Fixing HTTPS/SSL Issues"
echo "=========================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

DOMAIN="fastag.onebee.in"
NGINX_CONFIG="/etc/nginx/sites-available/fastag"

echo "🌐 Domain: $DOMAIN"

echo ""
echo "🔍 Step 1: Checking current SSL status"
echo "======================================"

echo "📋 Current Nginx configuration:"
if [ -f "$NGINX_CONFIG" ]; then
    grep -E "(listen|ssl_certificate)" "$NGINX_CONFIG" || echo "No SSL configuration found"
else
    echo "❌ Nginx configuration not found"
    exit 1
fi

echo ""
echo "🔍 Step 2: Checking SSL certificates"
echo "===================================="

if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "✅ SSL certificates found for $DOMAIN"
    echo "📅 Certificate expiry:"
    openssl x509 -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" -text -noout | grep "Not After" || echo "Could not check expiry"
else
    echo "❌ SSL certificates not found for $DOMAIN"
fi

echo ""
echo "🔍 Step 3: Checking firewall"
echo "============================"

echo "🔥 Firewall status:"
ufw status | grep -E "(80|443)" || echo "No firewall rules found for ports 80/443"

echo ""
echo "🎯 Choose an option:"
echo "1. Set up Let's Encrypt SSL certificate (recommended)"
echo "2. Configure HTTP only (no HTTPS)"
echo "3. Check current configuration and exit"

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🔒 Setting up Let's Encrypt SSL certificate..."
        
        # Install certbot if not installed
        if ! command -v certbot >/dev/null 2>&1; then
            echo "📦 Installing certbot..."
            apt update
            apt install -y certbot python3-certbot-nginx
        fi
        
        # Ensure HTTP is working first
        echo "🧪 Testing HTTP access..."
        if curl -s -I "http://$DOMAIN" | head -1; then
            echo "✅ HTTP is accessible"
        else
            echo "❌ HTTP is not accessible. Please ensure your domain points to this server."
            exit 1
        fi
        
        # Get SSL certificate
        echo "🔐 Obtaining SSL certificate..."
        certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN
        
        # Test SSL certificate
        echo "🧪 Testing SSL certificate..."
        if curl -s -I "https://$DOMAIN" | head -1; then
            echo "✅ HTTPS is now working!"
        else
            echo "❌ HTTPS still not working"
        fi
        
        ;;
        
    2)
        echo ""
        echo "🌐 Configuring HTTP only..."
        
        # Backup current config
        cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Create HTTP-only config
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
        
        # Test and restart
        if nginx -t; then
            echo "✅ Nginx configuration is valid"
            systemctl restart nginx
            echo "✅ HTTP-only configuration applied"
        else
            echo "❌ Nginx configuration has errors"
            exit 1
        fi
        
        ;;
        
    3)
        echo ""
        echo "📋 Current configuration summary:"
        echo "================================="
        
        echo "🌐 Domain: $DOMAIN"
        echo "📁 Nginx config: $NGINX_CONFIG"
        
        if [ -f "$NGINX_CONFIG" ]; then
            echo "📋 Listening ports:"
            grep "listen" "$NGINX_CONFIG" || echo "No listen directives found"
            
            echo ""
            echo "📋 SSL configuration:"
            grep -E "(ssl_certificate|ssl_certificate_key)" "$NGINX_CONFIG" || echo "No SSL configuration found"
        fi
        
        echo ""
        echo "🔥 Firewall status:"
        ufw status | grep -E "(80|443)" || echo "No firewall rules found for ports 80/443"
        
        echo ""
        echo "🧪 Connection tests:"
        echo "HTTP: $(curl -s -I "http://$DOMAIN" | head -1 2>/dev/null || echo 'Failed')"
        echo "HTTPS: $(curl -s -I "https://$DOMAIN" | head -1 2>/dev/null || echo 'Failed')"
        
        exit 0
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎯 Testing final configuration..."
sleep 2

echo "🧪 HTTP test:"
curl -s -I "http://$DOMAIN" | head -1 || echo "HTTP failed"

echo ""
echo "🧪 HTTPS test:"
curl -s -I "https://$DOMAIN" | head -1 || echo "HTTPS failed"

echo ""
echo "🎯 Your website should now be accessible at:"
echo "   http://$DOMAIN"
if [ $choice -eq 1 ]; then
    echo "   https://$DOMAIN"
fi

echo ""
echo "📝 If HTTPS still doesn't work:"
echo "1. Check domain DNS: nslookup $DOMAIN"
echo "2. Check firewall: ufw status"
echo "3. Check SSL certificates: ls -la /etc/letsencrypt/live/$DOMAIN/" 