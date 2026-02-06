#!/usr/bin/env python3
"""
Database migration to fix orders table schema
Adds missing columns: filled_time, filled_price, commission, notes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.database import DATABASE_URL
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to fix orders table"""
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                logger.info("🔧 Starting orders table migration...")
                
                # Check if columns exist and add them if they don't
                columns_to_add = [
                    ("filled_time", "TIMESTAMP"),
                    ("filled_price", "FLOAT"),
                    ("commission", "FLOAT DEFAULT 0.0"),
                    ("notes", "TEXT")
                ]
                
                for column_name, column_type in columns_to_add:
                    # Check if column exists
                    check_query = text(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'orders' 
                        AND column_name = '{column_name}'
                    """)
                    
                    result = conn.execute(check_query).fetchone()
                    
                    if not result:
                        logger.info(f"➕ Adding column: {column_name}")
                        alter_query = text(f"ALTER TABLE orders ADD COLUMN {column_name} {column_type}")
                        conn.execute(alter_query)
                    else:
                        logger.info(f"✅ Column {column_name} already exists")
                
                # Commit transaction
                trans.commit()
                logger.info("✅ Orders table migration completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"❌ Migration failed: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Database connection error: {str(e)}")
        raise

def verify_migration():
    """Verify that the migration was successful"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if all required columns exist
            query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'orders' 
                ORDER BY column_name
            """)
            
            result = conn.execute(query).fetchall()
            
            logger.info("📋 Current orders table schema:")
            for row in result:
                logger.info(f"   {row[0]}: {row[1]}")
            
            # Check for required columns
            required_columns = ['filled_time', 'filled_price', 'commission', 'notes']
            existing_columns = [row[0] for row in result]
            
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            if missing_columns:
                logger.warning(f"⚠️ Missing columns: {missing_columns}")
                return False
            else:
                logger.info("✅ All required columns are present!")
                return True
                
    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Orders Table Migration Script")
    print("=" * 40)
    
    try:
        # Run migration
        run_migration()
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            print("✅ Orders table now has all required columns")
            print("✅ Order placement should work now")
        else:
            print("\n❌ Migration verification failed")
            print("Please check the database manually")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        print("Please check your database connection and try again")
        sys.exit(1)
