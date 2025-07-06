#!/bin/bash

# Quick fix for static files 403 error
# Run this on your EC2 instance

echo "🔧 Quick fix for static files 403 error..."

# Fix permissions
sudo chown -R ubuntu:www-data /home/ubuntu/Fastag/fastag/static/
sudo chmod -R 755 /home/ubuntu/Fastag/fastag/static/
sudo chmod 644 /home/ubuntu/Fastag/fastag/static/*

# Restart nginx
sudo systemctl restart nginx

echo "✅ Quick fix applied!"
echo "Test with: curl -I http://your-domain/static/logo.png" 