#!/bin/bash

# Change to the Fastag directory
cd /home/ubuntu/Fastag

# Activate virtual environment
source venv/bin/activate

# Run the push notification script
python send_fcm_push_v1.py

# Log the execution
echo "$(date): Push notifications sent" >> /home/ubuntu/Fastag/logs/cron_notifications.log 