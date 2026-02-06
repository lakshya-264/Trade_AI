"""
Add Custom Stocks to StockMaster Database
Adds the requested stocks to the stock_master table
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database_unified import SessionLocal, StockMaster
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom stocks to add
CUSTOM_STOCKS = [
    {"symbol": "NMDC", "name": "NMDC Limited", "sector": "Steel", "exchange": "NSE"},
    {"symbol": "INFIBEAM", "name": "Infibeam Avenues Limited", "sector": "IT", "exchange": "NSE"},
    {"symbol": "INDIANREN", "name": "Indian Renewable Energy Development Agency", "sector": "Power", "exchange": "NSE"},
    {"symbol": "TANLA", "name": "Tanla Platforms Limited", "sector": "IT", "exchange": "NSE"},
    {"symbol": "BIRLASOFT", "name": "Birlasoft Limited", "sector": "IT", "exchange": "NSE"},
    {"symbol": "SUZLON", "name": "Suzlon Energy Limited", "sector": "Power", "exchange": "NSE"},
    {"symbol": "SAKSOFT", "name": "Saksoft Limited", "sector": "IT", "exchange": "NSE"},
    {"symbol": "GAIL", "name": "GAIL (India) Limited", "sector": "Oil & Gas", "exchange": "NSE"},
    {"symbol": "ADANIGREEN", "name": "Adani Green Energy Limited", "sector": "Power", "exchange": "NSE"},
    {"symbol": "NHPC", "name": "NHPC Limited", "sector": "Power", "exchange": "NSE"},
    {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Limited", "sector": "Infrastructure", "exchange": "NSE"},
    {"symbol": "IRB", "name": "IRB Infrastructure Developers Limited", "sector": "Infrastructure", "exchange": "NSE"},
    {"symbol": "BAJAJHLDNG", "name": "Bajaj Housing Finance Limited", "sector": "Financial Services", "exchange": "NSE"},
    {"symbol": "HGIEL", "name": "Hindustan Green Energy Limited", "sector": "Power", "exchange": "NSE"},
    {"symbol": "BSE", "name": "BSE Limited", "sector": "Financial Services", "exchange": "NSE"},
]

def add_custom_stocks():
    """Add custom stocks to StockMaster table"""
    db: Session = SessionLocal()
    try:
        created_count = 0
        updated_count = 0
        
        logger.info(f"🌱 Adding {len(CUSTOM_STOCKS)} custom stocks to StockMaster...")
        
        for stock_data in CUSTOM_STOCKS:
            try:
                symbol = stock_data["symbol"].upper()
                
                # Check if stock already exists
                existing = db.query(StockMaster).filter(
                    StockMaster.symbol == symbol,
                    StockMaster.exchange == stock_data["exchange"]
                ).first()
                
                if existing:
                    # Update existing
                    existing.company_name = stock_data["name"]
                    existing.sector = stock_data["sector"]
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                    logger.info(f"  ✅ Updated: {symbol} - {stock_data['name']}")
                else:
                    # Create new entry
                    stock = StockMaster(
                        symbol=symbol,
                        company_name=stock_data["name"],
                        exchange=stock_data["exchange"],
                        sector=stock_data["sector"],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(stock)
                    created_count += 1
                    logger.info(f"  ✅ Created: {symbol} - {stock_data['name']}")
                    
            except Exception as e:
                logger.warning(f"  ⚠️ Error processing {stock_data.get('symbol', 'UNKNOWN')}: {e}")
                continue
        
        db.commit()
        logger.info(f"✅ StockMaster updated: {created_count} created, {updated_count} updated")
        
        # Verify
        total_custom = db.query(StockMaster).filter(
            StockMaster.symbol.in_([s["symbol"].upper() for s in CUSTOM_STOCKS])
        ).count()
        logger.info(f"✅ Total custom stocks in StockMaster: {total_custom}/{len(CUSTOM_STOCKS)}")
        
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error adding custom stocks: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Adding Custom Stocks to StockMaster")
    logger.info("=" * 60)
    
    success = add_custom_stocks()
    
    if success:
        logger.info("=" * 60)
        logger.info("✅ Custom stocks added successfully!")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("❌ Failed to add custom stocks")
        logger.error("=" * 60)
        sys.exit(1)

