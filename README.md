# Fastag Parking Management System

A comprehensive parking management system with RFID reader integration, location management, and API endpoints for external devices.

## 🚀 Quick Deployment

After cloning the repository to your EC2 instance, simply run:

```bash
sudo ./deploy.sh
```

That's it! The script handles everything automatically.

## 🌐 Features

- **User Management**: Secure login system
- **Location Management**: Add/edit parking locations
- **Lane Management**: Configure entry/exit lanes
- **Reader Management**: Manage RFID readers with MAC addresses
- **API Endpoints**: External device integration
- **Real-time Monitoring**: Live system status
- **SSL Support**: Automatic Let's Encrypt certificates

## 🔧 Prerequisites

- Ubuntu Server 22.04 LTS (recommended)
- EC2 Security Group with ports 22, 80, 443 open
- Domain name (optional, for SSL)

## 📋 What the Deployment Script Does

1. **System Setup**: Updates packages, installs dependencies
2. **Application Setup**: Creates Python environment, installs requirements
3. **Database Setup**: Initializes database (no sample data)
4. **Web Server**: Configures Nginx with your domain
5. **SSL Certificate**: Automatic Let's Encrypt setup (optional)
6. **Firewall**: Configures UFW with proper rules
7. **Services**: Sets up systemd services with auto-start
8. **Testing**: Verifies everything works correctly

## 🌐 Access Your Application

After deployment, your application will be available at:

- **HTTP**: `http://your-domain-or-ip`
- **HTTPS**: `https://your-domain` (if SSL was set up)
- **Signup**: Create your first user account
- **API**: `http://your-domain/api/device/[mac-address]`

## 📊 API Endpoints

### Device Lookup
```
GET /api/device/{mac_address}
```

### Device Registration
```
POST /api/device/register
Content-Type: application/json

{
    "mac_address": "00:11:22:33:44:55"
}
```

### System Status
```
GET /api/status
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

## 🔒 Security Features

- **Firewall**: UFW configured with necessary ports
- **SSL/TLS**: Automatic Let's Encrypt certificates
- **Secure Headers**: Nginx security headers
- **Database**: SQLite with proper permissions
- **Process Isolation**: Systemd service management

## 📝 Database

The database is initialized empty with no sample data. You can:
1. Create your first user through the signup page
2. Add locations, lanes, and readers through the web interface
3. Use the API endpoints for external device integration

## 🎉 Success!

Your Fastag Parking Management System is now ready for production use! 