#!/usr/bin/env python3
"""
Script to check existing 34161 tags in access logs and their cache status
"""

import sqlite3
from datetime import datetime

# Database path
DB_PATH = 'instance/fastag.db'

def check_34161_tags():
    """Check all 34161 tags in access logs"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get all unique 34161 tags with their access counts
        query = """
        SELECT 
            al.tag_id,
            COUNT(*) as access_count,
            SUM(CASE WHEN al.access_result = 'granted' THEN 1 ELSE 0 END) as granted_count,
            SUM(CASE WHEN al.access_result = 'denied' THEN 1 ELSE 0 END) as denied_count,
            MAX(al.timestamp) as last_seen,
            tvc.vehicle_number as cached_vehicle,
            ku.vehicle_number as kyc_vehicle,
            ku.name as kyc_name
        FROM access_logs al
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
        WHERE al.tag_id LIKE '34161%'
        GROUP BY al.tag_id
        ORDER BY access_count DESC
        """
        
        rows = c.execute(query).fetchall()
        conn.close()
        
        print("=" * 80)
        print("34161 TAGS ANALYSIS")
        print("=" * 80)
        print(f"Total unique 34161 tags found: {len(rows)}")
        print()
        
        if not rows:
            print("No 34161 tags found in access logs")
            return
        
        # Print summary
        total_access = sum(row[1] for row in rows)
        total_granted = sum(row[2] for row in rows)
        total_denied = sum(row[3] for row in rows)
        cached_count = sum(1 for row in rows if row[5])
        kyc_count = sum(1 for row in rows if row[6])
        
        print(f"SUMMARY:")
        print(f"  Total access attempts: {total_access}")
        print(f"  Granted: {total_granted}")
        print(f"  Denied: {total_denied}")
        print(f"  Tags with cached vehicle numbers: {cached_count}")
        print(f"  Tags in KYC users: {kyc_count}")
        print()
        
        # Print detailed list
        print("DETAILED LIST:")
        print("-" * 80)
        print(f"{'Tag ID':<30} {'Access':<8} {'Granted':<8} {'Denied':<8} {'Last Seen':<20} {'Cached VRN':<15} {'KYC VRN':<15} {'KYC Name':<20}")
        print("-" * 80)
        
        for row in rows:
            tag_id, access_count, granted_count, denied_count, last_seen, cached_vehicle, kyc_vehicle, kyc_name = row
            
            # Format last seen
            last_seen_str = last_seen[:19] if last_seen else "Never"
            
            # Format vehicle numbers
            cached_vrn = cached_vehicle or "Not cached"
            kyc_vrn = kyc_vehicle or "Not in KYC"
            kyc_name = kyc_name or "Not in KYC"
            
            print(f"{tag_id:<30} {access_count:<8} {granted_count:<8} {denied_count:<8} {last_seen_str:<20} {cached_vrn:<15} {kyc_vrn:<15} {kyc_name:<20}")
        
        print("-" * 80)
        
        # Show tags that need caching
        uncached_tags = [row[0] for row in rows if not row[5] and not row[6]]
        if uncached_tags:
            print(f"\nTAGS NEEDING VEHICLE NUMBER CACHING ({len(uncached_tags)}):")
            for tag_id in uncached_tags:
                print(f"  - {tag_id}")
        
    except Exception as e:
        print(f"Error checking 34161 tags: {e}")

if __name__ == "__main__":
    check_34161_tags() 