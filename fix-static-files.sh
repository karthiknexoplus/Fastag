#!/bin/bash

# Fastag Static Files Fix Script
# This script fixes common issues with static files not loading (403 errors)

set -e

echo "🔧 Fixing Fastag Static Files Issues..."
echo "========================================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

# Define paths
FASTAG_DIR="/home/ubuntu/Fastag"
STATIC_DIR="$FASTAG_DIR/fastag/static"
NGINX_USER="www-data"

echo "📁 Checking Fastag installation..."
if [ ! -d "$FASTAG_DIR" ]; then
    echo "❌ Fastag directory not found at $FASTAG_DIR"
    exit 1
fi

echo "📁 Checking static files directory..."
if [ ! -d "$STATIC_DIR" ]; then
    echo "❌ Static files directory not found at $STATIC_DIR"
    exit 1
fi

# List current static files
echo "📋 Current static files:"
ls -la "$STATIC_DIR"

echo ""
echo "🔐 Fixing file permissions..."

# Set correct ownership
echo "👤 Setting ownership to ubuntu:www-data..."
chown -R ubuntu:www-data "$STATIC_DIR"

# Set correct permissions for directories
echo "📁 Setting directory permissions..."
find "$STATIC_DIR" -type d -exec chmod 755 {} \;

# Set correct permissions for files
echo "📄 Setting file permissions..."
find "$STATIC_DIR" -type f -exec chmod 644 {} \;

# Ensure nginx user can read the files
echo "🔓 Ensuring nginx can read files..."
chmod -R 755 "$STATIC_DIR"
chmod 644 "$STATIC_DIR"/*

# Set proper ownership for nginx access
echo "👥 Setting nginx-compatible ownership..."
chown -R ubuntu:www-data "$STATIC_DIR"
chmod g+rx "$STATIC_DIR"
chmod g+r "$STATIC_DIR"/*

echo ""
echo "📋 Updated file permissions:"
ls -la "$STATIC_DIR"

echo ""
echo "🔧 Checking Nginx configuration..."

# Check if nginx config exists
if [ ! -f "/etc/nginx/sites-available/fastag" ]; then
    echo "❌ Nginx configuration not found"
    exit 1
fi

# Test nginx configuration
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

# Test if files are accessible
if curl -I http://localhost/static/logo.png 2>/dev/null | grep -q "200 OK"; then
    echo "✅ logo.png is accessible"
else
    echo "❌ logo.png is not accessible"
fi

if curl -I http://localhost/static/branding.jpg 2>/dev/null | grep -q "200 OK"; then
    echo "✅ branding.jpg is accessible"
else
    echo "❌ branding.jpg is not accessible"
fi

if curl -I http://localhost/static/favicon.ico 2>/dev/null | grep -q "200 OK"; then
    echo "✅ favicon.ico is accessible"
else
    echo "❌ favicon.ico is not accessible"
fi

echo ""
echo "🔍 Additional troubleshooting steps:"

# Check nginx error logs
echo "📝 Recent Nginx error logs:"
tail -n 10 /var/log/nginx/fastag_error.log 2>/dev/null || echo "No error logs found"

# Check nginx access logs
echo ""
echo "📝 Recent Nginx access logs:"
tail -n 5 /var/log/nginx/fastag_access.log 2>/dev/null || echo "No access logs found"

echo ""
echo "🎯 Manual testing commands:"
echo "curl -I http://your-domain/static/logo.png"
echo "curl -I http://your-domain/static/branding.jpg"
echo "curl -I http://your-domain/static/favicon.ico"

echo ""
echo "✅ Static files fix completed!"
echo "If files still don't load, check:"
echo "1. Domain name in nginx config matches your actual domain/IP"
echo "2. Firewall allows HTTP traffic (port 80)"
echo "3. Nginx service is running: systemctl status nginx" 