#!/bin/bash

# Fastag Parking Management System - Complete EC2 Deployment Script
# Run this script on your EC2 instance as root or with sudo
# This script handles everything: setup, database, permissions, SSL, etc.

set -e  # Exit on any error

echo "🚀 Starting Complete Fastag Deployment on EC2..."
echo "================================================"
echo ""

# Function to detect Python executable
detect_python() {
    if [ -f "venv/bin/python3" ]; then
        echo "venv/bin/python3"
    elif [ -f "venv/bin/python" ]; then
        echo "venv/bin/python"
    else
        echo "ERROR"
    fi
}

# Function to get domain name
get_domain() {
    read -p "Enter your domain name (or press Enter to use EC2 public IP): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        # Get EC2 public IP
        DOMAIN=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
        echo "Using EC2 public IP: $DOMAIN"
    fi
    echo "$DOMAIN"
}

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx sqlite3 git curl certbot python3-certbot-nginx ufw

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /home/ubuntu/Fastag
sudo chown ubuntu:ubuntu /home/ubuntu/Fastag

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

PYTHON_EXEC=$(detect_python)
if [ "$PYTHON_EXEC" = "ERROR" ]; then
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

# Get domain name for Nginx configuration
echo ""
echo "🌐 Domain Configuration..."
DOMAIN=$(get_domain)

# Configure Nginx with the correct domain
echo "🌐 Configuring Nginx for domain: $DOMAIN"
sudo cp /home/ubuntu/Fastag/nginx.conf /etc/nginx/sites-available/fastag

# Update Nginx configuration with the correct domain
sudo sed -i "s/your-domain.com www.your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/fastag

sudo ln -sf /etc/nginx/sites-available/fastag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Test Nginx configuration
sudo nginx -t

# Start Nginx
echo "🚀 Starting Nginx..."
sudo systemctl enable nginx
sudo systemctl restart nginx

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

# Set proper permissions
echo "🔐 Setting proper permissions..."
sudo chown -R ubuntu:ubuntu /home/ubuntu/Fastag
sudo chmod -R 755 /home/ubuntu/Fastag
sudo chmod 644 /home/ubuntu/Fastag/instance/fastag.db

# Start the application
echo "🚀 Starting Fastag application..."
sudo systemctl start fastag

# Wait for application to start
sleep 5

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

# SSL Setup (if domain is provided and not localhost)
if [[ "$DOMAIN" != "localhost" && "$DOMAIN" != "127.0.0.1" ]]; then
    echo ""
    echo "🔒 SSL Certificate Setup..."
    echo "Domain: $DOMAIN"
    read -p "Do you want to set up SSL certificate with Let's Encrypt? (y/n): " SETUP_SSL
    
    if [[ "$SETUP_SSL" =~ ^[Yy]$ ]]; then
        echo "🎫 Obtaining SSL certificate..."
        
        # Temporarily modify Nginx config for SSL verification
        sudo sed -i 's/listen 80;/listen 80;\n    listen 443 ssl;/' /etc/nginx/sites-available/fastag
        
        # Get SSL certificate
        if sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN"; then
            echo "✅ SSL certificate obtained successfully!"
            
            # Set up automatic renewal
            echo "⏰ Setting up automatic renewal..."
            (sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -
            
            # Test renewal
            echo "🔄 Testing certificate renewal..."
            sudo certbot renew --dry-run
            
            echo "✅ SSL setup completed!"
        else
            echo "⚠️ SSL certificate setup failed. You can set it up manually later."
            echo "   Run: sudo certbot --nginx -d $DOMAIN"
        fi
    else
        echo "⏭️ Skipping SSL setup"
    fi
else
    echo "⏭️ Skipping SSL setup (using localhost/IP)"
fi

echo ""
echo "✅ Complete deployment finished successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "======================"
echo "🌐 Application URL: http://$DOMAIN"
if [[ "$DOMAIN" != "localhost" && "$DOMAIN" != "127.0.0.1" ]]; then
    echo "🔒 HTTPS URL: https://$DOMAIN (if SSL was set up)"
fi
echo "👤 Login: admin / admin123"
echo "📊 API Endpoint: http://$DOMAIN/api/device/00:00:00:00"
echo ""
echo "🔍 Service Status:"
echo "   sudo systemctl status fastag"
echo "   sudo systemctl status nginx"
echo ""
echo "📊 View Logs:"
echo "   sudo journalctl -u fastag -f"
echo "   sudo tail -f /var/log/nginx/fastag_error.log"
echo ""
echo "🔄 Restart Services:"
echo "   sudo systemctl restart fastag"
echo "   sudo systemctl restart nginx"
echo ""
echo "🎉 Your Fastag Parking Management System is ready!" 