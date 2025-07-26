from flask import Blueprint, render_template, jsonify, request
from fastag.utils.db import get_db
from datetime import datetime, timedelta
import sqlite3
import json
import pytz

analytics_bp = Blueprint('analytics', __name__)

def get_analytics_data():
    """Get comprehensive analytics data"""
    db = get_db()
    
    # Current date and time ranges
    now = datetime.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # 1. Current Occupancy (SLOW: correlated subquery)
    current_occupancy_rows = db.execute("""
        SELECT al1.tag_id
        FROM access_logs al1
        WHERE al1.access_result = 'granted'
        AND al1.timestamp = (
            SELECT MAX(al2.timestamp)
            FROM access_logs al2
            WHERE al2.tag_id = al1.tag_id
        )
    """).fetchall()
    current_occupancy = len(current_occupancy_rows)
    # Breakdown by tag type
    occ_fastag = 0
    occ_car_oem = 0
    occ_other = 0
    for row in current_occupancy_rows:
        tag_id = row[0]
        if tag_id.startswith('34161'):
            occ_fastag += 1
        elif tag_id.startswith('E20'):
            occ_car_oem += 1
        else:
            occ_other += 1
    current_occupancy_breakdown = {
        'fastag': occ_fastag,
        'car_oem': occ_car_oem,
        'other': occ_other,
        'total': current_occupancy
    }
    
    # 2. Today's Statistics
    today_stats_row = db.execute("""
        SELECT 
            COUNT(*) as total_events,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as granted,
            SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied
        FROM access_logs 
        WHERE DATE(timestamp) = DATE('now')
    """).fetchone()
    today_stats = list(today_stats_row) if today_stats_row else [0, 0, 0]
    
    # 3. Hourly Activity (Last 24 hours)
    hourly_data = [list(row) for row in db.execute("""
        SELECT 
            strftime('%H', timestamp) as hour,
            COUNT(*) as total,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as granted,
            SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied
        FROM access_logs 
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY strftime('%H', timestamp)
        ORDER BY hour
    """).fetchall()]
    
    # 4. Lane Utilization (now loaded via /api/lane-utilization)
    lane_utilization = None
    # 6. Top Users (now loaded via /api/top-users)
    top_users = None
    # 7. Denied Access Analysis (now loaded via /api/denied-analysis)
    denied_analysis = None
    
    # 8. Recent Activity (Last 50 events) - with cached vehicle details
    recent_activity_rows = db.execute("""
        SELECT 
            al.timestamp,
            al.tag_id,
            al.access_result,
            al.reason,
            ku.name as user_name,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            tvc.fuel_type,
            l.lane_name,
            r.reader_ip,
            r.type as reader_type,
            ku.vehicle_number as kyc_vehicle_number
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        JOIN readers r ON al.reader_id = r.id
        WHERE al.timestamp >= datetime('now', '-24 hours')
        ORDER BY al.timestamp DESC
        LIMIT 50
    """).fetchall()
    
    # Convert UTC timestamps to IST
    ist_tz = pytz.timezone('Asia/Kolkata')
    recent_activity = []
    for row in recent_activity_rows:
        # Parse the UTC timestamp and convert to IST
        timestamp_str = row[0]
        
        # Handle different timestamp formats
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            # ISO format with Z (UTC)
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            # ISO format without Z, assume UTC
            utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            # SQLite datetime format, assume UTC
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
        
        # Convert to IST (UTC + 5:30)
        ist_time = utc_time.astimezone(ist_tz)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Create new row with IST timestamp
        new_row = list(row)
        new_row[0] = ist_time_str
        recent_activity.append(new_row)
    
    # 9. Weekly Trends
    weekly_trends = [list(row) for row in db.execute("""
        SELECT 
            strftime('%Y-%W', timestamp) as week,
            COUNT(*) as total_events,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as granted,
            SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied
        FROM access_logs 
        WHERE timestamp >= datetime('now', '-8 weeks')
        GROUP BY strftime('%Y-%W', timestamp)
        ORDER BY week DESC
        LIMIT 8
    """).fetchall()]
    
    # 10. Suspicious Activity (Multiple denied attempts) - with vehicle numbers
    suspicious_activity_rows = db.execute("""
        SELECT 
            al.tag_id,
            COUNT(*) as denied_count,
            MAX(al.timestamp) as last_attempt,
            GROUP_CONCAT(al.reason) as reasons,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        WHERE al.access_result = 'denied' 
        AND al.timestamp >= datetime('now', '-24 hours')
        GROUP BY al.tag_id, ku.vehicle_number, tvc.vehicle_number
        HAVING denied_count > 3
        ORDER BY denied_count DESC
    """).fetchall()
    
    # Convert UTC timestamps to IST for suspicious activity
    suspicious_activity = []
    for row in suspicious_activity_rows:
        # Parse the UTC timestamp and convert to IST
        timestamp_str = row[2]  # last_attempt is at index 2
        
        # Handle different timestamp formats
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            # ISO format with Z (UTC)
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            # ISO format without Z, assume UTC
            utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            # SQLite datetime format, assume UTC
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
        
        # Convert to IST (UTC + 5:30)
        ist_time = utc_time.astimezone(ist_tz)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Create new row with IST timestamp
        new_row = list(row)
        new_row[2] = ist_time_str
        suspicious_activity.append(new_row)
    
    # --- FASTag vs Non-FASTag (today, unique tags) ---
    fastag_vs_nonfastag_row = db.execute('''
        SELECT
            COUNT(DISTINCT CASE WHEN tag_id LIKE '34161%' THEN tag_id END) as fastag_count,
            COUNT(DISTINCT CASE WHEN tag_id NOT LIKE '34161%' THEN tag_id END) as nonfastag_count
        FROM access_logs
        WHERE DATE(timestamp) = DATE('now')
    ''').fetchone()
    fastag_vs_nonfastag = {
        'fastag': fastag_vs_nonfastag_row[0] or 0,
        'nonfastag': fastag_vs_nonfastag_row[1] or 0
    }

    # --- Overstayed Vehicles (inside > 8h) ---
    overstayed = db.execute('''
        SELECT COUNT(*) FROM (
            SELECT tag_id, MAX(timestamp) as last_entry
            FROM access_logs WHERE access_result = 'granted'
            GROUP BY tag_id
            HAVING last_entry <= datetime('now', '-8 hours')
        )
    ''').fetchone()[0]

    # --- Unique Vehicles Today ---
    unique_vehicles_today = db.execute('''
        SELECT COUNT(DISTINCT tag_id) FROM access_logs WHERE DATE(timestamp) = DATE('now')
    ''').fetchone()[0]

    # --- Recent Entry/Exit Trend (today, per hour) ---
    entry_exit_trend = [list(row) for row in db.execute('''
        SELECT strftime('%H', timestamp) as hour,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as entries,
            SUM(CASE WHEN access_result = 'exit' THEN 1 ELSE 0 END) as exits
        FROM access_logs
        WHERE DATE(timestamp) = DATE('now')
        GROUP BY hour
        ORDER BY hour
    ''').fetchall()]

    # --- Unique Tags Breakdown (all events today) ---
    unique_tags_rows = db.execute('''
        SELECT tag_id FROM access_logs WHERE DATE(timestamp) = DATE('now')
    ''').fetchall()
    unique_tags_set = set()
    fastag_count = 0
    car_oem_count = 0
    other_count = 0
    for row in unique_tags_rows:
        tag_id = row[0]
        if tag_id not in unique_tags_set:
            unique_tags_set.add(tag_id)
            if tag_id.startswith('34161'):
                fastag_count += 1
            elif tag_id.startswith('E20'):
                car_oem_count += 1
            else:
                other_count += 1
    unique_tags_breakdown = {
        'fastag': fastag_count,
        'car_oem': car_oem_count,
        'other': other_count,
        'total': len(unique_tags_set)
    }

    # --- Unique Tags Denied Breakdown (denied events today) ---
    denied_tags_rows = db.execute('''
        SELECT tag_id FROM access_logs WHERE DATE(timestamp) = DATE('now') AND access_result = 'denied'
    ''').fetchall()
    denied_tags_set = set()
    denied_fastag_count = 0
    denied_car_oem_count = 0
    denied_other_count = 0
    for row in denied_tags_rows:
        tag_id = row[0]
        if tag_id not in denied_tags_set:
            denied_tags_set.add(tag_id)
            if tag_id.startswith('34161'):
                denied_fastag_count += 1
            elif tag_id.startswith('E20'):
                denied_car_oem_count += 1
            else:
                denied_other_count += 1
    unique_tags_denied_breakdown = {
        'fastag': denied_fastag_count,
        'car_oem': denied_car_oem_count,
        'other': denied_other_count,
        'total': len(denied_tags_set)
    }

    return {
        'current_occupancy': current_occupancy,
        'current_occupancy_breakdown': current_occupancy_breakdown,
        'today_stats': {
            'total': today_stats[0],
            'granted': today_stats[1],
            'denied': today_stats[2]
        },
        'hourly_data': hourly_data,
        'lane_utilization': lane_utilization,
        'top_users': top_users,
        'denied_analysis': denied_analysis,
        'recent_activity': recent_activity,
        'weekly_trends': weekly_trends,
        'suspicious_activity': suspicious_activity,
        'fastag_vs_nonfastag': fastag_vs_nonfastag,
        'overstayed': overstayed,
        'unique_vehicles_today': unique_vehicles_today,
        'entry_exit_trend': entry_exit_trend,
        'unique_tags_breakdown': unique_tags_breakdown,
        'unique_tags_denied_breakdown': unique_tags_denied_breakdown
    }

@analytics_bp.route('/dashboard')
def dashboard():
    """Main analytics dashboard"""
    return render_template('analytics/dashboard.html')

@analytics_bp.route('/api/analytics-data')
def analytics_data():
    """API endpoint for analytics data"""
    try:
        data = get_analytics_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/current-occupancy-details')
def current_occupancy_details():
    """API endpoint to get current occupancy details (fast: only last 24h)"""
    try:
        db = get_db()
        vehicles = db.execute("""
            SELECT 
                al1.tag_id,
                COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
                COALESCE(ku.name, tvc.owner_name) as owner_name,
                tvc.model_name,
                tvc.fuel_type,
                al1.timestamp as entry_time,
                l.lane_name,
                ROUND((julianday('now') - julianday(al1.timestamp)) * 24, 1) as duration_hours
            FROM access_logs al1
            LEFT JOIN kyc_users ku ON al1.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al1.tag_id = tvc.tag_id
            JOIN lanes l ON al1.lane_id = l.id
            WHERE al1.access_result = 'granted'
              AND al1.timestamp >= datetime('now', '-24 hours')
              AND al1.timestamp = (
                  SELECT MAX(al2.timestamp)
                  FROM access_logs al2
                  WHERE al2.tag_id = al1.tag_id
                    AND al2.timestamp >= datetime('now', '-24 hours')
              )
              AND NOT EXISTS (
                  SELECT 1 FROM access_logs al3
                  WHERE al3.tag_id = al1.tag_id
                    AND al3.timestamp > al1.timestamp
                    AND al3.timestamp >= datetime('now', '-24 hours')
                    AND al3.access_result = 'denied'
              )
            ORDER BY al1.timestamp DESC
        """).fetchall()
        
        # Convert UTC timestamps to IST
        ist_tz = pytz.timezone('Asia/Kolkata')
        formatted_vehicles = []
        
        for vehicle in vehicles:
            timestamp_str = vehicle[5]  # entry_time
            if 'T' in timestamp_str and 'Z' in timestamp_str:
                utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif 'T' in timestamp_str:
                utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
            else:
                utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                utc_time = utc_time.replace(tzinfo=pytz.UTC)
            ist_time = utc_time.astimezone(ist_tz)
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
            duration_hours = vehicle[7] or 0
            if duration_hours < 1:
                duration = f"{int(duration_hours * 60)} minutes"
            else:
                duration = f"{duration_hours:.1f} hours"
            formatted_vehicles.append({
                'tag_id': vehicle[0],
                'vehicle_number': vehicle[1],
                'owner_name': vehicle[2],
                'model_name': vehicle[3],
                'fuel_type': vehicle[4],
                'entry_time': ist_time_str,
                'lane_name': vehicle[6],
                'duration': duration
            })
        
        return jsonify({'vehicles': formatted_vehicles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/today-granted-details')
def today_granted_details():
    """API endpoint to get today's granted entries details"""
    try:
        db = get_db()
        
        # Get today's granted entries with vehicle details
        vehicles = db.execute("""
            SELECT 
                al.tag_id,
                COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
                COALESCE(ku.name, tvc.owner_name) as owner_name,
                tvc.model_name,
                tvc.fuel_type,
                al.timestamp as entry_time,
                l.lane_name,
                r.reader_ip
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
            JOIN lanes l ON al.lane_id = l.id
            JOIN readers r ON al.reader_id = r.id
            WHERE al.access_result = 'granted'
            AND DATE(al.timestamp) = DATE('now')
            ORDER BY al.timestamp DESC
        """).fetchall()
        
        # Convert UTC timestamps to IST
        ist_tz = pytz.timezone('Asia/Kolkata')
        formatted_vehicles = []
        
        for vehicle in vehicles:
            # Parse the UTC timestamp and convert to IST
            timestamp_str = vehicle[5]  # entry_time
            
            # Handle different timestamp formats
            if 'T' in timestamp_str and 'Z' in timestamp_str:
                # ISO format with Z (UTC)
                utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif 'T' in timestamp_str:
                # ISO format without Z, assume UTC
                utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
            else:
                # SQLite datetime format, assume UTC
                utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                utc_time = utc_time.replace(tzinfo=pytz.UTC)
            
            # Convert to IST
            ist_time = utc_time.astimezone(ist_tz)
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
            
            formatted_vehicles.append({
                'tag_id': vehicle[0],
                'vehicle_number': vehicle[1],
                'owner_name': vehicle[2],
                'model_name': vehicle[3],
                'fuel_type': vehicle[4],
                'entry_time': ist_time_str,
                'lane_name': vehicle[6],
                'reader_ip': vehicle[7]
            })
        
        return jsonify({'vehicles': formatted_vehicles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/today-denied-details')
def today_denied_details():
    try:
        db = get_db()
        denied_entries = db.execute("""
            SELECT 
                al.tag_id,
                COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
                COALESCE(ku.name, tvc.owner_name) as owner_name,
                tvc.model_name,
                tvc.fuel_type,
                al.timestamp,
                al.reason,
                l.lane_name,
                r.reader_ip,
                r.type as reader_type
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
            JOIN lanes l ON al.lane_id = l.id
            JOIN readers r ON al.reader_id = r.id
            WHERE al.access_result = 'denied'
            AND DATE(al.timestamp) = DATE('now')
            ORDER BY al.timestamp DESC
        """).fetchall()
        ist_tz = pytz.timezone('Asia/Kolkata')
        formatted_entries = []
        tag_categories = {'fastag': 0, 'car_oem': 0, 'other': 0}
        unique_tags = set()
        # Reader stats with bifurcation
        reader_stats = {'entry_readers': {}, 'exit_readers': {}}
        for entry in denied_entries:
            timestamp_str = entry[5]
            if 'T' in timestamp_str and 'Z' in timestamp_str:
                utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif 'T' in timestamp_str:
                utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
            else:
                utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                utc_time = utc_time.replace(tzinfo=pytz.UTC)
            ist_time = utc_time.astimezone(ist_tz)
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
            tag_id = entry[0]
            unique_tags.add(tag_id)
            if tag_id.startswith('34161'):
                tag_type = 'FASTag'
                tag_categories['fastag'] += 1
            elif tag_id.startswith('E20'):
                tag_type = 'CAR OEM'
                tag_categories['car_oem'] += 1
            else:
                tag_type = 'Other'
                tag_categories['other'] += 1
            reader_name = f"{entry[8]} ({entry[7]})"
            reader_type = entry[9]
            # --- Bifurcation logic ---
            stats_dict = reader_stats['entry_readers' if reader_type == 'entry' else 'exit_readers']
            if reader_name not in stats_dict:
                stats_dict[reader_name] = {'total': 0, 'fastag': 0, 'car_oem': 0, 'other': 0}
            stats_dict[reader_name]['total'] += 1
            if tag_type == 'FASTag':
                stats_dict[reader_name]['fastag'] += 1
            elif tag_type == 'CAR OEM':
                stats_dict[reader_name]['car_oem'] += 1
            else:
                stats_dict[reader_name]['other'] += 1
            formatted_entries.append({
                'tag_id': tag_id,
                'tag_type': tag_type,
                'vehicle_number': entry[1],
                'owner_name': entry[2],
                'model_name': entry[3],
                'fuel_type': entry[4],
                'timestamp': ist_time_str,
                'reason': entry[6],
                'lane_name': entry[7],
                'reader_name': reader_name
            })
        # Convert to list for frontend
        def reader_stats_list(stats_dict):
            return [
                {
                    'reader_name': name,
                    'total': stat['total'],
                    'fastag': stat['fastag'],
                    'car_oem': stat['car_oem'],
                    'other': stat['other']
                }
                for name, stat in sorted(stats_dict.items(), key=lambda x: x[1]['total'], reverse=True)
            ]
        entry_readers = reader_stats_list(reader_stats['entry_readers'])
        exit_readers = reader_stats_list(reader_stats['exit_readers'])
        return jsonify({
            'summary': {
                'fastag_count': tag_categories['fastag'],
                'car_oem_count': tag_categories['car_oem'],
                'other_count': tag_categories['other'],
                'unique_tags': len(unique_tags)
            },
            'reader_stats': {
                'entry_readers': entry_readers,
                'exit_readers': exit_readers
            },
            'entries': formatted_entries
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/reports')
def reports():
    """Reports page"""
    return render_template('analytics/reports.html')

@analytics_bp.route('/api/export-data')
def export_data():
    """Export data as CSV"""
    import csv
    from io import StringIO
    
    report_type = request.args.get('type', 'access_logs')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    vehicle_number = request.args.get('vehicle_number', '')
    
    db = get_db()
    
    if report_type == 'access_logs':
        query = """
            SELECT 
                al.timestamp,
                al.tag_id,
                al.access_result,
                al.reason,
                ku.name as user_name,
                COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
                COALESCE(ku.name, tvc.owner_name) as owner_name,
                tvc.model_name,
                tvc.fuel_type,
                l.lane_name,
                r.reader_ip
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
            JOIN lanes l ON al.lane_id = l.id
            JOIN readers r ON al.reader_id = r.id
        """
        
        conditions = []
        if start_date and end_date:
            conditions.append(f"DATE(al.timestamp) BETWEEN '{start_date}' AND '{end_date}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY al.timestamp DESC"
        
        rows = db.execute(query).fetchall()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'Tag ID', 'Access Result', 'Reason', 'User Name', 'Vehicle Number', 'Owner Name', 'Model Name', 'Fuel Type', 'Lane', 'Reader IP'])
        
        # Convert UTC timestamps to IST
        utc_tz = pytz.UTC
        ist_tz = pytz.timezone('Asia/Kolkata')
        
        for row in rows:
            # Convert UTC timestamp to IST
            utc_time = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
            ist_time = utc_time.astimezone(ist_tz)
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create new row with IST timestamp
            new_row = list(row)
            new_row[0] = ist_time_str
            writer.writerow(new_row)
        
        filename = f'access_logs_{datetime.now().strftime("%Y%m%d")}.csv'
    
    elif report_type == 'entry_reports':
        query = """
            SELECT 
                al.timestamp,
                al.tag_id,
                ku.name as user_name,
                COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
                COALESCE(ku.name, tvc.owner_name) as owner_name,
                tvc.model_name,
                tvc.fuel_type,
                ku.contact_number,
                l.lane_name,
                r.reader_ip,
                al.reason
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
            JOIN lanes l ON al.lane_id = l.id
            JOIN readers r ON al.reader_id = r.id
            WHERE al.access_result = 'granted'
        """
        
        conditions = []
        if start_date and end_date:
            conditions.append(f"DATE(al.timestamp) BETWEEN '{start_date}' AND '{end_date}'")
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY al.timestamp DESC"
        
        rows = db.execute(query).fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Entry Time', 'Tag ID', 'User Name', 'Vehicle Number', 'Owner Name', 'Model Name', 'Fuel Type', 'Contact Number', 'Entry Lane', 'Reader IP', 'Notes'])
        
        # Convert UTC timestamps to IST
        utc_tz = pytz.UTC
        ist_tz = pytz.timezone('Asia/Kolkata')
        
        for row in rows:
            # Convert UTC timestamp to IST
            utc_time = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
            ist_time = utc_time.astimezone(ist_tz)
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create new row with IST timestamp
            new_row = list(row)
            new_row[0] = ist_time_str
            writer.writerow(new_row)
        
        filename = f'entry_reports_{datetime.now().strftime("%Y%m%d")}.csv'
    
    elif report_type == 'exit_reports':
        query = """
            SELECT 
                al.timestamp,
                al.tag_id,
                ku.name as user_name,
                COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
                ku.contact_number,
                l.lane_name,
                r.reader_ip,
                al.reason
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
            JOIN lanes l ON al.lane_id = l.id
            JOIN readers r ON al.reader_id = r.id
            WHERE al.access_result = 'granted'
        """
        
        conditions = []
        if start_date and end_date:
            conditions.append(f"DATE(al.timestamp) BETWEEN '{start_date}' AND '{end_date}'")
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY al.timestamp DESC"
        
        rows = db.execute(query).fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Exit Time', 'Tag ID', 'User Name', 'Vehicle Number', 'Contact Number', 'Exit Lane', 'Reader IP', 'Notes'])
        
        # Convert UTC timestamps to IST
        utc_tz = pytz.UTC
        ist_tz = pytz.timezone('Asia/Kolkata')
        
        for row in rows:
            # Convert UTC timestamp to IST
            utc_time = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
            ist_time = utc_time.astimezone(ist_tz)
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create new row with IST timestamp
            new_row = list(row)
            new_row[0] = ist_time_str
            writer.writerow(new_row)
        
        filename = f'exit_reports_{datetime.now().strftime("%Y%m%d")}.csv'
    
    elif report_type == 'vehicle_non_exited':
        # Find vehicles that entered but haven't exited (based on last activity)
        query = """
            SELECT 
                ku.name as user_name,
                COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
                ku.contact_number,
                ku.address,
                al.tag_id,
                MAX(al.timestamp) as last_activity,
                l.lane_name as entry_lane,
                r.reader_ip as entry_reader,
                CASE 
                    WHEN MAX(al.timestamp) >= datetime('now', '-24 hours') THEN 'Recently Active'
                    WHEN MAX(al.timestamp) >= datetime('now', '-7 days') THEN 'Active This Week'
                    ELSE 'Long Term'
                END as status
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
            JOIN lanes l ON al.lane_id = l.id
            JOIN readers r ON al.reader_id = r.id
            WHERE al.access_result = 'granted'
        """
        
        conditions = []
        if start_date and end_date:
            conditions.append(f"DATE(al.timestamp) BETWEEN '{start_date}' AND '{end_date}'")
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += """
            GROUP BY al.tag_id, ku.name, ku.vehicle_number, tvc.vehicle_number, ku.contact_number, ku.address, l.lane_name, r.reader_ip
            HAVING MAX(al.timestamp) = (
                SELECT MAX(timestamp) 
                FROM access_logs al2 
                WHERE al2.tag_id = al.tag_id
            )
            ORDER BY last_activity DESC
        """
        
        rows = db.execute(query).fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['User Name', 'Vehicle Number', 'Contact Number', 'Address', 'Tag ID', 'Last Activity', 'Entry Lane', 'Entry Reader', 'Status'])
        
        # Convert UTC timestamps to IST
        utc_tz = pytz.UTC
        ist_tz = pytz.timezone('Asia/Kolkata')
        
        for row in rows:
            # Convert UTC timestamp to IST (last_activity is at index 5)
            utc_time = datetime.fromisoformat(row[5].replace('Z', '+00:00'))
            ist_time = utc_time.astimezone(ist_tz)
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create new row with IST timestamp
            new_row = list(row)
            new_row[5] = ist_time_str
            writer.writerow(new_row)
        
        filename = f'vehicle_non_exited_{datetime.now().strftime("%Y%m%d")}.csv'
    
    elif report_type == 'vehicle_specific':
        if not vehicle_number:
            return jsonify({'error': 'Vehicle number is required for vehicle-specific reports'}), 400
        
        query = """
            SELECT 
                al.timestamp,
                al.access_result,
                al.reason,
                ku.name as user_name,
                COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
                ku.contact_number,
                l.lane_name,
                r.reader_ip
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
            JOIN lanes l ON al.lane_id = l.id
            JOIN readers r ON al.reader_id = r.id
            WHERE COALESCE(ku.vehicle_number, tvc.vehicle_number) = ?
        """
        
        conditions = []
        if start_date and end_date:
            conditions.append(f"DATE(al.timestamp) BETWEEN '{start_date}' AND '{end_date}'")
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY al.timestamp DESC"
        
        rows = db.execute(query, (vehicle_number,)).fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'Access Result', 'Reason', 'User Name', 'Vehicle Number', 'Contact Number', 'Lane', 'Reader IP'])
        
        # Convert UTC timestamps to IST
        utc_tz = pytz.UTC
        ist_tz = pytz.timezone('Asia/Kolkata')
        
        for row in rows:
            # Convert UTC timestamp to IST
            utc_time = datetime.fromisoformat(row[0].replace('Z', '+00:00'))
            ist_time = utc_time.astimezone(ist_tz)
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create new row with IST timestamp
            new_row = list(row)
            new_row[0] = ist_time_str
            writer.writerow(new_row)
        
        filename = f'vehicle_{vehicle_number}_{datetime.now().strftime("%Y%m%d")}.csv'
    
    elif report_type == 'peak_hours':
        query = """
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as total_events,
                SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as granted,
                SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied
            FROM access_logs 
            WHERE timestamp >= datetime('now', '-30 days')
        """
        
        conditions = []
        if start_date and end_date:
            conditions.append(f"DATE(timestamp) BETWEEN '{start_date}' AND '{end_date}'")
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += """
            GROUP BY strftime('%H', timestamp)
            ORDER BY total_events DESC
        """
        
        rows = db.execute(query).fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Hour', 'Total Events', 'Granted', 'Denied', 'Success Rate (%)'])
        
        for row in rows:
            success_rate = (row[2] / row[1] * 100) if row[1] > 0 else 0
            writer.writerow([f"{row[0]}:00", row[1], row[2], row[3], f"{success_rate:.1f}"])
        
        filename = f'peak_hours_{datetime.now().strftime("%Y%m%d")}.csv'
    
    elif report_type == 'daily_traffic':
        query = """
            SELECT 
                DATE(timestamp) as date,
                strftime('%H', timestamp) as hour,
                COUNT(*) as total_events,
                SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as granted,
                SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied
            FROM access_logs 
        """
        
        conditions = []
        if start_date and end_date:
            conditions.append(f"DATE(timestamp) BETWEEN '{start_date}' AND '{end_date}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
            GROUP BY DATE(timestamp), strftime('%H', timestamp)
            ORDER BY date DESC, hour ASC
        """
        
        rows = db.execute(query).fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Hour', 'Total Events', 'Granted', 'Denied', 'Success Rate (%)'])
        
        for row in rows:
            success_rate = (row[3] / row[2] * 100) if row[2] > 0 else 0
            writer.writerow([row[0], f"{row[1]}:00", row[2], row[3], row[4], f"{success_rate:.1f}"])
        
        filename = f'daily_traffic_{datetime.now().strftime("%Y%m%d")}.csv'
    
    elif report_type == 'weekly_trends':
        query = """
            SELECT 
                strftime('%Y-%W', timestamp) as week,
                COUNT(*) as total_events,
                SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as granted,
                SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied,
                COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM access_logs 
        """
        
        conditions = []
        if start_date and end_date:
            conditions.append(f"DATE(timestamp) BETWEEN '{start_date}' AND '{end_date}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
            GROUP BY strftime('%Y-%W', timestamp)
            ORDER BY week DESC
        """
        
        rows = db.execute(query).fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Week', 'Total Events', 'Granted', 'Denied', 'Active Days', 'Avg Daily Events', 'Success Rate (%)'])
        
        for row in rows:
            avg_daily = row[1] / row[4] if row[4] > 0 else 0
            success_rate = (row[2] / row[1] * 100) if row[1] > 0 else 0
            writer.writerow([row[0], row[1], row[2], row[3], row[4], f"{avg_daily:.1f}", f"{success_rate:.1f}"])
        
        filename = f'weekly_trends_{datetime.now().strftime("%Y%m%d")}.csv'
    
    elif report_type == 'lane_performance':
        query = """
            SELECT 
                l.lane_name,
                COUNT(*) as total_events,
                SUM(CASE WHEN al.access_result = 'granted' THEN 1 ELSE 0 END) as granted,
                SUM(CASE WHEN al.access_result = 'denied' THEN 1 ELSE 0 END) as denied,
                COUNT(DISTINCT al.tag_id) as unique_vehicles,
                MAX(al.timestamp) as last_activity,
                r.reader_ip,
                r.type as reader_type
            FROM access_logs al
            JOIN lanes l ON al.lane_id = l.id
            JOIN readers r ON al.reader_id = r.id
        """
        
        conditions = []
        if start_date and end_date:
            conditions.append(f"DATE(al.timestamp) BETWEEN '{start_date}' AND '{end_date}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
            GROUP BY l.id, l.lane_name, r.reader_ip, r.type
            ORDER BY total_events DESC
        """
        
        rows = db.execute(query).fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Lane Name', 'Total Events', 'Granted', 'Denied', 'Unique Vehicles', 'Success Rate (%)', 'Last Activity', 'Reader IP', 'Reader Type'])
        
        for row in rows:
            success_rate = (row[2] / row[1] * 100) if row[1] > 0 else 0
            writer.writerow([row[0], row[1], row[2], row[3], row[4], f"{success_rate:.1f}", row[5], row[6], row[7]])
        
        filename = f'lane_performance_{datetime.now().strftime("%Y%m%d")}.csv'
    
    elif report_type == 'equipment_health':
        query = """
            SELECT 
                r.id as reader_id,
                r.reader_ip,
                r.type as reader_type,
                l.lane_name,
                COUNT(al.id) as events_last_7d,
                COUNT(CASE WHEN al.timestamp >= datetime('now', '-24 hours') THEN 1 END) as events_last_24h,
                MAX(al.timestamp) as last_activity,
                CASE 
                    WHEN MAX(al.timestamp) >= datetime('now', '-1 hour') THEN 'Online'
                    WHEN MAX(al.timestamp) >= datetime('now', '-24 hours') THEN 'Recent'
                    WHEN MAX(al.timestamp) >= datetime('now', '-7 days') THEN 'Inactive'
                    ELSE 'Offline'
                END as status
            FROM readers r
            JOIN lanes l ON r.lane_id = l.id
            LEFT JOIN access_logs al ON r.id = al.reader_id 
                AND al.timestamp >= datetime('now', '-7 days')
            GROUP BY r.id, r.reader_ip, r.type, l.lane_name
            ORDER BY r.id
        """
        
        rows = db.execute(query).fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Reader ID', 'IP Address', 'Type', 'Lane', 'Events (7 days)', 'Events (24h)', 'Last Activity', 'Status'])
        
        for row in rows:
            writer.writerow(row)
        
        filename = f'equipment_health_{datetime.now().strftime("%Y%m%d")}.csv'
    
    elif report_type == 'denied_access_analysis':
        query = """
            SELECT 
                al.reason,
                COUNT(*) as denied_count,
                COUNT(DISTINCT al.tag_id) as unique_vehicles,
                MAX(al.timestamp) as last_attempt,
                GROUP_CONCAT(DISTINCT COALESCE(ku.vehicle_number, tvc.vehicle_number)) as vehicle_numbers
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
            WHERE al.access_result = 'denied'
        """
        
        conditions = []
        if start_date and end_date:
            conditions.append(f"DATE(al.timestamp) BETWEEN '{start_date}' AND '{end_date}'")
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += """
            GROUP BY al.reason
            ORDER BY denied_count DESC
        """
        
        rows = db.execute(query).fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Reason', 'Denied Count', 'Unique Vehicles', 'Last Attempt', 'Vehicle Numbers'])
        
        for row in rows:
            writer.writerow(row)
        
        filename = f'denied_access_{datetime.now().strftime("%Y%m%d")}.csv'
    
    else:
        return jsonify({'error': 'Invalid report type'}), 400
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    ) 

@analytics_bp.route('/barrier-events')
def barrier_events():
    """Barrier Events Analytics Page"""
    return render_template('analytics/barrier_events.html')

@analytics_bp.route('/api/barrier-events')
def api_barrier_events():
    """API endpoint for barrier events with filtering"""
    db = get_db()
    # Get filters from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    relay_number = request.args.get('relay_number')
    user = request.args.get('user')
    action = request.args.get('action')
    lane_id = request.args.get('lane_id')
    query = "SELECT * FROM barrier_events WHERE 1=1"
    params = []
    if start_date:
        query += " AND DATE(timestamp) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(timestamp) <= ?"
        params.append(end_date)
    if relay_number:
        query += " AND relay_number = ?"
        params.append(relay_number)
    if user:
        query += " AND user = ?"
        params.append(user)
    if action:
        query += " AND action = ?"
        params.append(action)
    if lane_id:
        query += " AND lane_id = ?"
        params.append(lane_id)
    query += " ORDER BY timestamp DESC LIMIT 1000"
    rows = db.execute(query, params).fetchall()
    # Convert to dicts
    data = [dict(row) for row in rows]
    return jsonify(data)

@analytics_bp.route('/api/export-barrier-events')
def export_barrier_events():
    """Export filtered barrier events as CSV"""
    import csv
    from io import StringIO
    db = get_db()
    # Same filters as above
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    relay_number = request.args.get('relay_number')
    user = request.args.get('user')
    action = request.args.get('action')
    lane_id = request.args.get('lane_id')
    query = "SELECT * FROM barrier_events WHERE 1=1"
    params = []
    if start_date:
        query += " AND DATE(timestamp) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(timestamp) <= ?"
        params.append(end_date)
    if relay_number:
        query += " AND relay_number = ?"
        params.append(relay_number)
    if user:
        query += " AND user = ?"
        params.append(user)
    if action:
        query += " AND action = ?"
        params.append(action)
    if lane_id:
        query += " AND lane_id = ?"
        params.append(lane_id)
    query += " ORDER BY timestamp DESC"
    rows = db.execute(query, params).fetchall()
    output = StringIO()
    writer = csv.writer(output)
    # Write header
    if rows:
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow(row)
    else:
        writer.writerow(["No data"])
    from flask import Response
    filename = f'barrier_events_export.csv'
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    ) 

@analytics_bp.route('/api/barrier-log', methods=['GET'])
def api_barrier_log():
    """
    Returns barrier events as JSON for external devices/browsers.
    Query params: start_date, end_date
    """
    db = get_db()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query = "SELECT * FROM barrier_events WHERE 1=1"
    params = []
    if start_date:
        query += " AND DATE(timestamp) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(timestamp) <= ?"
        params.append(end_date)
    query += " ORDER BY timestamp DESC LIMIT 1000"
    rows = db.execute(query, params).fetchall()
    data = [dict(row) for row in rows]
    return jsonify({"success": True, "count": len(data), "events": data}) 

@analytics_bp.route('/viewonmobile_access_logs', methods=['GET'])
def viewonmobile_access_logs():
    db = get_db()
    # Query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    offset = (page - 1) * per_page

    # Build query
    query = '''
        SELECT 
            al.timestamp as access_time,
            ku.name as user_name,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            tvc.fuel_type,
            al.tag_id,
            l.lane_name,
            r.reader_ip as device,
            al.access_result as status
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        JOIN readers r ON al.reader_id = r.id
        WHERE 1=1
    '''
    params = []
    if start_date:
        query += ' AND DATE(al.timestamp) >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND DATE(al.timestamp) <= ?'
        params.append(end_date)
    if status:
        query += ' AND al.access_result = ?'
        params.append(status)
    query += ' ORDER BY al.timestamp DESC LIMIT ? OFFSET ?'
    params += [per_page, offset]

    rows = db.execute(query, params).fetchall()

    # Get total count for pagination
    count_query = '''
        SELECT COUNT(*) FROM access_logs al 
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        JOIN readers r ON al.reader_id = r.id
        WHERE 1=1
    '''
    count_params = []
    if start_date:
        count_query += ' AND DATE(al.timestamp) >= ?'
        count_params.append(start_date)
    if end_date:
        count_query += ' AND DATE(al.timestamp) <= ?'
        count_params.append(end_date)
    if status:
        count_query += ' AND al.access_result = ?'
        count_params.append(status)
    total_count = db.execute(count_query, count_params).fetchone()[0]

    logs = []
    # Create timezone objects
    ist_tz = pytz.timezone('Asia/Kolkata')
    
    for row in rows:
        # Parse the UTC timestamp and convert to IST
        # The timestamp from database is in UTC format like "2025-07-13T05:03:01Z"
        timestamp_str = row[0]
        
        # Handle different timestamp formats
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            # ISO format with Z (UTC)
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            # ISO format without Z, assume UTC
            utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            # SQLite datetime format, assume UTC
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
        
        # Convert to IST (UTC + 5:30)
        ist_time = utc_time.astimezone(ist_tz)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        
        logs.append({
            "access_time": ist_time_str,
            "user": {
                "name": row[1],
                "vehicle_number": row[2],
                "owner_name": row[3],
                "model_name": row[4],
                "fuel_type": row[5]
            },
            "tag_id": row[6],
            "lane": row[7],
            "device": row[8],
            "status": row[9]
        })

    return jsonify({
        "status": "success",
        "total_count": total_count,
        "logs": logs
    }) 

# --- MOBILE ANALYTICS API ENDPOINTS ---
@analytics_bp.route('/api/mobile/analytics/summary')
def mobile_analytics_summary():
    """Summary: entries, exits, denied, inside, overstayed"""
    db = get_db()
    today = datetime.now().date()
    # Entries, exits, denied today
    stats = db.execute('''
        SELECT 
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as entries,
            SUM(CASE WHEN access_result = 'exit' THEN 1 ELSE 0 END) as exits,
            SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied
        FROM access_logs WHERE DATE(timestamp) = DATE('now')
    ''').fetchone()
    entries, exits, denied = stats if stats else (0, 0, 0)
    # Vehicles currently inside
    inside = db.execute('''
        SELECT COUNT(DISTINCT tag_id) FROM access_logs al1
        WHERE al1.access_result = 'granted'
        AND al1.timestamp = (
            SELECT MAX(al2.timestamp) FROM access_logs al2 WHERE al2.tag_id = al1.tag_id
        )
    ''').fetchone()[0]
    # Overstayed (inside > 8h)
    overstayed = db.execute('''
        SELECT COUNT(*) FROM (
            SELECT tag_id, MAX(timestamp) as last_entry
            FROM access_logs WHERE access_result = 'granted'
            GROUP BY tag_id
            HAVING last_entry <= datetime('now', '-8 hours')
        )
    ''').fetchone()[0]
    return jsonify({
        'date': str(today),
        'entries': entries,
        'exits': exits,
        'denied': denied,
        'currently_inside': inside,
        'overstayed': overstayed
    })

@analytics_bp.route('/api/mobile/analytics/lanes')
def mobile_analytics_lanes():
    """Lane-wise stats: entries, exits, denied today"""
    db = get_db()
    rows = db.execute('''
        SELECT l.lane_name, 
            SUM(CASE WHEN al.access_result = 'granted' THEN 1 ELSE 0 END) as entries,
            SUM(CASE WHEN al.access_result = 'exit' THEN 1 ELSE 0 END) as exits,
            SUM(CASE WHEN al.access_result = 'denied' THEN 1 ELSE 0 END) as denied
        FROM access_logs al
        JOIN lanes l ON al.lane_id = l.id
        WHERE DATE(al.timestamp) = DATE('now')
        GROUP BY l.lane_name
    ''').fetchall()
    lanes = [dict(lane_name=row[0], entries=row[1], exits=row[2], denied=row[3]) for row in rows]
    return jsonify({'lanes': lanes})

@analytics_bp.route('/api/mobile/analytics/peak')
def mobile_analytics_peak():
    """Peak entry/exit hour, busiest/most denied lane today"""
    db = get_db()
    # Peak entry/exit hour
    peak = db.execute('''
        SELECT strftime('%H', timestamp) as hour,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as entries,
            SUM(CASE WHEN access_result = 'exit' THEN 1 ELSE 0 END) as exits
        FROM access_logs WHERE DATE(timestamp) = DATE('now')
        GROUP BY hour ORDER BY entries DESC LIMIT 1
    ''').fetchone()
    peak_entry_hour = int(peak[0]) if peak else None
    peak_exit = db.execute('''
        SELECT strftime('%H', timestamp) as hour,
            SUM(CASE WHEN access_result = 'exit' THEN 1 ELSE 0 END) as exits
        FROM access_logs WHERE DATE(timestamp) = DATE('now')
        GROUP BY hour ORDER BY exits DESC LIMIT 1
    ''').fetchone()
    peak_exit_hour = int(peak_exit[0]) if peak_exit else None
    # Busiest lane
    busiest = db.execute('''
        SELECT l.lane_name, COUNT(*) as cnt FROM access_logs al
        JOIN lanes l ON al.lane_id = l.id
        WHERE DATE(al.timestamp) = DATE('now')
        GROUP BY l.lane_name ORDER BY cnt DESC LIMIT 1
    ''').fetchone()
    busiest_lane = busiest[0] if busiest else None
    # Most denied lane
    denied = db.execute('''
        SELECT l.lane_name, COUNT(*) as cnt FROM access_logs al
        JOIN lanes l ON al.lane_id = l.id
        WHERE DATE(al.timestamp) = DATE('now') AND al.access_result = 'denied'
        GROUP BY l.lane_name ORDER BY cnt DESC LIMIT 1
    ''').fetchone()
    most_denied_lane = denied[0] if denied else None
    return jsonify({
        'peak_entry_hour': peak_entry_hour,
        'peak_exit_hour': peak_exit_hour,
        'busiest_lane': busiest_lane,
        'most_denied_lane': most_denied_lane
    })

@analytics_bp.route('/api/mobile/analytics/top-tags')
def mobile_analytics_top_tags():
    """Top 5 frequent and denied tags today with vehicle details"""
    db = get_db()
    top_frequent = db.execute('''
        SELECT 
            al.tag_id, 
            COUNT(*) as cnt,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            tvc.fuel_type
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        WHERE DATE(al.timestamp) = DATE('now') AND al.access_result = 'granted'
        GROUP BY al.tag_id, ku.vehicle_number, tvc.vehicle_number, ku.name, tvc.owner_name, tvc.model_name, tvc.fuel_type
        ORDER BY cnt DESC LIMIT 5
    ''').fetchall()
    top_denied = db.execute('''
        SELECT 
            al.tag_id, 
            COUNT(*) as cnt,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            tvc.fuel_type
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        WHERE DATE(al.timestamp) = DATE('now') AND al.access_result = 'denied'
        GROUP BY al.tag_id, ku.vehicle_number, tvc.vehicle_number, ku.name, tvc.owner_name, tvc.model_name, tvc.fuel_type
        ORDER BY cnt DESC LIMIT 5
    ''').fetchall()
    return jsonify({
        'top_frequent_visitors': [{
            'tag_id': row[0], 
            'count': row[1], 
            'vehicle_number': row[2] or 'Unknown',
            'owner_name': row[3] or 'Unknown',
            'model_name': row[4] or 'Unknown',
            'fuel_type': row[5] or 'Unknown'
        } for row in top_frequent],
        'top_denied_tags': [{
            'tag_id': row[0], 
            'count': row[1], 
            'vehicle_number': row[2] or 'Unknown',
            'owner_name': row[3] or 'Unknown',
            'model_name': row[4] or 'Unknown',
            'fuel_type': row[5] or 'Unknown'
        } for row in top_denied]
    })

@analytics_bp.route('/api/mobile/analytics/durations')
def mobile_analytics_durations():
    """Average, shortest, longest parking duration today (in minutes)"""
    db = get_db()
    # For each tag, get entry and exit times
    rows = db.execute('''
        SELECT tag_id, 
            MIN(CASE WHEN access_result = 'granted' THEN timestamp END) as entry_time,
            MAX(CASE WHEN access_result = 'exit' THEN timestamp END) as exit_time
        FROM access_logs WHERE DATE(timestamp) = DATE('now')
        GROUP BY tag_id
        HAVING entry_time IS NOT NULL AND exit_time IS NOT NULL
    ''').fetchall()
    durations = []
    for row in rows:
        entry = datetime.fromisoformat(row[1]) if row[1] else None
        exit = datetime.fromisoformat(row[2]) if row[2] else None
        if entry and exit:
            durations.append((exit - entry).total_seconds() / 60)
    avg_dur = int(sum(durations)/len(durations)) if durations else 0
    min_dur = int(min(durations)) if durations else 0
    max_dur = int(max(durations)) if durations else 0
    return jsonify({
        'average_duration_minutes': avg_dur,
        'shortest_duration_minutes': min_dur,
        'longest_duration_minutes': max_dur
    })

@analytics_bp.route('/api/mobile/analytics/vehicle-history')
def mobile_analytics_vehicle_history():
    """All logs for a specific tag (today)"""
    tag_id = request.args.get('tag_id')
    if not tag_id:
        return jsonify({'error': 'tag_id required'}), 400
    db = get_db()
    rows = db.execute('''
        SELECT timestamp, lane_id, access_result, reason FROM access_logs
        WHERE tag_id = ? AND DATE(timestamp) = DATE('now')
        ORDER BY timestamp DESC
    ''', (tag_id,)).fetchall()
    
    # Create timezone objects
    ist_tz = pytz.timezone('Asia/Kolkata')
    
    logs = []
    for row in rows:
        # Parse the UTC timestamp and convert to IST
        timestamp_str = row[0]
        
        # Handle different timestamp formats
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            # ISO format with Z (UTC)
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            # ISO format without Z, assume UTC
            utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            # SQLite datetime format, assume UTC
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
        
        # Convert to IST (UTC + 5:30)
        ist_time = utc_time.astimezone(ist_tz)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        
        logs.append(dict(timestamp=ist_time_str, lane_id=row[1], event=row[2], reason=row[3]))
    
    return jsonify({'tag_id': tag_id, 'logs': logs})

@analytics_bp.route('/api/mobile/analytics/trends')
def mobile_analytics_trends():
    """Daily entry/exit/denied counts for last 7 days"""
    db = get_db()
    rows = db.execute('''
        SELECT DATE(timestamp) as date,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as entries,
            SUM(CASE WHEN access_result = 'exit' THEN 1 ELSE 0 END) as exits,
            SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied
        FROM access_logs
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    ''').fetchall()
    trends = [dict(date=row[0], entries=row[1], exits=row[2], denied=row[3]) for row in rows]
    return jsonify({'trends': trends})

@analytics_bp.route('/api/mobile/analytics/heatmap')
def mobile_analytics_heatmap():
    """Hourly entry/exit counts for today"""
    db = get_db()
    rows = db.execute('''
        SELECT strftime('%H', timestamp) as hour,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as entries,
            SUM(CASE WHEN access_result = 'exit' THEN 1 ELSE 0 END) as exits
        FROM access_logs WHERE DATE(timestamp) = DATE('now')
        GROUP BY hour ORDER BY hour
    ''').fetchall()
    hours = [dict(hour=int(row[0]), entries=row[1], exits=row[2]) for row in rows]
    return jsonify({'hours': hours})

@analytics_bp.route('/api/mobile/analytics/denied-reasons')
def mobile_analytics_denied_reasons():
    """Denied counts by reason today"""
    db = get_db()
    rows = db.execute('''
        SELECT reason, COUNT(*) as count FROM access_logs
        WHERE access_result = 'denied' AND DATE(timestamp) = DATE('now')
        GROUP BY reason ORDER BY count DESC
    ''').fetchall()
    reasons = [dict(reason=row[0], count=row[1]) for row in rows]
    return jsonify({'reasons': reasons})

@analytics_bp.route('/api/mobile/analytics/denied-logs')
def mobile_analytics_denied_logs():
    """Detailed denied logs with vehicle numbers (today)"""
    db = get_db()
    rows = db.execute('''
        SELECT 
            al.timestamp,
            al.tag_id,
            al.reason,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            ku.name as user_name,
            l.lane_name,
            r.reader_ip
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        JOIN readers r ON al.reader_id = r.id
        WHERE al.access_result = 'denied' 
        AND DATE(al.timestamp) = DATE('now')
        ORDER BY al.timestamp DESC
    ''').fetchall()
    
    denied_logs = []
    # Create timezone objects
    ist_tz = pytz.timezone('Asia/Kolkata')
    
    for row in rows:
        # Parse the UTC timestamp and convert to IST
        timestamp_str = row[0]
        
        # Handle different timestamp formats
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            # ISO format with Z (UTC)
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            # ISO format without Z, assume UTC
            utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            # SQLite datetime format, assume UTC
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
        
        # Convert to IST (UTC + 5:30)
        ist_time = utc_time.astimezone(ist_tz)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        
        denied_logs.append({
            'timestamp': ist_time_str,
            'tag_id': row[1],
            'reason': row[2],
            'vehicle_number': row[3] or 'Unknown',
            'user_name': row[4] or 'Unknown',
            'lane_name': row[5],
            'reader_ip': row[6]
        })
    
    return jsonify({
        'date': datetime.now().date().isoformat(),
        'total_denied': len(denied_logs),
        'denied_logs': denied_logs
    }) 

@analytics_bp.route('/api/total-events-today-details')
def total_events_today_details():
    try:
        db = get_db()
        rows = db.execute("""
            SELECT 
                al.timestamp,
                al.tag_id,
                al.access_result,
                al.reason,
                ku.name as user_name,
                COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
                COALESCE(ku.name, tvc.owner_name) as owner_name,
                tvc.model_name,
                tvc.fuel_type,
                l.lane_name,
                r.reader_ip,
                r.type as reader_type
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
            JOIN lanes l ON al.lane_id = l.id
            JOIN readers r ON al.reader_id = r.id
            WHERE DATE(al.timestamp) = DATE('now')
            ORDER BY al.timestamp ASC
        """).fetchall()
        ist_tz = pytz.timezone('Asia/Kolkata')
        hour_stats = {}
        reader_stats = {}
        tag_type_counts = {'fastag': 0, 'car_oem': 0, 'other': 0}
        unique_tags = set()
        detailed_entries = []
        # Reader stats with bifurcation for unique tags
        reader_stats_bifurc = {}
        tag_seen_per_reader = {}
        for row in rows:
            timestamp_str = row[0]
            if 'T' in timestamp_str and 'Z' in timestamp_str:
                utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif 'T' in timestamp_str:
                utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
            else:
                utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                utc_time = utc_time.replace(tzinfo=pytz.UTC)
            ist_time = utc_time.astimezone(ist_tz)
            hour = ist_time.strftime('%H')
            ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
            tag_id = row[1]
            access_result = row[2]
            reader_type = row[11]
            reader_name = f"{row[10]} ({row[9]})"
            if tag_id.startswith('34161'):
                tag_type = 'FASTag'
                tag_type_counts['fastag'] += 1
            elif tag_id.startswith('E20'):
                tag_type = 'CAR OEM'
                tag_type_counts['car_oem'] += 1
            else:
                tag_type = 'Other'
                tag_type_counts['other'] += 1
            unique_tags.add(tag_id)
            # Hourly stats
            if hour not in hour_stats:
                hour_stats[hour] = {
                    'total': 0, 'granted': 0, 'denied': 0,
                    'fastag': 0, 'car_oem': 0, 'other': 0
                }
            hour_stats[hour]['total'] += 1
            if access_result == 'granted':
                hour_stats[hour]['granted'] += 1
            else:
                hour_stats[hour]['denied'] += 1
            if tag_type == 'FASTag':
                hour_stats[hour]['fastag'] += 1
            elif tag_type == 'CAR OEM':
                hour_stats[hour]['car_oem'] += 1
            else:
                hour_stats[hour]['other'] += 1
            # Reader stats bifurcation (unique tags per reader)
            if reader_name not in reader_stats_bifurc:
                reader_stats_bifurc[reader_name] = {'type': reader_type, 'tags': set(), 'fastag': set(), 'car_oem': set(), 'other': set()}
            if tag_id not in reader_stats_bifurc[reader_name]['tags']:
                reader_stats_bifurc[reader_name]['tags'].add(tag_id)
                if tag_type == 'FASTag':
                    reader_stats_bifurc[reader_name]['fastag'].add(tag_id)
                elif tag_type == 'CAR OEM':
                    reader_stats_bifurc[reader_name]['car_oem'].add(tag_id)
                else:
                    reader_stats_bifurc[reader_name]['other'].add(tag_id)
            # For detailed entries
            detailed_entries.append({
                'tag_id': tag_id,
                'tag_type': tag_type,
                'vehicle_number': row[5],
                'owner_name': row[6],
                'model_name': row[7],
                'fuel_type': row[8],
                'timestamp': ist_time_str,
                'reason': row[3],
                'lane_name': row[9],
                'reader_name': reader_name,
                'access_result': access_result
            })
        peak_hour = max(hour_stats.items(), key=lambda x: x[1]['total'])[0] if hour_stats else None
        top_reader = max(reader_stats_bifurc.items(), key=lambda x: len(x[1]['tags']))[0] if reader_stats_bifurc else None
        hour_wise = []
        for h in sorted(hour_stats.keys()):
            hour_wise.append({
                'hour': h,
                **hour_stats[h]
            })
        # Convert reader stats to list with bifurcation counts
        reader_stats_list = []
        for name, stat in sorted(reader_stats_bifurc.items(), key=lambda x: len(x[1]['tags']), reverse=True):
            reader_stats_list.append({
                'reader_name': name,
                'type': stat['type'],
                'total': len(stat['tags']),
                'fastag': len(stat['fastag']),
                'car_oem': len(stat['car_oem']),
                'other': len(stat['other'])
            })
        return jsonify({
            'summary': {
                'fastag_count': tag_type_counts['fastag'],
                'car_oem_count': tag_type_counts['car_oem'],
                'other_count': tag_type_counts['other'],
                'unique_tags': len(unique_tags),
                'peak_hour': peak_hour,
                'top_reader': top_reader
            },
            'hour_wise': hour_wise,
            'reader_stats': reader_stats_list,
            'entries': detailed_entries
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/denied-fastag-activity-feed')
def denied_fastag_activity_feed():
    """Return a feed of denied FASTag events (last 24h) for activity feed display."""
    try:
        db = get_db()
        denied_rows = db.execute('''
            SELECT 
                al.tag_id,
                COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
                COALESCE(ku.name, tvc.owner_name) as owner_name,
                tvc.model_name,
                tvc.fuel_type,
                al.timestamp,
                al.reason
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
            WHERE al.access_result = 'denied'
                AND al.timestamp >= datetime('now', '-24 hours')
            ORDER BY al.timestamp DESC
            LIMIT 50
        ''').fetchall()
        
        result = []
        for row in denied_rows:
            result.append({
                'tag_id': row[0] or 'Unknown',
                'vehicle_number': row[1] or 'Unknown',
                'owner_name': row[2] or 'Unknown',
                'model_name': row[3] or 'Unknown',
                'fuel_type': row[4] or '',
                'timestamp': row[5] or '',
                'reason': row[6] or 'No reason specified',
            })
        
        # Convert timestamps to IST
        import pytz
        from datetime import datetime
        ist_tz = pytz.timezone('Asia/Kolkata')
        for entry in result:
            timestamp_str = entry['timestamp']
            if timestamp_str:
                try:
                    if 'T' in timestamp_str and 'Z' in timestamp_str:
                        utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    elif 'T' in timestamp_str:
                        utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
                    else:
                        utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        utc_time = utc_time.replace(tzinfo=pytz.UTC)
                    ist_time = utc_time.astimezone(ist_tz)
                    entry['timestamp'] = ist_time.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    entry['timestamp'] = timestamp_str
        
        return jsonify({'results': result, 'count': len(result)})
    except Exception as e:
        return jsonify({'error': str(e), 'results': [], 'count': 0}), 500

@analytics_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@analytics_bp.route('/api/lane-utilization')
def lane_utilization_api():
    db = get_db()
    lane_utilization = [list(row) for row in db.execute("""
        SELECT 
            l.lane_name,
            COUNT(*) as total_events,
            SUM(CASE WHEN al.access_result = 'granted' THEN 1 ELSE 0 END) as granted,
            SUM(CASE WHEN al.access_result = 'denied' THEN 1 ELSE 0 END) as denied
        FROM access_logs al
        JOIN lanes l ON al.lane_id = l.id
        WHERE al.timestamp >= datetime('now', '-7 days')
        GROUP BY l.id, l.lane_name
        ORDER BY total_events DESC
    """).fetchall()]
    return jsonify({'lane_utilization': lane_utilization})

@analytics_bp.route('/api/top-users')
def top_users_api():
    db = get_db()
    top_users = [list(row) for row in db.execute("""
        SELECT 
            al.tag_id,
            ku.name as user_name,
            ku.vehicle_number as kyc_vehicle_number,
            tvc.vehicle_number as cache_vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            tvc.fuel_type,
            COUNT(*) as total_events,
            SUM(CASE WHEN al.access_result = 'granted' THEN 1 ELSE 0 END) as granted,
            SUM(CASE WHEN al.access_result = 'denied' THEN 1 ELSE 0 END) as denied,
            MAX(al.timestamp) as last_activity
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        WHERE al.timestamp >= datetime('now', '-24 hours')
        GROUP BY al.tag_id, ku.name, ku.vehicle_number, tvc.vehicle_number, tvc.owner_name, tvc.model_name, tvc.fuel_type
        ORDER BY total_events DESC
        LIMIT 10
    """).fetchall()]
    return jsonify({'top_users': top_users})

@analytics_bp.route('/api/denied-analysis')
def denied_analysis_api():
    db = get_db()
    denied_analysis = [list(row) for row in db.execute("""
        SELECT 
            al.reason,
            COUNT(*) as count,
            COUNT(DISTINCT al.tag_id) as unique_tags,
            GROUP_CONCAT(DISTINCT COALESCE(ku.vehicle_number, tvc.vehicle_number)) as vehicle_numbers
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        WHERE al.access_result = 'denied' 
        AND al.timestamp >= datetime('now', '-7 days')
        GROUP BY al.reason
        ORDER BY count DESC
    """).fetchall()]
    return jsonify({'denied_analysis': denied_analysis})

@analytics_bp.route('/api/current-occupancy')
def api_current_occupancy():
    db = get_db()
    # Fast version: only consider last 24 hours
    current_occupancy_rows = db.execute("""
        SELECT tag_id, MAX(timestamp) as last_grant
        FROM access_logs
        WHERE access_result = 'granted' AND timestamp >= datetime('now', '-24 hours')
        GROUP BY tag_id
    """).fetchall()
    occ_fastag = 0
    occ_car_oem = 0
    occ_other = 0
    for row in current_occupancy_rows:
        tag_id = row[0]
        if tag_id.startswith('34161'):
            occ_fastag += 1
        elif tag_id.startswith('E20'):
            occ_car_oem += 1
        else:
            occ_other += 1
    return jsonify({
        'fastag': occ_fastag,
        'car_oem': occ_car_oem,
        'other': occ_other,
        'total': len(current_occupancy_rows)
    })

@analytics_bp.route('/api/today-granted')
def api_today_granted():
    db = get_db()
    row = db.execute("""
        SELECT SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as granted
        FROM access_logs WHERE DATE(timestamp) = DATE('now')
    """).fetchone()
    return jsonify({'granted': row[0] or 0})

@analytics_bp.route('/api/unique-tags-denied-today')
def api_unique_tags_denied_today():
    db = get_db()
    denied_tags_rows = db.execute('''
        SELECT tag_id FROM access_logs WHERE DATE(timestamp) = DATE('now') AND access_result = 'denied'
    ''').fetchall()
    denied_tags_set = set()
    denied_fastag_count = 0
    denied_car_oem_count = 0
    denied_other_count = 0
    for row in denied_tags_rows:
        tag_id = row[0]
        if tag_id not in denied_tags_set:
            denied_tags_set.add(tag_id)
            if tag_id.startswith('34161'):
                denied_fastag_count += 1
            elif tag_id.startswith('E20'):
                denied_car_oem_count += 1
            else:
                denied_other_count += 1
    return jsonify({
        'fastag': denied_fastag_count,
        'car_oem': denied_car_oem_count,
        'other': denied_other_count,
        'total': len(denied_tags_set)
    })

@analytics_bp.route('/api/unique-tags-today')
def api_unique_tags_today():
    db = get_db()
    unique_tags_rows = db.execute('''
        SELECT tag_id FROM access_logs WHERE DATE(timestamp) = DATE('now')
    ''').fetchall()
    unique_tags_set = set()
    fastag_count = 0
    car_oem_count = 0
    other_count = 0
    for row in unique_tags_rows:
        tag_id = row[0]
        if tag_id not in unique_tags_set:
            unique_tags_set.add(tag_id)
            if tag_id.startswith('34161'):
                fastag_count += 1
            elif tag_id.startswith('E20'):
                car_oem_count += 1
            else:
                other_count += 1
    return jsonify({
        'fastag': fastag_count,
        'car_oem': car_oem_count,
        'other': other_count,
        'total': len(unique_tags_set)
    })

@analytics_bp.route('/api/overstayed-vehicles')
def api_overstayed_vehicles():
    db = get_db()
    overstayed = db.execute('''
        SELECT COUNT(*) FROM (
            SELECT tag_id, MAX(timestamp) as last_entry
            FROM access_logs WHERE access_result = 'granted'
            GROUP BY tag_id
            HAVING last_entry <= datetime('now', '-8 hours')
        )
    ''').fetchone()[0]
    return jsonify({'overstayed': overstayed})

@analytics_bp.route('/api/unique-vehicles-today')
def api_unique_vehicles_today():
    db = get_db()
    unique_vehicles_today = db.execute('''
        SELECT COUNT(DISTINCT tag_id) FROM access_logs WHERE DATE(timestamp) = DATE('now')
    ''').fetchone()[0]
    return jsonify({'unique_vehicles_today': unique_vehicles_today})

@analytics_bp.route('/api/fastag-vs-nonfastag')
def api_fastag_vs_nonfastag():
    db = get_db()
    row = db.execute('''
        SELECT
            COUNT(DISTINCT CASE WHEN tag_id LIKE '34161%' THEN tag_id END) as fastag_count,
            COUNT(DISTINCT CASE WHEN tag_id NOT LIKE '34161%' THEN tag_id END) as nonfastag_count
        FROM access_logs
        WHERE DATE(timestamp) = DATE('now')
    ''').fetchone()
    return jsonify({'fastag': row[0] or 0, 'nonfastag': row[1] or 0})

@analytics_bp.route('/api/entry-exit-trend')
def api_entry_exit_trend():
    db = get_db()
    rows = db.execute('''
        SELECT strftime('%H', timestamp) as hour,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as entries,
            SUM(CASE WHEN access_result = 'exit' THEN 1 ELSE 0 END) as exits
        FROM access_logs
        WHERE DATE(timestamp) = DATE('now')
        GROUP BY hour
        ORDER BY hour
    ''').fetchall()
    return jsonify({'entry_exit_trend': [list(row) for row in rows]})

@analytics_bp.route('/api/hourly-activity')
def api_hourly_activity():
    db = get_db()
    rows = db.execute('''
        SELECT 
            strftime('%H', timestamp) as hour,
            COUNT(*) as total,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as granted,
            SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied
        FROM access_logs 
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY strftime('%H', timestamp)
        ORDER BY hour
    ''').fetchall()
    return jsonify({'hourly_data': [list(row) for row in rows]})

@analytics_bp.route('/api/reader-health')
def api_reader_health():
    db = get_db()
    rows = db.execute('''
        SELECT 
            r.id as reader_id,
            r.reader_ip,
            r.type,
            l.lane_name,
            COUNT(al.id) as events_last_24h,
            MAX(al.timestamp) as last_activity
        FROM readers r
        JOIN lanes l ON r.lane_id = l.id
        LEFT JOIN access_logs al ON r.id = al.reader_id 
            AND al.timestamp >= datetime('now', '-24 hours')
        GROUP BY r.id, r.reader_ip, r.type, l.lane_name
        ORDER BY r.id
    ''').fetchall()
    return jsonify({'reader_health': [list(row) for row in rows]})

@analytics_bp.route('/api/recent-activity')
def api_recent_activity():
    db = get_db()
    rows = db.execute("""
        SELECT 
            al.timestamp,
            al.tag_id,
            al.access_result,
            al.reason,
            ku.name as user_name,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            tvc.fuel_type,
            l.lane_name,
            r.reader_ip,
            r.type as reader_type,
            ku.vehicle_number as kyc_vehicle_number
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        JOIN readers r ON al.reader_id = r.id
        WHERE al.timestamp >= datetime('now', '-24 hours')
        ORDER BY al.timestamp DESC
        LIMIT 50
    """).fetchall()
    # Convert timestamps to IST
    import pytz
    from datetime import datetime
    ist_tz = pytz.timezone('Asia/Kolkata')
    results = []
    for row in rows:
        timestamp_str = row[0]
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
        ist_time = utc_time.astimezone(ist_tz)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        results.append([ist_time_str] + list(row[1:]))
    return jsonify({'recent_activity': results})

@analytics_bp.route('/api/top-granted-tags')
def api_top_granted_tags():
    db = get_db()
    rows = db.execute('''
        SELECT 
            al.tag_id,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            COUNT(*) as granted_count
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        WHERE al.access_result = 'granted' AND DATE(al.timestamp) = DATE('now')
        GROUP BY al.tag_id, ku.vehicle_number, tvc.vehicle_number, ku.name, tvc.owner_name, tvc.model_name
        ORDER BY granted_count DESC
        LIMIT 10
    ''').fetchall()
    result = [
        {
            'tag_id': row[0],
            'vehicle_number': row[1] or '',
            'owner_name': row[2] or '',
            'model_name': row[3] or '',
            'granted_count': row[4]
        }
        for row in rows
    ]
    return jsonify({'top_granted_tags': result})

@analytics_bp.route('/api/recent-granted-tags')
def api_recent_granted_tags():
    db = get_db()
    rows = db.execute('''
        SELECT 
            al.timestamp,
            al.tag_id,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            l.lane_name
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        WHERE al.access_result = 'granted' AND DATE(al.timestamp) = DATE('now')
        ORDER BY al.timestamp DESC
        LIMIT 100
    ''').fetchall()
    # Convert timestamps to IST
    import pytz
    from datetime import datetime
    ist_tz = pytz.timezone('Asia/Kolkata')
    result = []
    for row in rows:
        timestamp_str = row[0]
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
        ist_time = utc_time.astimezone(ist_tz)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        result.append({
            'time': ist_time_str,
            'tag_id': row[1],
            'vehicle_number': row[2] or '',
            'owner_name': row[3] or '',
            'model_name': row[4] or '',
            'lane_name': row[5] or ''
        })
    return jsonify({'recent_granted_tags': result})

@analytics_bp.route('/api/most-denied-tags')
def api_most_denied_tags():
    db = get_db()
    rows = db.execute('''
        SELECT 
            al.tag_id,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            l.lane_name,
            MAX(al.timestamp) as last_denied,
            COUNT(*) as denied_count
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        WHERE al.access_result = 'denied' AND DATE(al.timestamp) = DATE('now')
        GROUP BY al.tag_id, ku.vehicle_number, tvc.vehicle_number, ku.name, tvc.owner_name, tvc.model_name, l.lane_name
        ORDER BY denied_count DESC, last_denied DESC
        LIMIT 10
    ''').fetchall()
    # Convert timestamps to IST
    import pytz
    from datetime import datetime
    ist_tz = pytz.timezone('Asia/Kolkata')
    result = []
    for row in rows:
        timestamp_str = row[5]
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
        ist_time = utc_time.astimezone(ist_tz)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        result.append({
            'tag_id': row[0],
            'vehicle_number': row[1] or '',
            'owner_name': row[2] or '',
            'model_name': row[3] or '',
            'lane_name': row[4] or '',
            'time': ist_time_str,
            'denied_count': row[6]
        })
    return jsonify({'most_denied_tags': result})

@analytics_bp.route('/api/recent-entries')
def api_recent_entries():
    db = get_db()
    rows = db.execute('''
        SELECT 
            al.timestamp,
            al.tag_id,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            l.lane_name
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        WHERE al.access_result = 'granted' 
            AND DATE(al.timestamp) = DATE('now')
            AND (l.lane_type = 'entry' OR l.lane_name LIKE '%entry%' OR l.lane_name LIKE '%Entry%')
        ORDER BY al.timestamp DESC
        LIMIT 100
    ''').fetchall()
    # Convert timestamps to IST
    import pytz
    from datetime import datetime
    ist_tz = pytz.timezone('Asia/Kolkata')
    result = []
    for row in rows:
        timestamp_str = row[0]
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
        ist_time = utc_time.astimezone(ist_tz)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        result.append({
            'time': ist_time_str,
            'tag_id': row[1],
            'vehicle_number': row[2] or '',
            'owner_name': row[3] or '',
            'model_name': row[4] or '',
            'lane_name': row[5] or ''
        })
    return jsonify({'recent_entries': result})

@analytics_bp.route('/api/recent-exits')
def api_recent_exits():
    db = get_db()
    rows = db.execute('''
        SELECT 
            al.timestamp,
            al.tag_id,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
            COALESCE(ku.name, tvc.owner_name) as owner_name,
            tvc.model_name,
            l.lane_name,
            al.access_result
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        WHERE DATE(al.timestamp) = DATE('now')
            AND (l.lane_type = 'exit' OR l.lane_name LIKE '%exit%' OR l.lane_name LIKE '%Exit%')
        ORDER BY al.timestamp DESC
        LIMIT 100
    ''').fetchall()
    # Convert timestamps to IST
    import pytz
    from datetime import datetime
    ist_tz = pytz.timezone('Asia/Kolkata')
    result = []
    for row in rows:
        timestamp_str = row[0]
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        elif 'T' in timestamp_str:
            utc_time = datetime.fromisoformat(timestamp_str + '+00:00')
        else:
            utc_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
        ist_time = utc_time.astimezone(ist_tz)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        result.append({
            'time': ist_time_str,
            'tag_id': row[1],
            'vehicle_number': row[2] or '',
            'owner_name': row[3] or '',
            'model_name': row[4] or '',
            'lane_name': row[5] or '',
            'access_result': row[6] or ''
        })
    return jsonify({'recent_exits': result})