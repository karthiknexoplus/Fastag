#!/bin/bash

# Fix logging permissions for Fastag application
echo "Fixing logging permissions for Fastag..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory with proper permissions
echo "Creating logs directory..."
mkdir -p logs
chmod 755 logs

# Create log files with proper permissions
echo "Setting up log files..."
touch logs/fastag.log
touch logs/rfid.log
touch logs/rfid_reader1.log
touch logs/rfid_reader2.log
touch logs/rfid_readers.log

# Set proper permissions for log files
chmod 664 logs/*.log

# Set ownership to ubuntu user (adjust if using different user)
echo "Setting ownership..."
sudo chown -R ubuntu:ubuntu logs/ 2>/dev/null || echo "Could not change ownership (may not be needed)"

# Fix instance directory permissions
echo "Fixing instance directory..."
mkdir -p instance
chmod 755 instance
sudo chown -R ubuntu:ubuntu instance/ 2>/dev/null || echo "Could not change instance ownership"

# Restart the services
echo "Restarting Fastag services..."
sudo systemctl restart fastag.service
sudo systemctl restart rfid_readers.service

echo "Logging permissions fixed!"
echo "Check service status with:"
echo "  sudo systemctl status fastag.service"
echo "  sudo systemctl status rfid_readers.service" 