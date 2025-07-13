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
    
    # 1. Current Occupancy
    current_occupancy = db.execute("""
        SELECT COUNT(DISTINCT tag_id) as count
        FROM access_logs al1
        WHERE al1.access_result = 'granted'
        AND al1.timestamp = (
            SELECT MAX(al2.timestamp)
            FROM access_logs al2
            WHERE al2.tag_id = al1.tag_id
        )
    """).fetchone()[0]
    
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
    
    # 4. Lane Utilization
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
    
    # 5. Reader Health Status
    reader_health = [list(row) for row in db.execute("""
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
    """).fetchall()]
    
    # 6. Top Users (Most Active Tags) - with cached vehicle details
    top_users = [list(row) for row in db.execute("""
        SELECT 
            al.tag_id,
            ku.name as user_name,
            COALESCE(ku.vehicle_number, tvc.vehicle_number) as vehicle_number,
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
        WHERE al.timestamp >= datetime('now', '-30 days')
        GROUP BY al.tag_id, ku.name, ku.vehicle_number, tvc.vehicle_number, tvc.owner_name, tvc.model_name, tvc.fuel_type
        ORDER BY total_events DESC
        LIMIT 10
    """).fetchall()]
    
    # 7. Denied Access Analysis (with cached vehicle numbers)
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
            r.reader_ip
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        JOIN lanes l ON al.lane_id = l.id
        JOIN readers r ON al.reader_id = r.id
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
    
    return {
        'current_occupancy': current_occupancy,
        'today_stats': {
            'total': today_stats[0],
            'granted': today_stats[1],
            'denied': today_stats[2]
        },
        'hourly_data': hourly_data,
        'lane_utilization': lane_utilization,
        'reader_health': reader_health,
        'top_users': top_users,
        'denied_analysis': denied_analysis,
        'recent_activity': recent_activity,
        'weekly_trends': weekly_trends,
        'suspicious_activity': suspicious_activity
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