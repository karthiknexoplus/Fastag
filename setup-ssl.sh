#!/bin/bash

echo "🔒 Manual SSL Certificate Setup"
echo "==============================="
echo ""

# Check if we're in the right directory
if [ ! -f "wsgi.py" ]; then
    echo "❌ Error: wsgi.py not found. Make sure you're in the Fastag directory."
    exit 1
fi

# Get domain name
read -p "Enter your domain name: " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "❌ Domain name is required!"
    exit 1
fi

echo "🌐 Setting up SSL for domain: $DOMAIN"
echo ""

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
fi

# Backup current nginx config
echo "💾 Backing up current nginx configuration..."
sudo cp /etc/nginx/sites-available/fastag /etc/nginx/sites-available/fastag.backup

# Test current nginx config
echo "🧪 Testing current nginx configuration..."
if sudo nginx -t; then
    echo "✅ Current nginx configuration is valid"
else
    echo "❌ Current nginx configuration has errors"
    echo "Restoring backup..."
    sudo cp /etc/nginx/sites-available/fastag.backup /etc/nginx/sites-available/fastag
    sudo nginx -t
    exit 1
fi

# Restart nginx to ensure clean state
echo "🔄 Restarting nginx..."
sudo systemctl restart nginx

# Wait a moment
sleep 3

# Get SSL certificate
echo "🎫 Obtaining SSL certificate..."
if sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN"; then
    echo "✅ SSL certificate obtained successfully!"
    
    # Set up automatic renewal
    echo "⏰ Setting up automatic renewal..."
    (sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -
    
    # Test renewal
    echo "🔄 Testing certificate renewal..."
    sudo certbot renew --dry-run
    
    # Test nginx config
    echo "🧪 Testing nginx configuration after SSL setup..."
    if sudo nginx -t; then
        echo "✅ Nginx configuration is valid"
        sudo systemctl reload nginx
        echo "✅ SSL setup completed successfully!"
        echo ""
        echo "🌐 Your application is now available at:"
        echo "   https://$DOMAIN"
    else
        echo "❌ Nginx configuration error after SSL setup"
        echo "Restoring backup..."
        sudo cp /etc/nginx/sites-available/fastag.backup /etc/nginx/sites-available/fastag
        sudo systemctl reload nginx
        exit 1
    fi
else
    echo "❌ SSL certificate setup failed"
    echo "Possible issues:"
    echo "1. Domain DNS is not pointing to this server"
    echo "2. Port 80 is not accessible from internet"
    echo "3. Domain is not accessible"
    echo ""
    echo "To troubleshoot:"
    echo "1. Check DNS: nslookup $DOMAIN"
    echo "2. Check connectivity: curl -I http://$DOMAIN"
    echo "3. Check nginx: sudo nginx -t"
    exit 1
fi

echo ""
echo "🎉 SSL setup completed!"
echo "Your application is now secure at: https://$DOMAIN" 