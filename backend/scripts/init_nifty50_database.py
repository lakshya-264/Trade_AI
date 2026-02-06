"""
Initialize Database Tables and Seed Nifty 50 Stocks
Creates all required tables and seeds StockMaster with Nifty 50 stocks
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database_unified import (
    Base, engine, SessionLocal,
    StockMaster, FinancialData, FinancialRatios,
    ScreenerGrowthMetrics, ScreenerBalanceSheet,
    ScreenerCashFlow, ScreenerShareholding
)
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Nifty 50 symbols
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", 
    "HDFC", "ITC", "BHARTIARTL", "SBIN", "BAJFINANCE", "ASIANPAINT", "AXISBANK", 
    "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "POWERGRID",
    "NTPC", "TECHM", "WIPRO", "HCLTECH", "LT", "BAJAJFINSV", "DRREDDY", 
    "TATAMOTORS", "BRITANNIA", "EICHERMOT", "SHREECEM", "JSWSTEEL", "TATASTEEL", 
    "INDUSINDBK", "COALINDIA", "GRASIM", "CIPLA", "ONGC", "TATACONSUM", "APOLLOHOSP",
    "ADANIPORTS", "BPCL", "HEROMOTOCO", "DIVISLAB", "UPL", "BAJAJ-AUTO", "TATAPOWER", 
    "ADANIENT", "SBILIFE", "HINDALCO"
]

# Company names mapping (for reference)
COMPANY_NAMES = {
    "RELIANCE": "Reliance Industries Ltd",
    "TCS": "Tata Consultancy Services Ltd",
    "HDFCBANK": "HDFC Bank Ltd",
    "INFY": "Infosys Ltd",
    "HINDUNILVR": "Hindustan Unilever Ltd",
    "ICICIBANK": "ICICI Bank Ltd",
    "KOTAKBANK": "Kotak Mahindra Bank Ltd",
    "HDFC": "Housing Development Finance Corporation Ltd",
    "ITC": "ITC Ltd",
    "BHARTIARTL": "Bharti Airtel Ltd",
    "SBIN": "State Bank of India",
    "BAJFINANCE": "Bajaj Finance Ltd",
    "ASIANPAINT": "Asian Paints Ltd",
    "AXISBANK": "Axis Bank Ltd",
    "MARUTI": "Maruti Suzuki India Ltd",
    "SUNPHARMA": "Sun Pharmaceutical Industries Ltd",
    "TITAN": "Titan Company Ltd",
    "ULTRACEMCO": "UltraTech Cement Ltd",
    "NESTLEIND": "Nestle India Ltd",
    "POWERGRID": "Power Grid Corporation of India Ltd",
    "NTPC": "NTPC Ltd",
    "TECHM": "Tech Mahindra Ltd",
    "WIPRO": "Wipro Ltd",
    "HCLTECH": "HCL Technologies Ltd",
    "LT": "Larsen & Toubro Ltd",
    "BAJAJFINSV": "Bajaj Finserv Ltd",
    "DRREDDY": "Dr. Reddy's Laboratories Ltd",
    "TATAMOTORS": "Tata Motors Ltd",
    "BRITANNIA": "Britannia Industries Ltd",
    "EICHERMOT": "Eicher Motors Ltd",
    "SHREECEM": "Shree Cement Ltd",
    "JSWSTEEL": "JSW Steel Ltd",
    "TATASTEEL": "Tata Steel Ltd",
    "INDUSINDBK": "IndusInd Bank Ltd",
    "COALINDIA": "Coal India Ltd",
    "GRASIM": "Grasim Industries Ltd",
    "CIPLA": "Cipla Ltd",
    "ONGC": "Oil and Natural Gas Corporation Ltd",
    "TATACONSUM": "Tata Consumer Products Ltd",
    "APOLLOHOSP": "Apollo Hospitals Enterprise Ltd",
    "ADANIPORTS": "Adani Ports and Special Economic Zone Ltd",
    "BPCL": "Bharat Petroleum Corporation Ltd",
    "HEROMOTOCO": "Hero MotoCorp Ltd",
    "DIVISLAB": "Divis Laboratories Ltd",
    "UPL": "UPL Ltd",
    "BAJAJ-AUTO": "Bajaj Auto Ltd",
    "TATAPOWER": "Tata Power Company Ltd",
    "ADANIENT": "Adani Enterprises Ltd",
    "SBILIFE": "SBI Life Insurance Company Ltd",
    "HINDALCO": "Hindalco Industries Ltd"
}

def create_all_tables():
    """Create all database tables if they don't exist"""
    try:
        logger.info("📊 Creating all database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False

def seed_stock_master(db: Session):
    """Seed StockMaster table with Nifty 50 stocks"""
    try:
        logger.info("🌱 Seeding StockMaster table with Nifty 50 stocks...")
        
        created_count = 0
        updated_count = 0
        
        for symbol in NIFTY_50_SYMBOLS:
            try:
                # Check if stock already exists
                existing = db.query(StockMaster).filter(
                    StockMaster.symbol == symbol.upper()
                ).first()
                
                if existing:
                    # Update if needed
                    if not existing.company_name:
                        existing.company_name = COMPANY_NAMES.get(symbol, symbol)
                    if not existing.exchange:
                        existing.exchange = "NSE"
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new entry
                    stock = StockMaster(
                        symbol=symbol.upper(),
                        company_name=COMPANY_NAMES.get(symbol, symbol),
                        exchange="NSE",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(stock)
                    created_count += 1
                    
            except Exception as e:
                logger.warning(f"Error processing {symbol}: {e}")
                continue
        
        db.commit()
        logger.info(f"✅ StockMaster seeded: {created_count} created, {updated_count} updated")
        return created_count + updated_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error seeding StockMaster: {e}")
        return 0

def verify_tables():
    """Verify that all required tables exist"""
    try:
        logger.info("🔍 Verifying database tables...")
        
        inspector = __import__('sqlalchemy.inspect', fromlist=['inspect']).inspect(engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = [
            'stock_master',
            'financial_data',
            'financial_ratios',
            'screener_growth_metrics',
            'screener_balance_sheet',
            'screener_cash_flow',
            'screener_shareholding'
        ]
        
        missing_tables = []
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if missing_tables:
            logger.warning(f"⚠️ Missing tables: {missing_tables}")
            return False
        else:
            logger.info("✅ All required tables exist")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error verifying tables: {e}")
        return False

def verify_stock_master_data(db: Session):
    """Verify StockMaster has all Nifty 50 stocks"""
    try:
        logger.info("🔍 Verifying StockMaster data...")
        
        stock_count = db.query(StockMaster).filter(
            StockMaster.symbol.in_([s.upper() for s in NIFTY_50_SYMBOLS])
        ).count()
        
        if stock_count == len(NIFTY_50_SYMBOLS):
            logger.info(f"✅ All {len(NIFTY_50_SYMBOLS)} Nifty 50 stocks are in StockMaster")
            return True
        else:
            logger.warning(f"⚠️ Only {stock_count}/{len(NIFTY_50_SYMBOLS)} stocks in StockMaster")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying StockMaster data: {e}")
        return False

def main():
    """Main function to initialize database"""
    logger.info("🚀 Starting database initialization for Nifty 50 stocks...")
    
    # Step 1: Create all tables
    if not create_all_tables():
        logger.error("❌ Failed to create tables. Exiting.")
        return False
    
    # Step 2: Verify tables exist
    if not verify_tables():
        logger.error("❌ Some required tables are missing. Exiting.")
        return False
    
    # Step 3: Seed StockMaster
    db = SessionLocal()
    try:
        seed_count = seed_stock_master(db)
        if seed_count == 0:
            logger.warning("⚠️ No stocks were seeded")
        
        # Step 4: Verify data
        verify_stock_master_data(db)
        
    finally:
        db.close()
    
    logger.info("✅ Database initialization complete!")
    logger.info("\n📊 Summary:")
    logger.info(f"   - Tables: Created/Verified")
    logger.info(f"   - StockMaster: {len(NIFTY_50_SYMBOLS)} Nifty 50 stocks")
    logger.info(f"   - Ready for financial data sync")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

