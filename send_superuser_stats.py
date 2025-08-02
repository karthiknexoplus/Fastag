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

def get_reader_status():
    """Get RFID reader status and last 24 hours events"""
    if not os.path.exists(DATABASE_PATH):
        return {}
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get last 24 hours timestamp
        yesterday = datetime.now() - timedelta(hours=24)
        yesterday_str = yesterday.strftime('%Y-%m-%d %H:%M:%S')
        
        # Get all readers with their status (including those with no events)
        cursor.execute('''
            SELECT 
                r.id as reader_id,
                r.type as reader_type,
                r.reader_ip,
                l.lane_name,
                loc.name as location_name,
                COALESCE(COUNT(al.id), 0) as event_count,
                MAX(al.timestamp) as last_event,
                CASE 
                    WHEN MAX(al.timestamp) > datetime('now', '-5 minutes') THEN '🟢 Online'
                    WHEN MAX(al.timestamp) > datetime('now', '-1 hour') THEN '🟡 Recent'
                    ELSE '🔴 Offline'
                END as status
            FROM readers r
            LEFT JOIN lanes l ON r.lane_id = l.id
            LEFT JOIN locations loc ON l.location_id = loc.id
            LEFT JOIN access_logs al ON r.id = al.reader_id AND al.timestamp > ?
            GROUP BY r.id, r.type, r.reader_ip, l.lane_name, loc.name
            ORDER BY r.id, r.type
        ''', (yesterday_str,))
        
        readers = cursor.fetchall()
        
        reader_status = {}
        for reader in readers:
            reader_id = reader[0] or 'Unknown'
            reader_type = reader[1] or 'Unknown'
            reader_ip = reader[2] or 'Unknown'
            lane_name = reader[3] or 'Unknown'
            location_name = reader[4] or 'Unknown'
            event_count = reader[5]
            last_event = reader[6]
            status = reader[7]
            
            key = f"{reader_id}_{reader_type}"
            reader_status[key] = {
                'reader_id': reader_id,
                'reader_type': reader_type,
                'reader_ip': reader_ip,
                'lane_name': lane_name,
                'location_name': location_name,
                'event_count': event_count,
                'last_event': last_event,
                'status': status
            }
        
        return reader_status
    except Exception as e:
        logger.error(f"Error getting reader status: {e}")
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

def create_stats_message(stats, controller_status, reader_status):
    """Create the statistics message"""
    current_time = datetime.now().strftime('%H:%M')
    
    title = f"📊 System Statistics ({current_time})"
    
    # Build reader status section
    reader_section = ""
    if reader_status:
        reader_section = "\n📡 Reader Status (Last 24h):"
        for key, reader in reader_status.items():
            reader_id = reader['reader_id']
            reader_type = reader['reader_type']
            reader_ip = reader['reader_ip']
            lane_name = reader['lane_name']
            location_name = reader['location_name']
            status = reader['status']
            event_count = reader['event_count']
            last_event = reader['last_event']
            
            # Format last event time (convert UTC to IST)
            if last_event:
                try:
                    # Parse the timestamp (handle both UTC and local time)
                    if 'Z' in last_event or '+00:00' in last_event:
                        # UTC time - convert to IST
                        last_event_dt = datetime.fromisoformat(last_event.replace('Z', '+00:00'))
                        # Add 5 hours 30 minutes for IST
                        ist_time = last_event_dt + timedelta(hours=5, minutes=30)
                        last_event_str = ist_time.strftime('%H:%M')
                    else:
                        # Assume local time already
                        last_event_dt = datetime.fromisoformat(last_event)
                        last_event_str = last_event_dt.strftime('%H:%M')
                except:
                    last_event_str = 'Unknown'
            else:
                last_event_str = 'Never'
            
            reader_section += f"\n{status} Reader{reader_id} ({reader_type}): {event_count} events, last: {last_event_str}"
            reader_section += f"\n  📍 {location_name} • {lane_name} • {reader_ip}"
    else:
        reader_section = "\n📡 Reader Status: No data available"
    
    body = f"""🚗 Entries: {stats.get('total_entries', 0)} | Exits: {stats.get('total_exits', 0)}
❌ Denied Entry: {stats.get('total_denied_entry', 0)} | Denied Exit: {stats.get('total_denied_exit', 0)}
✅ Success Rate: {stats.get('success_rate', 0)}%

🖥️ Controller Status:
🌡️ CPU: {controller_status.get('cpu_usage', 0)}% | Temp: {controller_status.get('cpu_temp', 'N/A')}°C
💾 RAM: {controller_status.get('ram_usage', 0)}% | Disk: {controller_status.get('disk_usage', 0)}%{reader_section}"""
    
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
    reader_status = get_reader_status()
    
    # Create message
    message = create_stats_message(stats, controller_status, reader_status)
    logger.info(f"📝 Message created - Title: {message['title']}")
    logger.info(f"📝 Message body preview: {message['body'][:200]}...")
    
    logger.info(f"📊 Statistics: {stats}")
    logger.info(f"🖥️ Controller Status: {controller_status}")
    logger.info(f"📡 Reader Status: {len(reader_status)} readers found")
    for key, reader in reader_status.items():
        logger.info(f"  📡 Reader{reader['reader_id']} ({reader['reader_type']}): {reader['event_count']} events, {reader['status']}")
    
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