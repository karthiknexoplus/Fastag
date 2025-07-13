#!/bin/bash
set -e
BACKUP_DIR="/home/ubuntu/Fastag/db_backups"
DB_PATH="/home/ubuntu/Fastag/instance/fastag.db"
DATE=$(date +%Y-%m-%d)
BACKUP_FILE="$BACKUP_DIR/fastag_$DATE.db"
EC2_USER=ubuntu
EC2_HOST=13.61.147.37
EC2_PATH=/home/ubuntu/backups/avhifield/
EC2_KEY="/home/ubuntu/Fastag/nexoplus.pem"

mkdir -p "$BACKUP_DIR"
cp "$DB_PATH" "$BACKUP_FILE"

# Upload to EC2
scp -i "$EC2_KEY" "$BACKUP_FILE" "$EC2_USER@$EC2_HOST:$EC2_PATH" 