#!/bin/bash

# SSL Certificate Setup with Let's Encrypt
# Run this script after your domain is pointing to your EC2 instance

set -e

echo "🔒 Setting up SSL certificate with Let's Encrypt..."

# Install Certbot
echo "📦 Installing Certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Get your domain name
read -p "Enter your domain name (e.g., example.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "❌ Domain name is required!"
    exit 1
fi

# Obtain SSL certificate
echo "🎫 Obtaining SSL certificate for $DOMAIN..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Test auto-renewal
echo "🔄 Testing certificate renewal..."
sudo certbot renew --dry-run

# Set up automatic renewal
echo "⏰ Setting up automatic renewal..."
sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -

echo "✅ SSL certificate setup completed!"
echo ""
echo "🔍 Check certificate status:"
echo "   sudo certbot certificates"
echo ""
echo "🌐 Your application is now accessible at: https://$DOMAIN" 