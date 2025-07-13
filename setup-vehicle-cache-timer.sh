#!/bin/bash

# Setup script for vehicle cache population timer
echo "Setting up vehicle cache population timer..."

# Copy service and timer files to systemd directory
sudo cp populate-vehicle-cache.service /etc/systemd/system/
sudo cp populate-vehicle-cache.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the timer
sudo systemctl enable populate-vehicle-cache.timer
sudo systemctl start populate-vehicle-cache.timer

echo "✓ Vehicle cache timer setup complete!"
echo ""
echo "To check status:"
echo "  sudo systemctl status populate-vehicle-cache.timer"
echo "  sudo systemctl status populate-vehicle-cache.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u populate-vehicle-cache.service -f"
echo ""
echo "To manually run once:"
echo "  sudo systemctl start populate-vehicle-cache.service"
echo ""
echo "To stop the timer:"
echo "  sudo systemctl stop populate-vehicle-cache.timer"
echo "  sudo systemctl disable populate-vehicle-cache.timer" 