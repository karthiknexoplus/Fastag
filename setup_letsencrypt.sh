#!/bin/bash
# Let's Encrypt SSL certificate setup for FASTag PWA

DOMAIN="your-domain.com"
EMAIL="your-email@example.com"

# Install certbot if not installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
fi

# Get SSL certificate
echo "Getting SSL certificate for $DOMAIN..."
sudo certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive

# Set up auto-renewal
echo "Setting up auto-renewal..."
sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -

echo "SSL certificate setup complete!"
echo "Your site should now be accessible at https://$DOMAIN"
