#!/bin/bash

# Fastag Parking Management System - Bulletproof EC2 Deployment Script
# Run this script on your EC2 instance as root or with sudo
# This script handles everything: setup, database, permissions, SSL, etc.

set -e  # Exit on any error

echo "🚀 Starting Bulletproof Fastag Deployment on EC2..."
echo "=================================================="
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

# Function to create bulletproof Nginx config
create_nginx_config() {
    local domain=$1
    local use_ssl=$2
    
    if [ "$use_ssl" = "true" ]; then
        # HTTPS configuration
        sudo tee /etc/nginx/sites-available/fastag > /dev/null << EOF
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name $domain;
    return 301 https://\$server_name\$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name $domain;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;
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
    
    # Static files - serve from /var/www/fastag_static (guaranteed access)
    location /static/ {
        alias /var/www/fastag_static/;
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
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
EOF
    else
        # HTTP-only configuration
        sudo tee /etc/nginx/sites-available/fastag > /dev/null << EOF
server {
    listen 80;
    server_name $domain;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Logs
    access_log /var/log/nginx/fastag_access.log;
    error_log /var/log/nginx/fastag_error.log;
    
    # Static files - serve from /var/www/fastag_static (guaranteed access)
    location /static/ {
        alias /var/www/fastag_static/;
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
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
EOF
    fi
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

# Create logs directory and fix permissions
echo "📝 Creating logs directory..."
sudo -u ubuntu mkdir -p /home/ubuntu/Fastag/logs
sudo chown -R ubuntu:ubuntu /home/ubuntu/Fastag/logs
sudo chmod -R 755 /home/ubuntu/Fastag/logs

# Ensure Gunicorn config is correct
echo "🔧 Ensuring Gunicorn configuration..."
if [ ! -f "gunicorn.conf.py" ]; then
    echo "❌ Gunicorn config file missing"
    exit 1
fi

# Set up database directory and initialize database
echo "🗄️ Setting up database..."
cd /home/ubuntu/Fastag

# Initialize database with comprehensive error handling
echo "🗄️ Initializing database..."
sudo -u ubuntu $PYTHON_EXEC init_database.py

# Verify database was created
if [ ! -f "instance/fastag.db" ]; then
    echo "❌ Error: Database file was not created"
    exit 1
fi

# Fix database permissions
echo "🔧 Fixing database permissions..."
sudo chown ubuntu:ubuntu instance/fastag.db
sudo chmod 644 instance/fastag.db

echo "✅ Database initialized successfully"

# Comprehensive database testing
echo "🧪 Testing database connection..."
sudo -u ubuntu $PYTHON_EXEC -c "
import sqlite3
import os

# Test direct database access
db_path = '/home/ubuntu/Fastag/instance/fastag.db'
print(f'Testing database: {db_path}')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
    tables = cursor.fetchall()
    print(f'✅ Database accessible - Found {len(tables)} tables:')
    for table in tables:
        print(f'   - {table[0]}')
    
    # Check users table
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    print(f'✅ Users in database: {user_count}')
    
    # Check locations table
    cursor.execute('SELECT COUNT(*) FROM locations')
    location_count = cursor.fetchone()[0]
    print(f'✅ Locations in database: {location_count}')
    
    conn.close()
    print('✅ Database connection test successful')
    
except Exception as e:
    print(f'❌ Database error: {e}')
    exit(1)
"

# Test Flask app import and DB connection before enabling Gunicorn service
echo "🧪 Testing Flask app import and DB connection..."
sudo -u ubuntu $PYTHON_EXEC -c "
import sys
import traceback
try:
    from fastag import create_app
    app = create_app()
    with app.app_context():
        from fastag.utils.db import get_db
        db = get_db()
        result = db.execute('SELECT COUNT(*) FROM users').fetchone()
        print(f'✅ Flask app and DB test passed: {result[0]} users')
except Exception as e:
    print(f'❌ Flask app/DB error: {e}')
    traceback.print_exc()
    sys.exit(1)
"

echo "✅ Flask and Gunicorn startup checks passed. Proceeding to enable systemd service."

# Set up systemd service
echo "⚙️ Setting up systemd service..."
sudo cp /home/ubuntu/Fastag/fastag.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fastag

# Get domain name for Nginx configuration
echo ""
echo "🌐 Domain Configuration..."
DOMAIN=$(get_domain)

# Set up static files directory with proper permissions
echo "📁 Setting up static files directory..."
sudo mkdir -p /var/www/fastag_static
sudo cp -r /home/ubuntu/Fastag/fastag/static/* /var/www/fastag_static/ 2>/dev/null || echo "Static files already copied"
sudo chown -R www-data:www-data /var/www/fastag_static
sudo chmod -R 755 /var/www/fastag_static
sudo chmod 644 /var/www/fastag_static/*

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Start Gunicorn via systemd
echo "🚀 Starting Gunicorn via systemd..."
sudo systemctl start fastag
sleep 5

# Test Gunicorn one last time
echo "🧪 Final Gunicorn test..."
if curl -s -I "http://localhost:8000" > /dev/null 2>&1; then
    echo "✅ Gunicorn is running successfully"
else
    echo "❌ Gunicorn is not responding after all checks. See systemctl status fastag and logs."
    sudo systemctl status fastag --no-pager
    sudo journalctl -u fastag -n 20 --no-pager
    exit 1
fi

# Configure Nginx (HTTP only initially)
echo "🌐 Configuring Nginx for domain: $DOMAIN"
create_nginx_config "$DOMAIN" "false"

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/fastag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    sudo nginx -t
    exit 1
fi

# Start Nginx
echo "🚀 Starting Nginx..."
sudo systemctl restart nginx

# Test Nginx
echo "🧪 Testing Nginx..."
sleep 3
if curl -s -I "http://localhost" > /dev/null 2>&1; then
    echo "✅ Nginx is working (localhost)"
elif curl -s -I "http://$DOMAIN" > /dev/null 2>&1; then
    echo "✅ Nginx is working (domain)"
else
    echo "❌ Nginx is not responding properly"
    echo "Checking Nginx error logs..."
    sudo tail -n 10 /var/log/nginx/error.log
    sudo systemctl status nginx
    exit 1
fi

# Test static files
echo "🧪 Testing static files..."
if curl -s -I "http://localhost/static/logo.png" | grep -q "200 OK"; then
    echo "✅ Static files are accessible"
else
    echo "❌ Static files are not accessible"
    echo "Checking static files directory..."
    ls -la /var/www/fastag_static/
fi

# SSL Setup (only if domain is not localhost)
if [[ "$DOMAIN" != "localhost" && "$DOMAIN" != "127.0.0.1" ]]; then
    echo ""
    echo "🔒 SSL Certificate Setup..."
    read -p "Do you want to set up SSL certificate for $DOMAIN? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🧪 Testing domain accessibility..."
        if curl -s -I "http://$DOMAIN" > /dev/null 2>&1; then
            echo "✅ Domain is accessible"
        else
            echo "⚠️ Domain may not be accessible yet (DNS propagation)"
            echo "Continuing with SSL setup..."
        fi
        
        # Get SSL certificate
        if sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN"; then
            echo "✅ SSL certificate obtained successfully!"
            
            # Update Nginx config with SSL
            echo "🔧 Updating Nginx configuration with SSL..."
            create_nginx_config "$DOMAIN" "true"
            
            # Test Nginx configuration
            if sudo nginx -t; then
                echo "✅ Nginx configuration is valid with SSL"
                sudo systemctl reload nginx
            else
                echo "❌ Nginx configuration error after SSL setup"
                sudo nginx -t
                exit 1
            fi
            
            # Set up automatic renewal
            echo "⏰ Setting up automatic renewal..."
            (sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -
            
            # Test renewal
            echo "🔄 Testing certificate renewal..."
            sudo certbot renew --dry-run
            
            SSL_SETUP_SUCCESS=true
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

# Comprehensive testing
echo "🧪 Comprehensive Application Testing..."
sleep 3

# Test Gunicorn directly
echo "Testing Gunicorn (port 8000)..."
if curl -s -I "http://localhost:8000" | head -1; then
    echo "✅ Gunicorn is responding"
else
    echo "❌ Gunicorn is not responding"
fi

# Test Nginx proxy
echo "Testing Nginx proxy (port 80)..."
if curl -s -I "http://localhost" | head -1; then
    echo "✅ Nginx proxy is working"
else
    echo "❌ Nginx proxy is not working"
fi

# Test static files through Nginx
echo "Testing static files through Nginx..."
if curl -s -I "http://localhost/static/logo.png" | grep -q "200 OK"; then
    echo "✅ Static files are accessible via Nginx"
else
    echo "❌ Static files are not accessible via Nginx"
fi

# Test static files through Gunicorn
echo "Testing static files through Gunicorn..."
if curl -s -I "http://localhost:8000/static/logo.png" | grep -q "200 OK"; then
    echo "✅ Static files are accessible via Gunicorn"
else
    echo "❌ Static files are not accessible via Gunicorn"
fi

# Test domain access (if not localhost)
if [[ "$DOMAIN" != "localhost" && "$DOMAIN" != "127.0.0.1" ]]; then
    echo "Testing domain access..."
    if curl -s -I "http://$DOMAIN" | head -1; then
        echo "✅ Domain is accessible via HTTP"
    else
        echo "⚠️ Domain may not be accessible yet (DNS propagation)"
    fi
    
    # Test HTTPS if SSL was set up
    if [[ "$SSL_SETUP_SUCCESS" == "true" ]]; then
        echo "Testing HTTPS access..."
        if curl -s -I "https://$DOMAIN" | head -1; then
            echo "✅ Domain is accessible via HTTPS"
        else
            echo "⚠️ HTTPS may not be accessible yet"
        fi
        
        echo "Testing static files via HTTPS..."
        if curl -s -I "https://$DOMAIN/static/logo.png" | grep -q "200 OK"; then
            echo "✅ Static files are accessible via HTTPS"
        else
            echo "❌ Static files are not accessible via HTTPS"
        fi
    fi
fi

echo ""
echo "🎉 Deployment Summary:"
echo "======================"
echo "✅ Application: Fastag Parking Management System"
echo "✅ Domain: $DOMAIN"
echo "✅ Gunicorn: Running on port 8000"
echo "✅ Nginx: Running and proxying to Gunicorn"
echo "✅ Static Files: Served from /var/www/fastag_static"
echo "✅ Database: SQLite initialized"
echo "✅ Firewall: Configured (ports 22, 80, 443 open)"
if [[ "$SSL_SETUP_SUCCESS" == "true" ]]; then
    echo "✅ SSL: Certificate installed and auto-renewal configured"
else
    echo "⚠️ SSL: Not configured (can be added later)"
fi

echo ""
echo "🌐 Access your application:"
if [[ "$SSL_SETUP_SUCCESS" == "true" ]]; then
    echo "   HTTPS: https://$DOMAIN"
    echo "   HTTP: http://$DOMAIN (redirects to HTTPS)"
else
    echo "   HTTP: http://$DOMAIN"
fi

echo ""
echo "📋 Useful commands:"
echo "   Check status: sudo systemctl status fastag"
echo "   View logs: sudo journalctl -u fastag -f"
echo "   Restart app: sudo systemctl restart fastag"
echo "   Check Nginx: sudo systemctl status nginx"
echo "   View Nginx logs: sudo tail -f /var/log/nginx/fastag_error.log"

echo ""
echo "🎯 Deployment completed successfully!" 