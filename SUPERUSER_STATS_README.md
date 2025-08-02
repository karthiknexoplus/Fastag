# Super User Statistics Push Notifications

## 📋 Overview

This system sends hourly statistics push notifications to super users only, providing real-time insights into system performance and access control metrics.

## 🎯 Features

### **📊 Statistics Included:**
- **🚗 Total Entries Today** - Number of successful vehicle entries
- **🚪 Total Exits Today** - Number of successful vehicle exits  
- **❌ Denied at Entry** - Number of denied access attempts at entry
- **❌ Denied at Exit** - Number of denied access attempts at exit
- **✅ Success Rate** - Percentage of successful access attempts

### **🖥️ Controller Status:**
- **🌡️ CPU Temperature** - Raspberry Pi CPU temperature
- **⚡ CPU Usage** - Current CPU utilization percentage
- **💾 RAM Usage** - Current memory usage percentage
- **💿 Disk Usage** - Current disk space usage percentage

## 👥 Target Users

Only users with `user_role = 'superuser'` or phone numbers containing `7904030221` will receive these notifications.

## ⏰ Frequency

Notifications are sent **every hour** automatically via systemd timer.

## 🏗️ Implementation

### **Files Created:**

1. **`send_superuser_stats.py`** - Main script that:
   - Fetches super user FCM tokens from database
   - Collects today's access statistics
   - Gets controller system status
   - Sends formatted push notifications

2. **`superuser-stats.service`** - Systemd service file
3. **`superuser-stats.timer`** - Systemd timer (runs every hour)
4. **`setup_superuser_stats.sh`** - Installation script

## 🚀 Installation

### **Step 1: Install Dependencies**
```bash
# Install psutil for system monitoring
pip install psutil
```

### **Step 2: Setup Service**
```bash
# Run the setup script as root
sudo ./setup_superuser_stats.sh
```

### **Step 3: Verify Installation**
```bash
# Check timer status
systemctl status superuser-stats.timer

# View recent logs
journalctl -u superuser-stats.service -f
```

## 📱 Sample Notification

```
📊 System Statistics (14:30)

🚗 Entries: 45 | Exits: 36
❌ Denied Entry: 3 | Denied Exit: 1
✅ Success Rate: 95.3%

🖥️ Controller Status:
🌡️ CPU: 12.5% | Temp: 45.2°C
💾 RAM: 68.2% | Disk: 23.1%
```

## 🔧 Configuration

### **Database Path**
Update `DATABASE_PATH` in `send_superuser_stats.py` if needed:
```python
DATABASE_PATH = 'instance/fastag.db'
```

### **Firebase Configuration**
Ensure these files exist:
- `pwapush-4e4e4-5a979a55d9d3.json` (Service account key)
- Update `FIREBASE_PROJECT_ID` if needed

### **User Detection**
Super users are identified by:
1. `user_role = 'superuser'` in `kyc_users` table
2. Phone numbers containing `7904030221`

## 📊 Monitoring

### **Check Service Status:**
```bash
systemctl status superuser-stats.timer
systemctl status superuser-stats.service
```

### **View Logs:**
```bash
# View all logs
journalctl -u superuser-stats.service

# Follow logs in real-time
journalctl -u superuser-stats.service -f

# View logs from today
journalctl -u superuser-stats.service --since today
```

### **Test Manually:**
```bash
# Run the script manually
python send_superuser_stats.py

# Or trigger the service
sudo systemctl start superuser-stats.service
```

## 🛠️ Troubleshooting

### **Common Issues:**

1. **No super users found**
   - Check if users have `user_role = 'superuser'`
   - Verify FCM tokens are active

2. **Service account error**
   - Ensure `pwapush-4e4e4-5a979a55d9d3.json` exists
   - Check Firebase project ID

3. **Database errors**
   - Verify database path is correct
   - Check database permissions

4. **System monitoring errors**
   - Install `psutil`: `pip install psutil`
   - For Raspberry Pi temperature, ensure `vcgencmd` is available

### **Log Files:**
- **System logs**: `journalctl -u superuser-stats.service`
- **Script logs**: `superuser_stats.log`

## 🔄 Customization

### **Change Frequency:**
Edit `superuser-stats.timer`:
```ini
# Every 30 minutes
OnCalendar=*:0/30

# Every 2 hours  
OnCalendar=0/2:0

# Daily at 9 AM
OnCalendar=09:00:00
```

### **Modify Statistics:**
Edit `get_today_statistics()` in `send_superuser_stats.py` to include additional metrics.

### **Custom Message Format:**
Edit `create_stats_message()` to change notification appearance.

## 📈 Benefits

- **Real-time monitoring** of system performance
- **Proactive alerts** for system issues
- **Access control insights** for super users
- **Automated reporting** without manual intervention
- **System health tracking** with temperature and resource usage

## 🔐 Security

- Only super users receive notifications
- Uses existing FCM infrastructure
- Secure service account authentication
- Database-based user role verification 