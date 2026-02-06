"""
Database Migration: Add missing tables and indexes
Run this to add Backtesting, Screener tables and missing indexes
"""

from sqlalchemy import text, Index, inspect
from core.database_unified import engine, Base, Alert, AlertTrigger
# Import new models (they should be in database_unified.py now)
try:
    from core.database_unified import BacktestResult, BacktestConfig, ScreenerResult, ScreenerFilter
except ImportError:
    # Models might not be imported yet, that's okay - Base.metadata.create_all will handle it
    BacktestResult = BacktestConfig = ScreenerResult = ScreenerFilter = None
import logging

logger = logging.getLogger(__name__)

def create_missing_indexes():
    """Create missing performance indexes"""
    with engine.connect() as conn:
        try:
            # Alert indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
            """))
            
            # Alert Trigger indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alert_triggers_alert_id ON alert_triggers(alert_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alert_triggers_user_id ON alert_triggers(user_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alert_triggers_triggered_at ON alert_triggers(triggered_at);
            """))
            
            # Watchlist indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON watchlists(user_id);
            """))
            
            conn.commit()
            logger.info("✅ Created missing indexes")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            conn.rollback()
            raise

def create_missing_tables():
    """Create missing tables (Backtesting, Screener)"""
    try:
        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Created missing tables")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def migrate_portfolio_table_name():
    """Migrate portfolio table name from 'portfolio' to 'portfolios'"""
    with engine.connect() as conn:
        try:
            # Check if old table exists
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='portfolio'
            """))
            
            if result.fetchone():
                # Check if new table exists
                result2 = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='portfolios'
                """))
                
                if not result2.fetchone():
                    # Rename table
                    conn.execute(text("""
                        ALTER TABLE portfolio RENAME TO portfolios;
                    """))
                    logger.info("✅ Renamed portfolio table to portfolios")
                else:
                    # Both exist - migrate data and drop old
                    conn.execute(text("""
                        INSERT OR IGNORE INTO portfolios 
                        SELECT * FROM portfolio;
                    """))
                    conn.execute(text("""
                        DROP TABLE portfolio;
                    """))
                    logger.info("✅ Migrated portfolio data and dropped old table")
            else:
                logger.info("ℹ️ Portfolio table already uses correct name or doesn't exist")
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error migrating portfolio table: {e}")
            conn.rollback()
            # For SQLite, ALTER TABLE RENAME might not work in all cases
            # This is a non-critical fix, so we'll log and continue
            logger.warning("Portfolio table name migration skipped (non-critical)")

def run_migration():
    """Run all migrations"""
    logger.info("🚀 Starting database corrections migration...")
    
    try:
        # 1. Create missing tables
        logger.info("Step 1: Creating missing tables...")
        create_missing_tables()
        
        # 2. Create missing indexes
        logger.info("Step 2: Creating missing indexes...")
        create_missing_indexes()
        
        # 3. Migrate portfolio table name (if needed)
        logger.info("Step 3: Migrating portfolio table name...")
        migrate_portfolio_table_name()
        
        logger.info("✅ Database corrections migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    success = run_migration()
    sys.exit(0 if success else 1)

