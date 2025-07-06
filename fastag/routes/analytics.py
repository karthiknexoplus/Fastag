from flask import Blueprint, render_template, jsonify, request
from fastag.utils.db import get_db
from datetime import datetime, timedelta
import sqlite3
import json

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
    today_stats = db.execute("""
        SELECT 
            COUNT(*) as total_events,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as granted,
            SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied
        FROM access_logs 
        WHERE DATE(timestamp) = DATE('now')
    """).fetchone()
    
    # 3. Hourly Activity (Last 24 hours)
    hourly_data = db.execute("""
        SELECT 
            strftime('%H', timestamp) as hour,
            COUNT(*) as total,
            SUM(CASE WHEN access_result = 'granted' THEN 1 ELSE 0 END) as granted,
            SUM(CASE WHEN access_result = 'denied' THEN 1 ELSE 0 END) as denied
        FROM access_logs 
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY strftime('%H', timestamp)
        ORDER BY hour
    """).fetchall()
    
    # 4. Lane Utilization
    lane_utilization = db.execute("""
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
    """).fetchall()
    
    # 5. Reader Health Status
    reader_health = db.execute("""
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
    """).fetchall()
    
    # 6. Top Users (Most Active Tags)
    top_users = db.execute("""
        SELECT 
            al.tag_id,
            ku.name as user_name,
            ku.vehicle_number,
            COUNT(*) as total_events,
            SUM(CASE WHEN al.access_result = 'granted' THEN 1 ELSE 0 END) as granted,
            SUM(CASE WHEN al.access_result = 'denied' THEN 1 ELSE 0 END) as denied,
            MAX(al.timestamp) as last_activity
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        WHERE al.timestamp >= datetime('now', '-30 days')
        GROUP BY al.tag_id, ku.name, ku.vehicle_number
        ORDER BY total_events DESC
        LIMIT 10
    """).fetchall()
    
    # 7. Denied Access Analysis
    denied_analysis = db.execute("""
        SELECT 
            reason,
            COUNT(*) as count
        FROM access_logs 
        WHERE access_result = 'denied' 
        AND timestamp >= datetime('now', '-7 days')
        GROUP BY reason
        ORDER BY count DESC
    """).fetchall()
    
    # 8. Recent Activity (Last 50 events)
    recent_activity = db.execute("""
        SELECT 
            al.timestamp,
            al.tag_id,
            al.access_result,
            al.reason,
            ku.name as user_name,
            ku.vehicle_number,
            l.lane_name,
            r.reader_ip
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        JOIN lanes l ON al.lane_id = l.id
        JOIN readers r ON al.reader_id = r.id
        ORDER BY al.timestamp DESC
        LIMIT 50
    """).fetchall()
    
    # 9. Weekly Trends
    weekly_trends = db.execute("""
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
    """).fetchall()
    
    # 10. Suspicious Activity (Multiple denied attempts)
    suspicious_activity = db.execute("""
        SELECT 
            tag_id,
            COUNT(*) as denied_count,
            MAX(timestamp) as last_attempt,
            GROUP_CONCAT(reason) as reasons
        FROM access_logs 
        WHERE access_result = 'denied' 
        AND timestamp >= datetime('now', '-24 hours')
        GROUP BY tag_id
        HAVING denied_count > 3
        ORDER BY denied_count DESC
    """).fetchall()
    
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
    
    db = get_db()
    
    if report_type == 'access_logs':
        query = """
            SELECT 
                al.timestamp,
                al.tag_id,
                al.access_result,
                al.reason,
                ku.name as user_name,
                ku.vehicle_number,
                l.lane_name,
                r.reader_ip
            FROM access_logs al
            LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
            JOIN lanes l ON al.lane_id = l.id
            JOIN readers r ON al.reader_id = r.id
        """
        
        if start_date and end_date:
            query += f" WHERE DATE(al.timestamp) BETWEEN '{start_date}' AND '{end_date}'"
        
        query += " ORDER BY al.timestamp DESC"
        
        rows = db.execute(query).fetchall()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'Tag ID', 'Access Result', 'Reason', 'User Name', 'Vehicle Number', 'Lane', 'Reader IP'])
        
        for row in rows:
            writer.writerow(row)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=access_logs_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
    
    return jsonify({'error': 'Invalid report type'}), 400 