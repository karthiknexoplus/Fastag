#!/bin/bash

# Fix Nginx Static Files Serving Issues
# This script provides two options to fix static file serving

set -e

echo "🔧 Fixing Nginx Static Files Serving Issues"
echo "============================================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

FASTAG_DIR="/home/ubuntu/Fastag"
NGINX_CONFIG="/etc/nginx/sites-available/fastag"

echo "📁 Checking Fastag installation..."
if [ ! -d "$FASTAG_DIR" ]; then
    echo "❌ Fastag directory not found at $FASTAG_DIR"
    exit 1
fi

echo "✅ Fastag directory found"

echo ""
echo "🔍 Current situation:"
echo "✅ Gunicorn (port 8000) can serve static files"
echo "❌ Nginx (port 80/443) cannot serve static files"
echo ""

echo "🎯 Choose a fix option:"
echo "1. Fix permissions for Nginx direct serving (recommended for performance)"
echo "2. Let Flask/Gunicorn handle static files (simpler, less performance)"
echo "3. Show current file permissions and exit"

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🔧 Option 1: Fixing permissions for Nginx direct serving..."
        
        # Fix permissions comprehensively
        echo "👤 Setting ownership..."
        chown -R ubuntu:www-data "$FASTAG_DIR/fastag/static/"
        
        echo "📁 Setting directory permissions..."
        find "$FASTAG_DIR/fastag/static/" -type d -exec chmod 755 {} \;
        
        echo "📄 Setting file permissions..."
        find "$FASTAG_DIR/fastag/static/" -type f -exec chmod 644 {} \;
        
        # Ensure nginx user can access the directory tree
        echo "🔓 Ensuring nginx can access directory tree..."
        chmod 755 "$FASTAG_DIR"
        chmod 755 "$FASTAG_DIR/fastag"
        chmod 755 "$FASTAG_DIR/fastag/static"
        
        # Set group read permissions
        echo "👥 Setting group read permissions..."
        chmod g+rx "$FASTAG_DIR/fastag/static"
        chmod g+r "$FASTAG_DIR/fastag/static"/*
        
        echo ""
        echo "📋 Updated permissions:"
        ls -la "$FASTAG_DIR/fastag/static/"
        
        # Test nginx configuration
        echo ""
        echo "🧪 Testing Nginx configuration..."
        if nginx -t; then
            echo "✅ Nginx configuration is valid"
        else
            echo "❌ Nginx configuration has errors"
            exit 1
        fi
        
        # Restart nginx
        echo "🔄 Restarting Nginx..."
        systemctl restart nginx
        
        echo ""
        echo "🧪 Testing static file access..."
        sleep 2
        
        if curl -s -I http://localhost/static/logo.png | grep -q "200 OK"; then
            echo "✅ Static files now accessible via Nginx"
        else
            echo "❌ Static files still not accessible"
            echo "📝 Nginx error logs:"
            tail -n 5 /var/log/nginx/fastag_error.log 2>/dev/null || echo "No error logs found"
        fi
        
        ;;
        
    2)
        echo ""
        echo "🔧 Option 2: Letting Flask handle static files..."
        
        # Backup current config
        echo "💾 Backing up current Nginx configuration..."
        cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Create new config without static file handling
        echo "📝 Creating new Nginx configuration..."
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
    
    # Proxy everything to Gunicorn (including static files)
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
        
        # Test nginx configuration
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
        
        # Restart nginx
        echo "🔄 Restarting Nginx..."
        systemctl restart nginx
        
        echo ""
        echo "🧪 Testing static file access..."
        sleep 2
        
        if curl -s -I http://localhost/static/logo.png | grep -q "200 OK"; then
            echo "✅ Static files now accessible via Flask/Gunicorn"
        else
            echo "❌ Static files still not accessible"
        fi
        
        ;;
        
    3)
        echo ""
        echo "📋 Current file permissions:"
        echo "Directory tree:"
        ls -la "$FASTAG_DIR" | head -5
        echo ""
        ls -la "$FASTAG_DIR/fastag/" | head -5
        echo ""
        echo "Static files:"
        ls -la "$FASTAG_DIR/fastag/static/"
        echo ""
        echo "Nginx user:"
        id www-data
        echo ""
        echo "Current nginx config:"
        grep -A 10 "location /static/" "$NGINX_CONFIG" 2>/dev/null || echo "Static location not found in config"
        exit 0
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎯 Manual testing commands:"
echo "curl -I http://localhost/static/logo.png"
echo "curl -I https://fastag.onebee.in/static/logo.png"
echo ""
echo "📝 If issues persist, check:"
echo "sudo tail -f /var/log/nginx/fastag_error.log"
echo "sudo journalctl -u nginx -f" 