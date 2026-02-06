"""
Database Migration Script for Paper Trading Tables
Creates paper_accounts, paper_orders, and paper_positions tables
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database_unified import Base, engine, PaperAccount, PaperOrder, PaperPosition
from sqlalchemy import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def create_paper_trading_tables():
    """Create paper trading tables if they don't exist"""
    try:
        logger.info("🚀 Starting paper trading tables migration...")
        
        # Check if tables already exist
        tables_to_create = {
            'paper_accounts': PaperAccount,
            'paper_orders': PaperOrder,
            'paper_positions': PaperPosition
        }
        
        existing_tables = []
        missing_tables = []
        
        for table_name, model in tables_to_create.items():
            if check_table_exists(table_name):
                existing_tables.append(table_name)
                logger.info(f"✅ Table '{table_name}' already exists")
            else:
                missing_tables.append(table_name)
                logger.info(f"⚠️  Table '{table_name}' does not exist, will be created")
        
        if missing_tables:
            logger.info(f"📦 Creating {len(missing_tables)} missing table(s)...")
            # Create all tables (SQLAlchemy will skip existing ones)
            Base.metadata.create_all(bind=engine, tables=[tables_to_create[name].__table__ for name in missing_tables])
            logger.info(f"✅ Created {len(missing_tables)} table(s) successfully")
        else:
            logger.info("✅ All paper trading tables already exist")
        
        # Verify tables were created
        logger.info("\n🔍 Verifying tables...")
        for table_name in tables_to_create.keys():
            if check_table_exists(table_name):
                logger.info(f"✅ Verified: '{table_name}' exists")
            else:
                logger.error(f"❌ ERROR: '{table_name}' was not created!")
                return False
        
        logger.info("\n🎉 Paper trading tables migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_paper_trading_tables()
    sys.exit(0 if success else 1)

