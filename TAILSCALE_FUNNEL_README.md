# Tailscale Funnel Automation Setup

This setup provides automatic Tailscale Funnel management for your Fastag application, ensuring it's always available at `https://pgshospital.tail1b76dc.ts.net/` even when network connectivity is intermittent.

## 🚀 Quick Setup

### 1. Prerequisites
- Tailscale installed and authenticated
- Fastag application running on port 8000
- Root/sudo access

### 2. Run the Setup Script
```bash
sudo ./setup-tailscale-funnel.sh
```

This will:
- ✅ Check Tailscale installation and authentication
- ✅ Verify your Fastag service is running
- ✅ Install the systemd service
- ✅ Enable automatic startup
- ✅ Start the funnel service
- ✅ Test the funnel connection

## 📋 What This Setup Provides

### 🔄 Automatic Management
- **Boot Startup**: Funnel starts automatically when the system boots
- **Network Resilience**: Waits for network connectivity before starting
- **Service Dependency**: Waits for your Fastag service to be available
- **Auto-Restart**: Automatically restarts if the funnel dies
- **Health Monitoring**: Continuously monitors funnel and service status

### 🛡️ Error Handling
- **Network Issues**: Gracefully handles network connectivity problems
- **Service Downtime**: Waits for your application to come back online
- **Tailscale Issues**: Handles Tailscale disconnections and reconnections
- **Process Monitoring**: Detects and restarts dead funnel processes

### 📊 Logging and Monitoring
- **Detailed Logs**: All activities logged to `/home/ubuntu/Fastag/logs/tailscale-funnel.log`
- **Systemd Integration**: Full systemd service with status monitoring
- **Manual Control**: Direct script control for troubleshooting

## 🎯 Your Funnel URL

Once set up, your application will be available at:
```
https://pgshospital.tail1b76dc.ts.net/
```

This URL will:
- ✅ Work from anywhere on the internet
- ✅ Automatically handle SSL/TLS
- ✅ Proxy to your local `http://127.0.0.1:8000`
- ✅ Stay available even during network issues

## 📝 Management Commands

### Service Management
```bash
# Check service status
sudo systemctl status tailscale-funnel

# View logs
sudo journalctl -u tailscale-funnel -f

# Restart service
sudo systemctl restart tailscale-funnel

# Stop service
sudo systemctl stop tailscale-funnel

# Enable auto-start (already done by setup)
sudo systemctl enable tailscale-funnel

# Disable auto-start
sudo systemctl disable tailscale-funnel
```

### Manual Control
```bash
# Start funnel manually
sudo ./tailscale-funnel.sh start

# Stop funnel manually
sudo ./tailscale-funnel.sh stop

# Check funnel status
sudo ./tailscale-funnel.sh status

# View funnel list
tailscale funnel --list
```

### Logs and Debugging
```bash
# View funnel logs
sudo tail -f /home/ubuntu/Fastag/logs/tailscale-funnel.log

# Check if funnel is active
tailscale funnel --list

# Test funnel connectivity
curl -I https://pgshospital.tail1b76dc.ts.net/
```

## 🔧 Configuration

### Environment Variables
The service uses these environment variables (set in `tailscale-funnel.service`):
- `TAILSCALE_FUNNEL_PORT=8000` - Your application port
- `TAILSCALE_FUNNEL_HOSTNAME=pgshospital` - Your funnel hostname

### Customization
To change the port or hostname:
1. Edit `/etc/systemd/system/tailscale-funnel.service`
2. Update the `Environment` lines
3. Restart the service: `sudo systemctl restart tailscale-funnel`

## 🚨 Troubleshooting

### Funnel Not Starting
```bash
# Check if Tailscale is authenticated
tailscale status

# Check if your service is running
netstat -tlnp | grep :8000

# Check service logs
sudo journalctl -u tailscale-funnel -n 20
```

### Funnel Not Accessible
```bash
# Check if funnel is active
tailscale funnel --list

# Test local connectivity
curl -I http://localhost:8000

# Check Tailscale connectivity
tailscale ping pgshospital
```

### Service Won't Start
```bash
# Check systemd status
sudo systemctl status tailscale-funnel

# Check for dependency issues
sudo systemctl list-dependencies tailscale-funnel

# View detailed logs
sudo journalctl -u tailscale-funnel --no-pager
```

## 🔄 How It Works

### Startup Sequence
1. **System Boot**: systemd starts `tailscale-funnel.service`
2. **Dependency Check**: Waits for `tailscaled.service` to be ready
3. **Network Check**: Verifies Tailscale is connected
4. **Service Check**: Waits for port 8000 to be listening
5. **Funnel Start**: Starts `tailscale funnel 8000`
6. **Monitoring**: Continuously monitors health

### Health Monitoring
The service continuously checks:
- ✅ Tailscale connectivity
- ✅ Target service availability (port 8000)
- ✅ Funnel process health
- ✅ Network connectivity

### Auto-Recovery
If any issue is detected:
- 🔄 Waits for network to be available
- 🔄 Waits for service to come back online
- 🔄 Restarts funnel process if needed
- 🔄 Logs all recovery actions

## 📈 Benefits

### For Your Application
- 🌐 **Always Available**: Works even with intermittent network
- 🔒 **Secure**: Automatic SSL/TLS encryption
- ⚡ **Fast**: Direct Tailscale network routing
- 🔄 **Resilient**: Automatic recovery from failures

### For Management
- 📊 **Monitoring**: Full logging and status tracking
- 🛠️ **Easy Management**: Standard systemd commands
- 🔧 **Troubleshooting**: Detailed logs and manual controls
- 🚀 **Zero Maintenance**: Fully automated operation

## 🎉 Success!

Once set up, your Fastag application will be:
- ✅ Automatically available at `https://pgshospital.tail1b76dc.ts.net/`
- ✅ Resilient to network issues
- ✅ Self-healing and self-monitoring
- ✅ Ready for production use

Your funnel will handle all the complexity of network management, allowing you to focus on your application! 