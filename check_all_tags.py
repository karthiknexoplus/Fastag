#!/usr/bin/env python3
"""
Script to check all tags in access logs
"""

import sqlite3
from datetime import datetime

# Database path
DB_PATH = 'instance/fastag.db'

def check_all_tags():
    """Check all tags in access logs"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get all unique tags with their access counts
        query = """
        SELECT 
            al.tag_id,
            COUNT(*) as access_count,
            SUM(CASE WHEN al.access_result = 'granted' THEN 1 ELSE 0 END) as granted_count,
            SUM(CASE WHEN al.access_result = 'denied' THEN 1 ELSE 0 END) as denied_count,
            MAX(al.timestamp) as last_seen,
            ku.vehicle_number as kyc_vehicle,
            ku.name as kyc_name
        FROM access_logs al
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        GROUP BY al.tag_id
        ORDER BY access_count DESC
        LIMIT 50
        """
        
        rows = c.execute(query).fetchall()
        conn.close()
        
        print("=" * 80)
        print("ALL TAGS ANALYSIS (Top 50 by access count)")
        print("=" * 80)
        print(f"Total unique tags found: {len(rows)}")
        print()
        
        if not rows:
            print("No tags found in access logs")
            return
        
        # Print summary
        total_access = sum(row[1] for row in rows)
        total_granted = sum(row[2] for row in rows)
        total_denied = sum(row[3] for row in rows)
        kyc_count = sum(1 for row in rows if row[5])
        
        print(f"SUMMARY:")
        print(f"  Total access attempts: {total_access}")
        print(f"  Granted: {total_granted}")
        print(f"  Denied: {total_denied}")
        print(f"  Tags in KYC users: {kyc_count}")
        print()
        
        # Print detailed list
        print("DETAILED LIST:")
        print("-" * 80)
        print(f"{'Tag ID':<30} {'Access':<8} {'Granted':<8} {'Denied':<8} {'Last Seen':<20} {'KYC VRN':<15} {'KYC Name':<20}")
        print("-" * 80)
        
        for row in rows:
            tag_id, access_count, granted_count, denied_count, last_seen, kyc_vehicle, kyc_name = row
            
            # Format last seen
            last_seen_str = last_seen[:19] if last_seen else "Never"
            
            # Format vehicle numbers
            kyc_vrn = kyc_vehicle or "Not in KYC"
            kyc_name = kyc_name or "Not in KYC"
            
            print(f"{tag_id:<30} {access_count:<8} {granted_count:<8} {denied_count:<8} {last_seen_str:<20} {kyc_vrn:<15} {kyc_name:<20}")
        
        print("-" * 80)
        
        # Check for 34161 tags specifically
        print("\nCHECKING FOR 34161 TAGS:")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Count 34161 tags
        count_query = """
        SELECT COUNT(DISTINCT tag_id) 
        FROM access_logs 
        WHERE tag_id LIKE '34161%'
        """
        count = c.execute(count_query).fetchone()[0]
        print(f"  Total 34161 tags: {count}")
        
        if count > 0:
            # Get 34161 tags
            query = """
            SELECT DISTINCT tag_id 
            FROM access_logs 
            WHERE tag_id LIKE '34161%'
            ORDER BY tag_id
            """
            rows = c.execute(query).fetchall()
            print("  34161 tags found:")
            for row in rows:
                print(f"    - {row[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking tags: {e}")

if __name__ == "__main__":
    check_all_tags() 