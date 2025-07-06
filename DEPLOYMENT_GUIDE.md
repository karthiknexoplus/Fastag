# Fastag Parking Management System - EC2 Deployment Guide

This guide will help you deploy your Fastag application to an AWS EC2 instance with Nginx as a reverse proxy.

## Prerequisites

1. **AWS Account** with EC2 access
2. **Domain name** (optional but recommended for SSL)
3. **SSH key pair** for EC2 access
4. **Basic knowledge** of AWS EC2 and Linux commands

## Step 1: Launch EC2 Instance

### 1.1 Create EC2 Instance
1. Go to AWS Console → EC2 → Launch Instance
2. Choose **Ubuntu Server 22.04 LTS** (free tier eligible)
3. Select **t2.micro** (free tier) or larger based on your needs
4. Configure Security Group:
   - **SSH (22)** - Your IP
   - **HTTP (80)** - 0.0.0.0/0
   - **HTTPS (443)** - 0.0.0.0/0 (for SSL later)
5. Launch instance and download your `.pem` key file

### 1.2 Connect to EC2 Instance
```bash
# Make key file executable
chmod 400 your-key.pem

# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## Step 2: Upload Your Application

### Option A: Using Git (Recommended)
```bash
# On your local machine, push to GitHub/GitLab
git add .
git commit -m "Deploy to EC2"
git push origin main

# On EC2 instance
sudo -u ubuntu git clone https://github.com/yourusername/Fastag.git /home/ubuntu/Fastag
```

### Option B: Using SCP
```bash
# From your local machine
scp -i your-key.pem -r /path/to/Fastag ubuntu@your-ec2-public-ip:/home/ubuntu/
```

### Option C: Using AWS S3
```bash
# Upload to S3 from local
aws s3 cp /path/to/Fastag s3://your-bucket/ --recursive

# Download on EC2
sudo -u ubuntu aws s3 cp s3://your-bucket/Fastag /home/ubuntu/ --recursive
```

## Step 3: Run Deployment Script

```bash
# Make script executable
chmod +x /home/ubuntu/Fastag/deploy.sh

# Run deployment script
sudo /home/ubuntu/Fastag/deploy.sh
```

## Step 4: Configure Domain (Optional)

1. **Point your domain** to your EC2 public IP
2. **Update Nginx configuration**:
   ```bash
   sudo nano /etc/nginx/sites-available/fastag
   # Change server_name to your domain
   ```

3. **Reload Nginx**:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Step 5: Set Up SSL (Recommended)

```bash
# Make SSL script executable
chmod +x /home/ubuntu/Fastag/ssl-setup.sh

# Run SSL setup
sudo /home/ubuntu/Fastag/ssl-setup.sh
```

## Step 6: Verify Deployment

### Check Services Status
```bash
# Check Fastag service
sudo systemctl status fastag

# Check Nginx service
sudo systemctl status nginx

# Check if ports are listening
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
sudo netstat -tlnp | grep :8000
```

### Test Application
1. **HTTP**: `http://your-ec2-public-ip` or `http://your-domain.com`
2. **HTTPS**: `https://your-domain.com` (after SSL setup)

## Step 7: Monitoring and Maintenance

### View Logs
```bash
# Application logs
sudo journalctl -u fastag -f

# Nginx access logs
sudo tail -f /var/log/nginx/fastag_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/fastag_error.log

# Gunicorn logs
sudo tail -f /home/ubuntu/Fastag/logs/gunicorn_access.log
sudo tail -f /home/ubuntu/Fastag/logs/gunicorn_error.log
```

### Common Commands
```bash
# Restart application
sudo systemctl restart fastag

# Reload Nginx configuration
sudo systemctl reload nginx

# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
ps aux | grep gunicorn
```

## Troubleshooting

### Application Not Starting
```bash
# Check service status
sudo systemctl status fastag

# Check logs
sudo journalctl -u fastag -n 50

# Test application manually
cd /home/ubuntu/Fastag
source venv/bin/activate
python wsgi.py
```

### Nginx Issues
```bash
# Test Nginx configuration
sudo nginx -t

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check if port 80 is in use
sudo lsof -i :80
```

### Database Issues
```bash
# Check database file
ls -la /home/ubuntu/Fastag/instance/

# Reinitialize database
cd /home/ubuntu/Fastag
source venv/bin/activate
python init_database.py
```

### Permission Issues
```bash
# Fix permissions
sudo chown -R ubuntu:ubuntu /home/ubuntu/Fastag
sudo chmod -R 755 /home/ubuntu/Fastag
```

## Security Considerations

1. **Keep system updated**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Configure firewall** (already done in deploy script):
   ```bash
   sudo ufw status
   ```

3. **Regular backups**:
   ```bash
   # Backup database
   cp /home/ubuntu/Fastag/instance/fastag.db /home/ubuntu/backup/
   ```

4. **Monitor logs** for suspicious activity

## Performance Optimization

1. **Enable Nginx caching** for static files
2. **Configure Gunicorn workers** based on CPU cores
3. **Use CDN** for static assets (optional)
4. **Monitor resource usage** and scale if needed

## Cost Optimization

1. **Use EC2 free tier** for development
2. **Stop instance** when not in use (for dev/test)
3. **Use reserved instances** for production
4. **Monitor AWS billing** regularly

## Next Steps

1. **Set up monitoring** (CloudWatch, etc.)
2. **Configure backups** (S3, RDS)
3. **Set up CI/CD** pipeline
4. **Implement load balancing** for high availability
5. **Add monitoring and alerting**

---

## Quick Reference

| Service | Command | Status |
|---------|---------|--------|
| Fastag | `sudo systemctl status fastag` | Application |
| Nginx | `sudo systemctl status nginx` | Web Server |
| UFW | `sudo ufw status` | Firewall |

| File | Purpose | Location |
|------|---------|----------|
| `gunicorn.conf.py` | Gunicorn config | `/home/ubuntu/Fastag/` |
| `fastag.service` | Systemd service | `/etc/systemd/system/` |
| `nginx.conf` | Nginx config | `/etc/nginx/sites-available/fastag` |

| Port | Service | Purpose |
|------|---------|---------|
| 22 | SSH | Remote access |
| 80 | Nginx | HTTP |
| 443 | Nginx | HTTPS |
| 8000 | Gunicorn | Application (internal) | 