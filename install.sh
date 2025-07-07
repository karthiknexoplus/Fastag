#!/bin/bash

# Fastag Parking Management System - Local/RPi Installation Script
# This script is for local or Raspberry Pi deployments (no public IP/domain required)
# It skips OS update/upgrade and gives an option to skip SSL setup

set -e  # Exit on any error

echo "🚀 Starting Fastag Local/RPi Installation..."
echo "==========================================="
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
    read -p "Enter your domain name (or press Enter to use localhost): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        DOMAIN="localhost"
        echo "Using localhost as domain."
    fi
    echo "$DOMAIN"
}

# Function to create Nginx config (HTTP or HTTPS)
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
    
    # Static files
    location /static/ {
        alias /var/www/fastag_static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin "*";
        location ~* \\.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|eot|svg)$ {
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
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
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
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    access_log /var/log/nginx/fastag_access.log;
    error_log /var/log/nginx/fastag_error.log;
    location /static/ {
        alias /var/www/fastag_static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin "*";
        location ~* \\.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|eot|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header Access-Control-Allow-Origin "*";
        }
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;
}
EOF
    fi
}

# --- SKIP OS UPDATE/UPGRADE ---

# Install required packages (assume user has already updated system if needed)
echo "🔧 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx sqlite3 git curl

# (Certbot and ufw will only be installed if SSL is chosen)

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /home/ubuntu/Fastag
sudo chown ubuntu:ubuntu /home/ubuntu/Fastag

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd /home/ubuntu/Fastag
if [ -d "venv" ]; then
    echo "🗑️ Removing existing virtual environment..."
    sudo -u ubuntu rm -rf venv
fi
sudo -u ubuntu /usr/bin/python3 -m venv venv
sleep 2
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment creation failed"
    exit 1
fi
PYTHON_EXEC=$(detect_python)
if [ "$PYTHON_EXEC" = "ERROR" ]; then
    echo "❌ Error: Could not find Python executable in virtual environment"
    exit 1
fi
echo "✅ Using Python executable: $PYTHON_EXEC"
sudo -u ubuntu $PYTHON_EXEC --version
echo "⬆️ Upgrading pip..."
sudo -u ubuntu $PYTHON_EXEC -m pip install --upgrade pip
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
echo "🗄️ Initializing database..."
sudo -u ubuntu $PYTHON_EXEC init_database.py
if [ ! -f "instance/fastag.db" ]; then
    echo "❌ Error: Database file was not created"
    exit 1
fi
echo "🔧 Fixing database permissions..."
sudo chown ubuntu:ubuntu instance/fastag.db
sudo chmod 644 instance/fastag.db
echo "✅ Database initialized successfully"

# Test DB and Flask app (same as deploy.sh)
# ... (keep the same DB and Flask app test code) ...

# Set up systemd service
echo "⚙️ Setting up systemd service..."
sudo cp /home/ubuntu/Fastag/fastag.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fastag

echo ""
echo "🌐 Domain & SSL Configuration..."
DOMAIN=$(get_domain)

# Ask if user wants SSL
read -p "Do you want to set up SSL with a real certificate? (y/n): " SETUP_SSL
if [[ "$SETUP_SSL" =~ ^[Yy]$ ]]; then
    # Install certbot and ufw if needed
    sudo apt install -y certbot python3-certbot-nginx ufw
    # Certbot and firewall setup
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    # Obtain certificate
    sudo certbot --nginx -d "$DOMAIN"
    create_nginx_config "$DOMAIN" "true"
else
    # HTTP only
    create_nginx_config "$DOMAIN" "false"
    # Only open HTTP port
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw --force enable
fi

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/fastag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "🧪 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    sudo nginx -t
    exit 1
fi

echo "🚀 Starting Nginx..."
sudo systemctl restart nginx
sleep 3
if curl -s -I "http://localhost" > /dev/null 2>&1; then
    echo "✅ Nginx is running successfully"
else
    echo "❌ Nginx is not responding. See systemctl status nginx and logs."
    sudo systemctl status nginx --no-pager
    sudo journalctl -u nginx -n 20 --no-pager
    exit 1
fi

echo "🚀 Starting Gunicorn via systemd..."
sudo systemctl start fastag
sleep 5
if curl -s -I "http://localhost:8000" > /dev/null 2>&1; then
    echo "✅ Gunicorn is running successfully"
else
    echo "❌ Gunicorn is not responding after all checks. See systemctl status fastag and logs."
    sudo systemctl status fastag --no-pager
    sudo journalctl -u fastag -n 20 --no-pager
    exit 1
fi

echo "🎉 Fastag Local/RPi Installation Complete!" 