#!/bin/bash

echo "🔍 Debugging static file issues..."

echo ""
echo "1. Checking static file existence and permissions:"
ls -la /home/ubuntu/Fastag/fastag/static/

echo ""
echo "2. Checking nginx error logs:"
sudo tail -10 /var/log/nginx/fastag_error.log

echo ""
echo "3. Testing static file access directly:"
curl -I http://localhost/static/logo.png
curl -I http://localhost/static/branding.jpg

echo ""
echo "4. Checking nginx configuration:"
sudo cat /etc/nginx/sites-available/fastag

echo ""
echo "5. Testing nginx static file serving:"
sudo nginx -T | grep -A 10 -B 5 "location /static/"

echo ""
echo "6. Checking if nginx can read the static directory:"
sudo -u www-data ls -la /home/ubuntu/Fastag/fastag/static/ 2>/dev/null || echo "nginx user cannot access static directory"

echo ""
echo "7. Testing with curl from server:"
curl -s -I "https://fastag.onebee.in/static/logo.png" | head -5
curl -s -I "https://fastag.onebee.in/static/branding.jpg" | head -5

echo ""
echo "8. Checking file types:"
file /home/ubuntu/Fastag/fastag/static/logo.png
file /home/ubuntu/Fastag/fastag/static/branding.jpg 