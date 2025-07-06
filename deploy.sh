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

# Initialize database (script will create instance directory if needed)
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
    print(f'✅ Database test successful - Database initialized with {len(locations)} locations')
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

# Backup nginx config for SSL setup
sudo cp /etc/nginx/sites-available/fastag /etc/nginx/sites-available/fastag.backup

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

# Ensure static files are accessible
echo "🖼️ Setting up static files..."
sudo chown -R ubuntu:www-data /home/ubuntu/Fastag/fastag/static/
sudo chmod -R 755 /home/ubuntu/Fastag/fastag/static/
sudo chmod 644 /home/ubuntu/Fastag/fastag/static/*

# Test static file accessibility
echo "🧪 Testing static file accessibility..."
if [ -f "/home/ubuntu/Fastag/fastag/static/logo.png" ]; then
    echo "✅ Logo file exists and is accessible"
else
    echo "❌ Logo file not found"
fi

if [ -f "/home/ubuntu/Fastag/fastag/static/branding.jpg" ]; then
    echo "✅ Branding image exists and is accessible"
else
    echo "❌ Branding image not found"
fi

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
        
        # Ensure nginx is running and accessible
        echo "🔄 Ensuring nginx is running..."
        sudo systemctl restart nginx
        sleep 3
        
        # Test domain accessibility
        echo "🧪 Testing domain accessibility..."
        if curl -s -I "http://$DOMAIN" > /dev/null 2>&1; then
            echo "✅ Domain is accessible"
        else
            echo "⚠️ Domain may not be accessible yet (DNS propagation)"
            echo "Continuing with SSL setup..."
        fi
        
        # Get SSL certificate (certbot will handle nginx config automatically)
        if sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN" --redirect; then
            echo "✅ SSL certificate obtained successfully!"
            
            # Fix static file handling after SSL setup
            echo "🔧 Fixing static file handling after SSL setup..."
            
            # Create a proper nginx config with static files
            sudo tee /etc/nginx/sites-available/fastag > /dev/null << 'EOF'
server {
    listen 80;
    listen 443 ssl;
    server_name fastag.onebee.in;
    
    # SSL Configuration (certbot will add this)
    ssl_certificate /etc/letsencrypt/live/fastag.onebee.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fastag.onebee.in/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Logs
    access_log /var/log/nginx/fastag_access.log;
    error_log /var/log/nginx/fastag_error.log;
    
    # Static files - serve directly from nginx for better performance
    location /static/ {
        alias /home/ubuntu/Fastag/fastag/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin "*";
        
        # Handle common static file types
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|eot|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header Access-Control-Allow-Origin "*";
        }
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name fastag.onebee.in;
    return 301 https://$server_name$request_uri;
}
EOF
            
            # Set up automatic renewal
            echo "⏰ Setting up automatic renewal..."
            (sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -
            
            # Test renewal
            echo "🔄 Testing certificate renewal..."
            sudo certbot renew --dry-run
            
            # Test nginx config
            echo "🧪 Testing nginx configuration..."
            if sudo nginx -t; then
                echo "✅ Nginx configuration is valid"
                sudo systemctl reload nginx
                echo "✅ SSL setup completed successfully!"
                SSL_SETUP_SUCCESS=true
            else
                echo "❌ Nginx configuration error after SSL setup"
                echo "Restoring original configuration..."
                sudo cp /etc/nginx/sites-available/fastag.backup /etc/nginx/sites-available/fastag 2>/dev/null || echo "No backup found"
                sudo systemctl reload nginx
                SSL_SETUP_SUCCESS=false
            fi
        else
            echo "⚠️ SSL certificate setup failed"
            echo "This might be due to:"
            echo "1. DNS not pointing to this server yet"
            echo "2. Domain not accessible from internet"
            echo "3. Port 80 not open"
            echo ""
            echo "You can set it up manually later with:"
            echo "   sudo certbot --nginx -d $DOMAIN"
            SSL_SETUP_SUCCESS=false
        fi
    else
        echo "⏭️ Skipping SSL setup"
        SSL_SETUP_SUCCESS=false
    fi
else
    echo "⏭️ Skipping SSL setup (using localhost/IP)"
    SSL_SETUP_SUCCESS=false
fi

echo ""
echo "✅ Complete deployment finished successfully!"
echo ""
echo "🧪 Final Application Test..."
sleep 5

# Test application endpoints
echo "Testing application endpoints..."
if curl -s -I "http://localhost:8000" > /dev/null; then
    echo "✅ Application is responding on localhost:8000"
else
    echo "⚠️ Application may not be fully started yet"
fi

# Test static files
echo "Testing static files..."
if curl -s -I "http://localhost:8000/static/logo.png" > /dev/null; then
    echo "✅ Static files are accessible"
else
    echo "⚠️ Static files may not be accessible"
fi

echo ""
echo "📋 Deployment Summary:"
echo "======================"
if [[ "$SSL_SETUP_SUCCESS" == "true" ]]; then
    echo "🌐 Application URL: https://$DOMAIN (SSL enabled)"
    echo "📊 API Endpoint: https://$DOMAIN/api/device/00:00:00:00"
else
    echo "🌐 Application URL: http://$DOMAIN"
    echo "📊 API Endpoint: http://$DOMAIN/api/device/00:00:00:00"
    if [[ "$DOMAIN" != "localhost" && "$DOMAIN" != "127.0.0.1" ]]; then
        echo "💡 To enable SSL later: sudo certbot --nginx -d $DOMAIN"
    fi
fi
echo "👤 Login: Create your first user through the signup page"
echo "📝 Database: Empty (no sample data) - add your own data through the web interface"
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