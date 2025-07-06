#!/bin/bash

# Quick diagnostic script for Internal Server Error
# Run this on your EC2 instance to check current status

echo "🔍 Quick Diagnostic for Internal Server Error"
echo "=============================================="

echo "📊 Service Status:"
sudo systemctl status fastag --no-pager || echo "Service not found"

echo ""
echo "📝 Recent Application Logs:"
sudo journalctl -u fastag --no-pager -n 10 || echo "No logs found"

echo ""
echo "🌐 Nginx Status:"
sudo systemctl status nginx --no-pager || echo "Nginx not found"

echo ""
echo "📝 Recent Nginx Error Logs:"
sudo tail -n 10 /var/log/nginx/fastag_error.log 2>/dev/null || echo "No error logs found"

echo ""
echo "🧪 Testing Local Access:"
curl -s -I http://localhost:8000 2>/dev/null | head -1 || echo "Local access failed"

echo ""
echo "🧪 Testing Nginx Proxy:"
curl -s -I http://localhost 2>/dev/null | head -1 || echo "Nginx proxy failed"

echo ""
echo "📁 File Permissions:"
ls -la /home/ubuntu/Fastag/instance/ 2>/dev/null || echo "Instance directory not found"
ls -la /home/ubuntu/Fastag/fastag/static/ 2>/dev/null || echo "Static directory not found"

echo ""
echo "🐍 Python Environment:"
ls -la /home/ubuntu/Fastag/venv/bin/python* 2>/dev/null || echo "Python environment not found" 