#!/bin/bash

# Setup script for vehicle cache population using crontab
echo "Setting up vehicle cache population using crontab..."

# Get the current user's crontab
crontab -l > /tmp/current_crontab 2>/dev/null || echo "" > /tmp/current_crontab

# Add the new cron job (every 5 minutes)
echo "# Vehicle cache population - runs every 5 minutes" >> /tmp/current_crontab
echo "*/5 * * * * cd /home/ubuntu/Fastag && /home/ubuntu/Fastag/venv/bin/python /home/ubuntu/Fastag/populate_enhanced_vehicle_cache.py >> /home/ubuntu/Fastag/logs/vehicle_cache_cron.log 2>&1" >> /tmp/current_crontab

# Install the new crontab
crontab /tmp/current_crontab

# Clean up
rm /tmp/current_crontab

echo "✓ Vehicle cache crontab setup complete!"
echo ""
echo "To check if cron job is installed:"
echo "  crontab -l"
echo ""
echo "To view logs:"
echo "  tail -f /home/ubuntu/Fastag/logs/vehicle_cache_cron.log"
echo ""
echo "To remove the cron job:"
echo "  crontab -e"
echo "  (then delete the line with populate_enhanced_vehicle_cache.py)" 