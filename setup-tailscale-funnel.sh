#!/bin/bash

# Tailscale Funnel Setup Script
# This script installs and configures Tailscale Funnel for automatic startup

set -e

echo "🚀 Setting up Tailscale Funnel for automatic startup..."
echo "======================================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root or with sudo"
    exit 1
fi

# Check if Tailscale is installed
if ! command -v tailscale >/dev/null 2>&1; then
    echo "❌ Tailscale is not installed. Please install Tailscale first:"
    echo "   curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null"
    echo "   curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list"
    echo "   sudo apt-get update && sudo apt-get install tailscale"
    exit 1
fi

echo "✅ Tailscale is installed"

# Check if Tailscale is authenticated
if ! tailscale status >/dev/null 2>&1; then
    echo "❌ Tailscale is not authenticated. Please run:"
    echo "   sudo tailscale up"
    echo "   Then authenticate via the provided URL"
    exit 1
fi

echo "✅ Tailscale is authenticated"

# Check if the target service is running
if ! netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo "⚠️  Warning: Port 8000 is not listening. Make sure your Fastag service is running."
    echo "   You can start it with: sudo systemctl start fastag"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Target service is running on port 8000"
fi

# Copy the service file
echo "📋 Installing systemd service..."
cp tailscale-funnel.service /etc/systemd/system/
chmod 644 /etc/systemd/system/tailscale-funnel.service

# Make the script executable
chmod +x tailscale-funnel.sh

# Create logs directory
mkdir -p /home/ubuntu/Fastag/logs
chown ubuntu:ubuntu /home/ubuntu/Fastag/logs

# Reload systemd and enable the service
echo "⚙️  Enabling systemd service..."
systemctl daemon-reload
systemctl enable tailscale-funnel

# Start the service
echo "🚀 Starting Tailscale Funnel service..."
systemctl start tailscale-funnel

# Wait a moment for the service to start
sleep 5

# Check service status
echo "📊 Checking service status..."
if systemctl is-active --quiet tailscale-funnel; then
    echo "✅ Tailscale Funnel service is running"
else
    echo "❌ Tailscale Funnel service failed to start"
    echo "Checking logs:"
    journalctl -u tailscale-funnel -n 10 --no-pager
    exit 1
fi

# Test the funnel
echo "🧪 Testing Tailscale Funnel..."
sleep 10  # Give it time to establish the funnel

if tailscale funnel --list 2>/dev/null | grep -q "8000"; then
    echo "✅ Funnel is active and working"
    echo "🌐 Funnel URL: https://pgshospital.tail1b76dc.ts.net/"
else
    echo "⚠️  Funnel might not be active yet. Check logs:"
    echo "   sudo journalctl -u tailscale-funnel -f"
fi

echo ""
echo "🎉 Tailscale Funnel setup complete!"
echo "=================================="
echo ""
echo "📋 Service Information:"
echo "   Service Name: tailscale-funnel"
echo "   Status: sudo systemctl status tailscale-funnel"
echo "   Logs: sudo journalctl -u tailscale-funnel -f"
echo "   Manual Control: sudo ./tailscale-funnel.sh {start|stop|status}"
echo ""
echo "🌐 Funnel URL: https://pgshospital.tail1b76dc.ts.net/"
echo ""
echo "🔄 The service will automatically:"
echo "   - Start on system boot"
echo "   - Restart if the funnel dies"
echo "   - Wait for network connectivity"
echo "   - Wait for the target service to be available"
echo ""
echo "📝 Useful commands:"
echo "   sudo systemctl restart tailscale-funnel  # Restart service"
echo "   sudo systemctl stop tailscale-funnel     # Stop service"
echo "   sudo systemctl enable tailscale-funnel   # Enable auto-start"
echo "   sudo systemctl disable tailscale-funnel  # Disable auto-start" 