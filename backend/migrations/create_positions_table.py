"""
Database migration script to create positions table
Run this script to add the positions table to your database
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.database_unified import Base, Position
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_positions_table():
    """Create positions table if it doesn't exist"""
    try:
        # Import database URL from your config
        from core.database_unified import engine
        
        # Create all tables (will skip if exists)
        Base.metadata.create_all(bind=engine, tables=[Position.__table__])
        
        logger.info("✅ Positions table created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating positions table: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Creating positions table...")
    if create_positions_table():
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed. Check logs for details.")
        sys.exit(1)
