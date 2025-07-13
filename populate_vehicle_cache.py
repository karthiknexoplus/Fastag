#!/usr/bin/env python3
"""
Script to populate vehicle numbers for existing 34161 tags in access logs
"""

import sqlite3
import requests
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('populate_vehicle_cache.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'instance/fastag.db'

def get_unique_34161_tags():
    """Get all unique tags starting with 34161 from access logs"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get unique 34161 tags that don't have vehicle numbers in cache
        query = """
        SELECT DISTINCT al.tag_id 
        FROM access_logs al
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        WHERE al.tag_id LIKE '34161%'
        AND (tvc.vehicle_number IS NULL OR tvc.vehicle_number = '')
        ORDER BY al.tag_id
        """
        
        rows = c.execute(query).fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Error getting unique 34161 tags: {e}")
        return []

def fetch_vehicle_number(tag_id):
    """Fetch vehicle number from Axis Bank API"""
    try:
        url = f'https://acquirerportal.axisbank.co.in/MTMSPG/GetTagDetails?SearchType=TagId&SearchValue={tag_id}'
        headers = {
            'Cookie': 'axisbiconnect=1067559104.47873.0000'
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ErrorMessage') == 'NONE' and data.get('npcitagDetails'):
                tag_detail = data['npcitagDetails'][0]
                vehicle_number = tag_detail.get('VRN', '')
                if vehicle_number:
                    return vehicle_number
                else:
                    logger.warning(f"No vehicle number found for tag {tag_id}")
                    return None
            else:
                logger.warning(f"No tag details found for {tag_id}: {data.get('ErrorMessage', 'Unknown error')}")
                return None
        else:
            logger.error(f"Failed to fetch vehicle number for tag {tag_id}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching vehicle number for tag {tag_id}: {e}")
        return None

def cache_vehicle_number(tag_id, vehicle_number):
    """Cache vehicle number in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if already exists
        c.execute("SELECT vehicle_number FROM tag_vehicle_cache WHERE tag_id=?", (tag_id,))
        row = c.fetchone()
        
        if row:
            # Update existing record
            c.execute("UPDATE tag_vehicle_cache SET vehicle_number=?, last_updated=CURRENT_TIMESTAMP WHERE tag_id=?", (vehicle_number, tag_id))
            logger.info(f"✓ Updated vehicle number for tag {tag_id}: {vehicle_number}")
        else:
            # Insert new record
            c.execute("INSERT INTO tag_vehicle_cache (tag_id, vehicle_number) VALUES (?, ?)", (tag_id, vehicle_number))
            logger.info(f"✓ Cached vehicle number for tag {tag_id}: {vehicle_number}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error caching vehicle number for tag {tag_id}: {e}")
        return False

def create_cache_table():
    """Create tag_vehicle_cache table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS tag_vehicle_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id TEXT UNIQUE NOT NULL,
                vehicle_number TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("✓ tag_vehicle_cache table ready")
        
    except Exception as e:
        logger.error(f"Error creating cache table: {e}")

def main():
    """Main function to populate vehicle cache"""
    logger.info("=" * 60)
    logger.info("STARTING VEHICLE CACHE POPULATION")
    logger.info("=" * 60)
    
    # Create cache table if needed
    create_cache_table()
    
    # Get unique 34161 tags
    unique_tags = get_unique_34161_tags()
    
    if not unique_tags:
        logger.info("No new 34161 tags found to populate")
        return
    
    logger.info(f"Found {len(unique_tags)} unique 34161 tags to populate")
    
    # Process each tag
    successful = 0
    failed = 0
    
    for i, tag_id in enumerate(unique_tags, 1):
        logger.info(f"Processing {i}/{len(unique_tags)}: {tag_id}")
        
        # Fetch vehicle number
        vehicle_number = fetch_vehicle_number(tag_id)
        
        if vehicle_number:
            # Cache the vehicle number
            if cache_vehicle_number(tag_id, vehicle_number):
                successful += 1
            else:
                failed += 1
        else:
            failed += 1
        
        # Add delay to avoid overwhelming the API
        time.sleep(1)
    
    logger.info("=" * 60)
    logger.info("POPULATION COMPLETE")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total processed: {len(unique_tags)}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main() 