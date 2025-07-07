#!/bin/bash

# Fastag Parking Management System - Safe Update Script
# Use this for routine code/feature updates (not for first-time install)

set -e  # Exit on any error

# --- CONFIG ---
APP_DIR="/home/ubuntu/Fastag"
VENV_DIR="$APP_DIR/venv"
PYTHON_EXEC="$VENV_DIR/bin/python3"
GUNICORN_SERVICE="fastag"
LAUNCHER_SCRIPT="$APP_DIR/launcher_readers.py"

cd "$APP_DIR"

echo "========================================="
echo "🚀 Fastag Update Script Starting..."
echo "========================================="

# 1. Pull latest code
echo "🔄 Pulling latest code from git..."
git pull

echo ""
# 2. Activate venv and install dependencies
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ venv not found! Please run deploy.sh first."
    exit 1
fi

echo "🐍 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "📦 Installing/updating Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
# 3. Run safe DB init/migration (idempotent)
echo "🗄️ Running database initialization (safe)..."
$PYTHON_EXEC init_database.py

echo ""
# 4. Restart Gunicorn service
echo "🔁 Restarting Gunicorn (API/web app)..."
sudo systemctl restart $GUNICORN_SERVICE
sleep 2

echo ""
# 5. Restart Nginx
echo "🔁 Restarting Nginx..."
sudo systemctl restart nginx
sleep 2

echo ""
# 6. Restart RFID reader services via launcher
echo "🔁 Restarting RFID reader services..."
$PYTHON_EXEC "$LAUNCHER_SCRIPT"
sleep 2

echo ""
echo "✅ Update complete! Your Fastag app and readers are now running the latest code."
echo "=========================================" 