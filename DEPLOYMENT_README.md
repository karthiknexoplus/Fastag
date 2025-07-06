# Fastag Parking Management System - Deployment Guide

## 🚀 Quick Deployment (One Command)

After cloning the repository to your EC2 instance, simply run:

```bash
sudo ./deploy.sh
```

That's it! The script handles everything automatically.

## 📋 What the Deployment Script Does

### 1. **System Setup**
- Updates Ubuntu packages
- Installs Python, Nginx, SQLite, Certbot, and UFW firewall

### 2. **Application Setup**
- Creates Python virtual environment
- Installs all Python dependencies
- Sets up database with sample data
- Configures proper permissions

### 3. **Web Server Setup**
- Configures Nginx as reverse proxy
- Sets up firewall rules
- Enables and starts services

### 4. **SSL Certificate (Optional)**
- Automatically detects your domain
- Sets up Let's Encrypt SSL certificate
- Configures automatic renewal

### 5. **Verification**
- Tests database connection
- Verifies application is running
- Shows service status

## 🌐 Access Your Application

After deployment, your application will be available at:

- **HTTP**: `http://your-domain-or-ip`
- **HTTPS**: `https://your-domain` (if SSL was set up)
- **Login**: `admin` / `admin123`
- **API**: `http://your-domain/api/device/00:00:00:00`

## 🔧 Prerequisites

### For EC2:
1. **Ubuntu Server 22.04 LTS** (recommended)
2. **Security Group** with ports 22, 80, 443 open
3. **Domain name** (optional, for SSL)

### For Local Development:
1. **Python 3.8+**
2. **Git**

## 📝 Step-by-Step Manual Deployment

If you prefer manual deployment:

```bash
# 1. Clone repository
git clone https://github.com/yourusername/Fastag.git
cd Fastag

# 2. Run deployment script
sudo ./deploy.sh

# 3. Follow the prompts
# - Enter your domain name (or press Enter for IP)
# - Choose whether to set up SSL
```

## 🔍 Troubleshooting

### Check Service Status
```bash
sudo systemctl status fastag
sudo systemctl status nginx
```

### View Logs
```bash
sudo journalctl -u fastag -f
sudo tail -f /var/log/nginx/fastag_error.log
```

### Restart Services
```bash
sudo systemctl restart fastag
sudo systemctl restart nginx
```

### Manual SSL Setup
```bash
sudo certbot --nginx -d your-domain.com
```

## 📊 Application Features

- **User Management**: Admin login system
- **Location Management**: Add/edit parking locations
- **Lane Management**: Configure entry/exit lanes
- **Reader Management**: Manage RFID readers
- **API Endpoints**: External device integration
- **Real-time Monitoring**: Live system status

## 🔒 Security Features

- **Firewall**: UFW configured with necessary ports
- **SSL/TLS**: Automatic Let's Encrypt certificates
- **Secure Headers**: Nginx security headers
- **Database**: SQLite with proper permissions
- **Process Isolation**: Systemd service management

## 📞 Support

If you encounter issues:

1. Check the logs: `sudo journalctl -u fastag -f`
2. Verify services: `sudo systemctl status fastag`
3. Test database: `python3 debug-app.py`
4. Check permissions: `ls -la /home/ubuntu/Fastag/`

## 🎉 Success!

Your Fastag Parking Management System is now ready for production use! 