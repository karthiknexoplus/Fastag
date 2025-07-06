#!/bin/bash

# Fastag Parking Management System - EC2 Deployment Script
# Run this script on your EC2 instance as root or with sudo

set -e  # Exit on any error

echo "🚀 Starting Fastag deployment on EC2..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx sqlite3 git curl

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /home/ubuntu/Fastag
sudo chown ubuntu:ubuntu /home/ubuntu/Fastag

# Clone or copy your application (if using git)
# sudo -u ubuntu git clone <your-repo-url> /home/ubuntu/Fastag
# OR copy files manually to /home/ubuntu/Fastag

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd /home/ubuntu/Fastag

# Remove existing venv if it exists and is corrupted
if [ -d "venv" ]; then
    echo "🗑️ Removing existing virtual environment..."
    sudo -u ubuntu rm -rf venv
fi

# Create virtual environment with explicit Python path
echo "🔧 Creating virtual environment..."
sudo -u ubuntu /usr/bin/python3 -m venv venv

# Wait a moment for venv creation to complete
sleep 2

# Check if venv was created successfully
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment creation failed"
    exit 1
fi

# Determine the correct Python executable name
echo "🔍 Checking Python executables in virtual environment..."
ls -la venv/bin/python*

if [ -f "venv/bin/python3" ]; then
    PYTHON_EXEC="venv/bin/python3"
elif [ -f "venv/bin/python" ]; then
    PYTHON_EXEC="venv/bin/python"
else
    echo "❌ Error: Could not find Python executable in virtual environment"
    echo "Contents of venv/bin/:"
    ls -la venv/bin/
    exit 1
fi

echo "✅ Using Python executable: $PYTHON_EXEC"

# Test the Python executable
echo "🧪 Testing Python executable..."
sudo -u ubuntu $PYTHON_EXEC --version

# Upgrade pip
echo "⬆️ Upgrading pip..."
sudo -u ubuntu $PYTHON_EXEC -m pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
sudo -u ubuntu $PYTHON_EXEC -m pip install -r requirements.txt

# Create logs directory
echo "📝 Creating logs directory..."
sudo -u ubuntu mkdir -p /home/ubuntu/Fastag/logs

# Set up database directory and initialize database
echo "🗄️ Setting up database..."
cd /home/ubuntu/Fastag

# Create instance directory if it doesn't exist
if [ ! -d "instance" ]; then
    echo "📂 Creating instance directory..."
    sudo -u ubuntu mkdir -p instance
fi

# Initialize database
echo "🗄️ Initializing database..."
sudo -u ubuntu $PYTHON_EXEC init_database.py

# Verify database was created
if [ ! -f "instance/fastag.db" ]; then
    echo "❌ Error: Database file was not created"
    exit 1
fi

echo "✅ Database initialized successfully"

# Test database connection
echo "🧪 Testing database connection..."
sudo -u ubuntu $PYTHON_EXEC -c "
from fastag import create_app
app = create_app()
with app.app_context():
    from fastag.utils.db import get_db
    db = get_db()
    locations = db.execute('SELECT * FROM locations').fetchall()
    print(f'✅ Database test successful - Found {len(locations)} locations')
"

# Set up systemd service
echo "⚙️ Setting up systemd service..."
sudo cp /home/ubuntu/Fastag/fastag.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fastag
sudo systemctl start fastag

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo cp /home/ubuntu/Fastag/nginx.conf /etc/nginx/sites-available/fastag
sudo ln -sf /etc/nginx/sites-available/fastag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Test Nginx configuration
sudo nginx -t

# Start Nginx
echo "🚀 Starting Nginx..."
sudo systemctl enable nginx
sudo systemctl restart nginx

# Configure firewall (if using UFW)
echo "🔥 Configuring firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

# Set proper permissions
echo "🔐 Setting proper permissions..."
sudo chown -R ubuntu:ubuntu /home/ubuntu/Fastag
sudo chmod -R 755 /home/ubuntu/Fastag

# Final verification
echo "🔍 Final verification..."
echo "Checking application status..."
sudo systemctl status fastag --no-pager

echo "Testing application..."
sleep 3  # Give the service time to start
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Application is responding on localhost:8000"
else
    echo "⚠️ Application may not be fully started yet"
fi

echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Update the server_name in /etc/nginx/sites-available/fastag"
echo "2. Configure your domain DNS to point to this EC2 instance"
echo "3. Set up SSL certificate with Let's Encrypt (recommended)"
echo ""
echo "🔍 Check application status:"
echo "   sudo systemctl status fastag"
echo "   sudo systemctl status nginx"
echo ""
echo "📊 View logs:"
echo "   sudo journalctl -u fastag -f"
echo "   sudo tail -f /var/log/nginx/fastag_error.log"
echo ""
echo "🌐 Your application should be accessible at: http://your-ec2-public-ip" 