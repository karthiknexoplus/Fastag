#!/usr/bin/env python3
"""
Script to populate enhanced vehicle details for existing 34161 tags
Fetches vehicle number from Axis Bank API and additional details from Acko API
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
        logging.FileHandler('populate_enhanced_vehicle_cache.log'),
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
        
        # Get unique 34161 tags that don't have complete vehicle details in cache
        query = """
        SELECT DISTINCT al.tag_id 
        FROM access_logs al
        LEFT JOIN tag_vehicle_cache tvc ON al.tag_id = tvc.tag_id
        WHERE al.tag_id LIKE '34161%'
        AND (tvc.vehicle_number IS NULL OR tvc.vehicle_number = '' OR tvc.owner_name IS NULL OR tvc.model_name IS NULL)
        ORDER BY al.tag_id
        """
        
        rows = c.execute(query).fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Error getting unique 34161 tags: {e}")
        return []

def fetch_vehicle_number_from_axis(tag_id):
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

def fetch_vehicle_details_from_acko(vehicle_number):
    """Fetch vehicle details from Acko API"""
    try:
        url = f'https://www.acko.com/api/app/vehicleInfo/?regNo={vehicle_number}'
        headers = {
            'Cookie': '__cf_bm=pGh50u94vAfct.OfbGLFFETRpGkG.c3kiX_7rg8j5Zo-1752374138-1.0.1.1-rWgkGF5d83kQHh.O.2NEe1WolLv.rKJyzup7ZRVTcezjH8t5Z.wJDDEoD.LZW3GRCFS2Dup2_InlxdHYx3rFrISKs8Cx6i156cMjOoJIhI0; trackerid=58db3079-80b0-40a3-b71e-0aa17adcd4ff; acko_visit=72id4bJOAC1NhUwxz9WHaQ'
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('registration_number'):
                return {
                    'owner_name': data.get('owner_name', ''),
                    'model_name': data.get('model_name', ''),
                    'fuel_type': data.get('fuel_type', ''),
                    'vehicle_type': data.get('vehicle_type_v2', ''),
                    'make_name': data.get('db_make_name', '')
                }
            else:
                logger.warning(f"No vehicle details found for {vehicle_number}")
                return None
        else:
            logger.error(f"Failed to fetch vehicle details for {vehicle_number}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching vehicle details for {vehicle_number}: {e}")
        return None

def cache_enhanced_vehicle_details(tag_id, vehicle_number, owner_name=None, model_name=None, fuel_type=None):
    """Cache enhanced vehicle details in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if already exists
        c.execute("SELECT vehicle_number FROM tag_vehicle_cache WHERE tag_id=?", (tag_id,))
        row = c.fetchone()
        
        if row:
            # Update existing record
            c.execute("""
                UPDATE tag_vehicle_cache 
                SET vehicle_number=?, owner_name=?, model_name=?, fuel_type=?, last_updated=CURRENT_TIMESTAMP 
                WHERE tag_id=?
            """, (vehicle_number, owner_name, model_name, fuel_type, tag_id))
            logger.info(f"✓ Updated enhanced vehicle details for tag {tag_id}: {vehicle_number} - {owner_name} - {model_name} - {fuel_type}")
        else:
            # Insert new record
            c.execute("""
                INSERT INTO tag_vehicle_cache (tag_id, vehicle_number, owner_name, model_name, fuel_type) 
                VALUES (?, ?, ?, ?, ?)
            """, (tag_id, vehicle_number, owner_name, model_name, fuel_type))
            logger.info(f"✓ Cached enhanced vehicle details for tag {tag_id}: {vehicle_number} - {owner_name} - {model_name} - {fuel_type}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error caching enhanced vehicle details for tag {tag_id}: {e}")
        return False

def create_enhanced_cache_table():
    """Create enhanced tag_vehicle_cache table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS tag_vehicle_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id TEXT UNIQUE NOT NULL,
                vehicle_number TEXT,
                owner_name TEXT,
                model_name TEXT,
                fuel_type TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("✓ Enhanced tag_vehicle_cache table ready")
        
    except Exception as e:
        logger.error(f"Error creating enhanced cache table: {e}")

def main():
    """Main function to populate enhanced vehicle cache"""
    logger.info("=" * 60)
    logger.info("STARTING ENHANCED VEHICLE CACHE POPULATION")
    logger.info("=" * 60)
    
    # Create enhanced cache table if needed
    create_enhanced_cache_table()
    
    # Get unique 34161 tags
    unique_tags = get_unique_34161_tags()
    
    if not unique_tags:
        logger.info("No new 34161 tags found to populate with enhanced details")
        return
    
    logger.info(f"Found {len(unique_tags)} unique 34161 tags to populate with enhanced details")
    
    # Process each tag
    successful = 0
    failed = 0
    
    for i, tag_id in enumerate(unique_tags, 1):
        logger.info(f"Processing {i}/{len(unique_tags)}: {tag_id}")
        
        # Step 1: Fetch vehicle number from Axis Bank API
        vehicle_number = fetch_vehicle_number_from_axis(tag_id)
        
        if vehicle_number:
            # Step 2: Fetch additional details from Acko API
            vehicle_details = fetch_vehicle_details_from_acko(vehicle_number)
            
            owner_name = vehicle_details.get('owner_name', '') if vehicle_details else ''
            model_name = vehicle_details.get('model_name', '') if vehicle_details else ''
            fuel_type = vehicle_details.get('fuel_type', '') if vehicle_details else ''
            
            # Step 3: Cache all details
            if cache_enhanced_vehicle_details(tag_id, vehicle_number, owner_name, model_name, fuel_type):
                successful += 1
                logger.info(f"✓ Successfully cached enhanced details for {tag_id}: {vehicle_number} - {owner_name} - {model_name} - {fuel_type}")
            else:
                failed += 1
                logger.error(f"✗ Failed to cache enhanced details for {tag_id}")
        else:
            failed += 1
            logger.warning(f"✗ No vehicle number found for tag {tag_id}")
        
        # Add delay to avoid overwhelming the APIs
        time.sleep(2)
    
    logger.info("=" * 60)
    logger.info("ENHANCED POPULATION COMPLETE")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total processed: {len(unique_tags)}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main() 