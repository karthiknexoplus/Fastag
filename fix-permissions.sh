#!/bin/bash

echo "🔧 Fixing static file permissions for nginx..."

# Fix ownership and permissions for static files
echo "📁 Setting proper ownership and permissions..."
sudo chown -R www-data:www-data /home/ubuntu/Fastag/fastag/static/
sudo chmod -R 755 /home/ubuntu/Fastag/fastag/static/
sudo chmod 644 /home/ubuntu/Fastag/fastag/static/*

# Also ensure the parent directories are accessible
sudo chown ubuntu:ubuntu /home/ubuntu/Fastag/
sudo chmod 755 /home/ubuntu/Fastag/
sudo chown ubuntu:ubuntu /home/ubuntu/Fastag/fastag/
sudo chmod 755 /home/ubuntu/Fastag/fastag/

# Test nginx user access
echo "🧪 Testing nginx user access..."
if sudo -u www-data ls -la /home/ubuntu/Fastag/fastag/static/ > /dev/null 2>&1; then
    echo "✅ nginx user can access static directory"
else
    echo "❌ nginx user still cannot access static directory"
fi

# Test specific files
echo "🧪 Testing specific file access..."
if sudo -u www-data test -r /home/ubuntu/Fastag/fastag/static/logo.png; then
    echo "✅ nginx user can read logo.png"
else
    echo "❌ nginx user cannot read logo.png"
fi

if sudo -u www-data test -r /home/ubuntu/Fastag/fastag/static/branding.jpg; then
    echo "✅ nginx user can read branding.jpg"
else
    echo "❌ nginx user cannot read branding.jpg"
fi

# Reload nginx
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

# Test static files
echo "🧪 Testing static file accessibility..."
sleep 2

if curl -s -I "https://fastag.onebee.in/static/logo.png" | grep -q "200 OK"; then
    echo "✅ Logo is now accessible"
else
    echo "❌ Logo still not accessible"
fi

if curl -s -I "https://fastag.onebee.in/static/branding.jpg" | grep -q "200 OK"; then
    echo "✅ Branding image is now accessible"
else
    echo "❌ Branding image still not accessible"
fi

echo ""
echo "🌐 Test your site: https://fastag.onebee.in"
echo "The images and logos should now load properly!" 