"""
Run Complete Database Setup
Initializes database and syncs financial data for all Nifty 50 stocks
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database_unified import (
    Base, engine, SessionLocal,
    StockMaster
)
from services.nifty50_financial_sync import nifty50_financial_sync, NIFTY_50_SYMBOLS
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

async def main():
    """Main function to run complete setup"""
    logger.info("🚀 Starting Complete Database Setup...")
    logger.info("=" * 60)
    
    results = {
        "tables_created": False,
        "stocks_seeded": 0,
        "financial_sync": None
    }
    
    # Step 1: Create all tables
    logger.info("📊 Step 1: Creating all database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        results["tables_created"] = True
        logger.info("✅ All database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False
    
    # Step 2: Seed StockMaster
    logger.info("🌱 Step 2: Seeding StockMaster table with Nifty 50 stocks...")
    db = SessionLocal()
    try:
        created_count = 0
        updated_count = 0
        
        for symbol in NIFTY_50_SYMBOLS:
            try:
                existing = db.query(StockMaster).filter(
                    StockMaster.symbol == symbol.upper()
                ).first()
                
                if existing:
                    if not existing.company_name:
                        existing.company_name = COMPANY_NAMES.get(symbol, symbol)
                    if not existing.exchange:
                        existing.exchange = "NSE"
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
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
                logger.warning(f"⚠️ Error processing {symbol}: {e}")
                continue
        
        db.commit()
        results["stocks_seeded"] = created_count + updated_count
        logger.info(f"✅ StockMaster seeded: {created_count} created, {updated_count} updated")
        
        # Verify
        total_stocks = db.query(StockMaster).filter(
            StockMaster.symbol.in_([s.upper() for s in NIFTY_50_SYMBOLS])
        ).count()
        logger.info(f"✅ Total stocks in StockMaster: {total_stocks}/{len(NIFTY_50_SYMBOLS)}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error seeding StockMaster: {e}")
        db.close()
        return False
    
    # Step 3: Sync Financial Data
    logger.info("🔄 Step 3: Starting financial data sync for all Nifty 50 stocks...")
    logger.info("⏳ This may take 10-15 minutes...")
    logger.info("=" * 60)
    
    try:
        sync_result = await nifty50_financial_sync.sync_all_nifty50(db, max_concurrent=5)
        results["financial_sync"] = sync_result
        logger.info("=" * 60)
        logger.info(f"✅ Financial data sync completed!")
        logger.info(f"   - Successful: {sync_result.get('successful', 0)}/{sync_result.get('total_symbols', 0)}")
        logger.info(f"   - Failed: {sync_result.get('failed', 0)}")
        logger.info(f"   - Total quarters saved: {sync_result.get('total_quarters_saved', 0)}")
    except Exception as e:
        logger.error(f"❌ Error in financial data sync: {e}")
        import traceback
        logger.error(traceback.format_exc())
        results["financial_sync"] = {"success": False, "error": str(e)}
    finally:
        db.close()
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 SETUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Tables Created: {results['tables_created']}")
    logger.info(f"✅ Stocks Seeded: {results['stocks_seeded']}")
    if results['financial_sync']:
        logger.info(f"✅ Financial Sync: {results['financial_sync'].get('successful', 0)}/{results['financial_sync'].get('total_symbols', 0)} stocks")
    logger.info("=" * 60)
    logger.info("🎉 Complete database setup finished!")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

