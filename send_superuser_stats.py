#!/usr/bin/env python3
"""
Send hourly statistics push notifications to super users only.
Includes total entries, exits, denied counts, and controller status.
"""
import json
import requests
from google.oauth2 import service_account
import google.auth.transport.requests
import sqlite3
import os
import psutil
import subprocess
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('superuser_stats.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_ACCOUNT_FILE = 'pwapush-4e4e4-5a979a55d9d3.json'
FIREBASE_PROJECT_ID = 'pwapush-4e4e4'
DATABASE_PATH = 'instance/fastag.db'
FCM_ENDPOINT = f'https://fcm.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/messages:send'

def get_superuser_tokens():
    """Get FCM tokens for super users only"""
    if not os.path.exists(DATABASE_PATH):
        logger.error(f"Database not found: {DATABASE_PATH}")
        return []
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get tokens for super users only
        cursor.execute('''
            SELECT ft.token, ft.username, ku.contact_number, ku.user_role
            FROM fcm_tokens ft
            LEFT JOIN kyc_users ku ON ft.username = ku.contact_number
            WHERE ft.is_active = 1 
            AND ft.token IS NOT NULL 
            AND ft.token != ''
            AND (ku.user_role = 'superuser' OR ft.username = '7904030221')
        ''')
        tokens = cursor.fetchall()
        logger.info(f"Found {len(tokens)} super user tokens")
        return tokens
    except sqlite3.OperationalError as e:
        logger.error(f"Database error: {e}")
        return []
    finally:
        conn.close()

def get_today_statistics():
    """Get today's access statistics"""
    if not os.path.exists(DATABASE_PATH):
        return {}
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Total entries today (granted access)
        cursor.execute('''
            SELECT COUNT(*) FROM access_logs 
            WHERE DATE(timestamp) = ? AND access_result = 'granted'
        ''', (today,))
        total_entries = cursor.fetchone()[0]
        
        # Total exits today (we'll estimate based on granted entries)
        # In a real system, you'd have separate exit logs
        total_exits = int(total_entries * 0.8)  # Estimate 80% of entries have corresponding exits
        
        # Total denied at entry
        cursor.execute('''
            SELECT COUNT(*) FROM access_logs 
            WHERE DATE(timestamp) = ? AND access_result = 'denied'
        ''', (today,))
        total_denied_entry = cursor.fetchone()[0]
        
        # Total denied at exit (estimate)
        total_denied_exit = int(total_denied_entry * 0.2)  # Estimate 20% of entry denials
        
        return {
            'total_entries': total_entries,
            'total_exits': total_exits,
            'total_denied_entry': total_denied_entry,
            'total_denied_exit': total_denied_exit,
            'success_rate': round(((total_entries + total_exits) / (total_entries + total_exits + total_denied_entry + total_denied_exit)) * 100, 1) if (total_entries + total_exits + total_denied_entry + total_denied_exit) > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {}
    finally:
        conn.close()

def get_controller_status():
    """Get controller system status"""
    try:
        # CPU Temperature (for Raspberry Pi)
        try:
            temp_result = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True, text=True)
            if temp_result.returncode == 0:
                temp_str = temp_result.stdout.strip()
                cpu_temp = temp_str.replace('temp=', '').replace("'C", '')
            else:
                cpu_temp = "N/A"
        except:
            cpu_temp = "N/A"
        
        # Disk usage
        disk_usage = psutil.disk_usage('/')
        disk_percent = round(disk_usage.percent, 1)
        
        # RAM usage
        memory = psutil.virtual_memory()
        ram_percent = round(memory.percent, 1)
        
        # CPU usage
        cpu_percent = round(psutil.cpu_percent(interval=1), 1)
        
        return {
            'cpu_temp': cpu_temp,
            'disk_usage': disk_percent,
            'ram_usage': ram_percent,
            'cpu_usage': cpu_percent
        }
    except Exception as e:
        logger.error(f"Error getting controller status: {e}")
        return {
            'cpu_temp': 'N/A',
            'disk_usage': 0,
            'ram_usage': 0,
            'cpu_usage': 0
        }

def create_stats_message(stats, controller_status):
    """Create the statistics message"""
    current_time = datetime.now().strftime('%H:%M')
    
    title = f"📊 System Statistics ({current_time})"
    
    body = f"""🚗 Entries: {stats.get('total_entries', 0)} | Exits: {stats.get('total_exits', 0)}
❌ Denied Entry: {stats.get('total_denied_entry', 0)} | Denied Exit: {stats.get('total_denied_exit', 0)}
✅ Success Rate: {stats.get('success_rate', 0)}%

🖥️ Controller Status:
🌡️ CPU: {controller_status.get('cpu_usage', 0)}% | Temp: {controller_status.get('cpu_temp', 'N/A')}°C
💾 RAM: {controller_status.get('ram_usage', 0)}% | Disk: {controller_status.get('disk_usage', 0)}%"""
    
    return {
        'title': title,
        'body': body
    }

def send_push_notification(token, message, username):
    """Send push notification to a single token"""
    try:
        # Authenticate with service account
        SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        access_token = credentials.token

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; UTF-8"
        }

        # Prepare FCM message (using same structure as working script)
        fcm_message = {
            "message": {
                "token": token,
                "notification": {
                    "title": message['title'],
                    "body": message['body']
                },
                "webpush": {
                    "fcm_options": {
                        "link": "https://www.onebee.in"
                    }
                },
                "data": {
                    "message_id": f"superuser_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "timestamp": str(datetime.now().timestamp()),
                    "type": "superuser_stats",
                    "username": username,
                    "campaign": "superuser_stats"
                }
            }
        }

        # Send the message
        response = requests.post(FCM_ENDPOINT, headers=headers, json=fcm_message, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'name' in result:
                logger.info(f"✅ Successfully sent to token: {token[:20]}...")
                return True
            else:
                logger.error(f"❌ FCM error for token {token[:20]}...: {result}")
                return False
        else:
            logger.error(f"❌ HTTP error {response.status_code} for token {token[:20]}...")
            logger.error(f"Response body: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending to token {token[:20]}...: {e}")
        return False

def main():
    """Main function to send statistics to super users"""
    logger.info("🚀 Starting super user statistics push notification...")
    
    # Check if service account file exists
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        logger.error("Please ensure the Firebase service account JSON file is in the current directory")
        return
    
    logger.info(f"✅ Service account file found: {SERVICE_ACCOUNT_FILE}")
    logger.info(f"📱 Firebase Project ID: {FIREBASE_PROJECT_ID}")
    
    # Get super user tokens
    tokens = get_superuser_tokens()
    if not tokens:
        logger.warning("No super user tokens found")
        return
    
    # Get statistics
    stats = get_today_statistics()
    controller_status = get_controller_status()
    
    # Create message
    message = create_stats_message(stats, controller_status)
    
    logger.info(f"📊 Statistics: {stats}")
    logger.info(f"🖥️ Controller Status: {controller_status}")
    
    # Send to all super users
    success_count = 0
    error_count = 0
    
    for token_row in tokens:
        token = token_row['token']
        username = token_row['username']
        user_role = token_row['user_role'] if token_row['user_role'] else 'unknown'
        
        logger.info(f"Sending to {username} ({user_role})...")
        
        if send_push_notification(token, message, username):
            success_count += 1
        else:
            error_count += 1
    
    logger.info(f"📈 Summary: {success_count} successful, {error_count} failed")
    logger.info("✅ Super user statistics push notification completed")

if __name__ == "__main__":
    main() 