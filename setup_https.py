#!/usr/bin/env python3
"""
Setup HTTPS for PWA development and production
HTTPS is required for service workers to function properly
"""

import os
import ssl
import subprocess
from pathlib import Path

def create_self_signed_cert():
    """Create self-signed certificate for development"""
    
    cert_dir = Path('ssl')
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = cert_dir / 'cert.pem'
    key_file = cert_dir / 'key.pem'
    
    if cert_file.exists() and key_file.exists():
        print("SSL certificates already exist")
        return
    
    print("Creating self-signed SSL certificate...")
    
    # Generate certificate
    cmd = [
        'openssl', 'req', '-x509', '-newkey', 'rsa:4096', 
        '-keyout', str(key_file), '-out', str(cert_file),
        '-days', '365', '-nodes',
        '-subj', '/C=IN/ST=State/L=City/O=FASTag/CN=localhost'
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"SSL certificate created: {cert_file}")
        print(f"SSL key created: {key_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating SSL certificate: {e}")
        print("You may need to install OpenSSL")
    except FileNotFoundError:
        print("OpenSSL not found. Please install OpenSSL to create certificates.")

def create_https_server():
    """Create HTTPS server configuration"""
    
    config_content = '''from fastag import create_app
import ssl

app = create_app()

if __name__ == '__main__':
    # SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('ssl/cert.pem', 'ssl/key.pem')
    
    # Run with HTTPS
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=8443,
        ssl_context=context
    )
'''
    
    with open('https_server.py', 'w') as f:
        f.write(config_content)
    
    print("HTTPS server configuration created: https_server.py")

def create_nginx_config():
    """Create nginx configuration for production HTTPS"""
    
    nginx_config = '''server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/your/fastag/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
'''
    
    with open('nginx_fastag.conf', 'w') as f:
        f.write(nginx_config)
    
    print("Nginx configuration created: nginx_fastag.conf")
    print("Remember to:")
    print("1. Replace 'your-domain.com' with your actual domain")
    print("2. Update SSL certificate paths")
    print("3. Update static files path")

def create_letsencrypt_script():
    """Create Let's Encrypt setup script"""
    
    script_content = '''#!/bin/bash
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
'''
    
    with open('setup_letsencrypt.sh', 'w') as f:
        f.write(script_content)
    
    # Make executable
    os.chmod('setup_letsencrypt.sh', 0o755)
    
    print("Let's Encrypt setup script created: setup_letsencrypt.sh")
    print("Remember to update the domain and email in the script")

def main():
    print("FASTag PWA HTTPS Setup")
    print("=" * 30)
    
    print("\n1. Creating self-signed certificate for development...")
    create_self_signed_cert()
    
    print("\n2. Creating HTTPS server configuration...")
    create_https_server()
    
    print("\n3. Creating nginx configuration for production...")
    create_nginx_config()
    
    print("\n4. Creating Let's Encrypt setup script...")
    create_letsencrypt_script()
    
    print("\n" + "=" * 30)
    print("HTTPS Setup Complete!")
    print("\nFor Development:")
    print("  python3 https_server.py")
    print("  Access: https://localhost:8443")
    
    print("\nFor Production:")
    print("  1. Update nginx_fastag.conf with your domain")
    print("  2. Run: ./setup_letsencrypt.sh")
    print("  3. Configure nginx with the provided config")
    
    print("\nNote: HTTPS is required for PWA service workers to function!")

if __name__ == '__main__':
    main() 