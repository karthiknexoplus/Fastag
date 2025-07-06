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
sudo -u ubuntu python3 -m venv venv
sudo -u ubuntu /home/ubuntu/Fastag/venv/bin/pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
sudo -u ubuntu /home/ubuntu/Fastag/venv/bin/pip install -r requirements.txt

# Create logs directory
echo "📝 Creating logs directory..."
sudo -u ubuntu mkdir -p /home/ubuntu/Fastag/logs

# Initialize database
echo "🗄️ Initializing database..."
cd /home/ubuntu/Fastag
sudo -u ubuntu /home/ubuntu/Fastag/venv/bin/python init_database.py

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