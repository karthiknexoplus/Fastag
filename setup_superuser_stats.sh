#!/bin/bash

# Setup script for Super User Statistics Push Notifications
echo "🚀 Setting up Super User Statistics Push Notifications..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Copy service files
echo "📁 Copying service files..."
cp superuser-stats.service /etc/systemd/system/
cp superuser-stats.timer /etc/systemd/system/

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable and start the timer
echo "✅ Enabling and starting timer..."
systemctl enable superuser-stats.timer
systemctl start superuser-stats.timer

# Check status
echo "📊 Checking service status..."
systemctl status superuser-stats.timer --no-pager

echo "✅ Setup completed!"
echo "📅 Timer will run every hour"
echo "📋 To check status: systemctl status superuser-stats.timer"
echo "📋 To view logs: journalctl -u superuser-stats.service"
echo "📋 To test manually: sudo systemctl start superuser-stats.service" 