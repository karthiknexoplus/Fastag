#!/usr/bin/env python3
"""
Script to update the existing tag_vehicle_cache table with new columns
"""

import sqlite3
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_database_schema.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'instance/fastag.db'

def update_tag_vehicle_cache_table():
    """Update the tag_vehicle_cache table with new columns"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check current table structure
        c.execute("PRAGMA table_info(tag_vehicle_cache)")
        columns = [row[1] for row in c.fetchall()]
        logger.info(f"Current columns: {columns}")
        
        # Add new columns if they don't exist
        new_columns = [
            ('owner_name', 'TEXT'),
            ('model_name', 'TEXT'),
            ('fuel_type', 'TEXT')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                try:
                    c.execute(f"ALTER TABLE tag_vehicle_cache ADD COLUMN {column_name} {column_type}")
                    logger.info(f"✓ Added column: {column_name}")
                except Exception as e:
                    logger.error(f"Failed to add column {column_name}: {e}")
            else:
                logger.info(f"✓ Column {column_name} already exists")
        
        # Verify final table structure
        c.execute("PRAGMA table_info(tag_vehicle_cache)")
        final_columns = [row[1] for row in c.fetchall()]
        logger.info(f"Final columns: {final_columns}")
        
        conn.commit()
        conn.close()
        
        logger.info("✓ Database schema updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")
        return False

def main():
    """Main function to update database schema"""
    logger.info("=" * 60)
    logger.info("STARTING DATABASE SCHEMA UPDATE")
    logger.info("=" * 60)
    
    if update_tag_vehicle_cache_table():
        logger.info("✓ Database schema update completed successfully")
    else:
        logger.error("✗ Database schema update failed")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main() 