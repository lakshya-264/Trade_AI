"""
Retry Failed Stocks Sync
Retries financial data sync for stocks that failed due to rate limiting or errors
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database_unified import SessionLocal
from services.nifty50_financial_sync import nifty50_financial_sync
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Stocks that typically fail due to rate limiting or other issues
# You can customize this list based on your previous run
FAILED_STOCKS = [
    "COALINDIA",
    "HEROMOTOCO",
    "HINDALCO",
    "POWERGRID",
    "DRREDDY",
    "GRASIM",
    "NTPC",
    "TATAMOTORS"
]

async def retry_failed_stocks():
    """Retry sync for failed stocks"""
    logger.info("🔄 Starting retry for failed stocks...")
    logger.info(f"📋 Stocks to retry: {len(FAILED_STOCKS)}")
    logger.info("=" * 60)
    
    db = SessionLocal()
    results = []
    
    try:
        for idx, symbol in enumerate(FAILED_STOCKS, 1):
            logger.info(f"🔄 [{idx}/{len(FAILED_STOCKS)}] Retrying {symbol}...")
            
            try:
                # Add delay between requests to avoid rate limiting
                if idx > 1:
                    await asyncio.sleep(5)  # 5 second delay between stocks
                
                result = await nifty50_financial_sync.sync_stock_financial_data(db, symbol)
                results.append(result)
                
                if result.get("success"):
                    logger.info(f"✅ {symbol}: {result.get('quarterly_saved', 0)} quarters saved")
                else:
                    logger.warning(f"❌ {symbol}: {result.get('error', 'Failed')}")
            except Exception as e:
                logger.error(f"❌ Error syncing {symbol}: {e}")
                results.append({
                    "symbol": symbol,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r.get("success"))
        total_quarters = sum(r.get("quarterly_saved", 0) for r in results)
        
        logger.info("=" * 60)
        logger.info("📊 RETRY SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Successful: {successful}/{len(FAILED_STOCKS)}")
        logger.info(f"❌ Failed: {len(FAILED_STOCKS) - successful}")
        logger.info(f"📊 Total quarters saved: {total_quarters}")
        logger.info("=" * 60)
        
        return successful == len(FAILED_STOCKS)
        
    finally:
        db.close()

if __name__ == "__main__":
    try:
        success = asyncio.run(retry_failed_stocks())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Retry interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

