#!/bin/bash

echo "🔄 Restarting Fastag service on EC2..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script with sudo"
    echo "Usage: sudo ./restart_ec2_service.sh"
    exit 1
fi

echo "📋 Current service status:"
systemctl status fastag --no-pager -l

echo ""
echo "🛑 Stopping Fastag service..."
systemctl stop fastag

echo "⏳ Waiting 3 seconds..."
sleep 3

echo "▶️  Starting Fastag service..."
systemctl start fastag

echo "⏳ Waiting 5 seconds for service to fully start..."
sleep 5

echo "📋 New service status:"
systemctl status fastag --no-pager -l

echo ""
echo "🔍 Checking if pricing route is available..."
curl -s -o /dev/null -w "Pricing route status: %{http_code}\n" http://localhost/pricing

echo ""
echo "✅ Service restart completed!"
echo "🌐 You can now access the pricing page at: http://your-ec2-ip/pricing" 