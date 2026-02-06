"""
Stock Master Service
Fetches and maintains complete stock list from NSE/BSE
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from core.database_unified import StockMaster, SessionLocal
from core.nse_bse_stock_scraper import NSEBSEStockScraper

logger = logging.getLogger(__name__)

class StockMasterService:
    """Service to manage stock master list"""
    
    def __init__(self):
        self.scraper = NSEBSEStockScraper()
    
    async def sync_stock_master(self, exchange: str = "NSE") -> Dict:
        """
        Sync stock master list from NSE/BSE
        
        Args:
            exchange: "NSE" or "BSE"
        
        Returns:
            Dictionary with sync results
        """
        try:
            logger.info(f"🔄 Starting stock master sync for {exchange}...")
            
            # Fetch stock list
            if exchange == "NSE":
                stocks = await self.scraper.get_nse_stock_list()
            else:
                stocks = await self.scraper.get_bse_stock_list()
            
            if not stocks:
                logger.warning(f"No stocks fetched from {exchange}")
                return {
                    "success": False,
                    "error": f"No stocks fetched from {exchange}",
                    "synced": 0
                }
            
            # Store in database
            db = SessionLocal()
            synced_count = 0
            updated_count = 0
            
            try:
                for stock_data in stocks:
                    try:
                        symbol = stock_data.get("symbol", "").upper()
                        if not symbol:
                            continue
                        
                        # Check if exists
                        existing = db.query(StockMaster).filter(
                            StockMaster.symbol == symbol,
                            StockMaster.exchange == exchange
                        ).first()
                        
                        stock_master_data = {
                            "symbol": symbol,
                            "isin": stock_data.get("isin"),
                            "exchange": exchange,
                            "sector": stock_data.get("sector"),
                            "sub_sector": stock_data.get("sub_sector"),
                            "industry": stock_data.get("industry"),
                            "face_value": stock_data.get("face_value"),
                            "listing_date": stock_data.get("listing_date"),
                            "market_cap": stock_data.get("market_cap"),
                            "company_name": stock_data.get("name") or stock_data.get("company_name"),
                            "updated_at": datetime.utcnow()
                        }
                        
                        if existing:
                            # Update existing
                            for key, value in stock_master_data.items():
                                if value is not None:
                                    setattr(existing, key, value)
                            updated_count += 1
                        else:
                            # Create new
                            stock_master = StockMaster(**stock_master_data)
                            stock_master.created_at = datetime.utcnow()
                            db.add(stock_master)
                            synced_count += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing stock {stock_data.get('symbol')}: {e}")
                        continue
                
                db.commit()
                logger.info(f"✅ Stock master sync completed: {synced_count} new, {updated_count} updated")
                
                return {
                    "success": True,
                    "exchange": exchange,
                    "total_fetched": len(stocks),
                    "synced": synced_count,
                    "updated": updated_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Error syncing stock master: {e}")
            return {
                "success": False,
                "error": str(e),
                "synced": 0
            }
    
    def get_stock_master(self, exchange: Optional[str] = None, sector: Optional[str] = None) -> List[Dict]:
        """
        Get stock master list from database
        
        Args:
            exchange: Filter by exchange (NSE/BSE)
            sector: Filter by sector
        
        Returns:
            List of stock master records
        """
        try:
            db = SessionLocal()
            try:
                query = db.query(StockMaster)
                
                if exchange:
                    query = query.filter(StockMaster.exchange == exchange)
                
                if sector:
                    query = query.filter(StockMaster.sector == sector)
                
                stocks = query.all()
                
                return [
                    {
                        "id": stock.id,
                        "symbol": stock.symbol,
                        "isin": stock.isin,
                        "exchange": stock.exchange,
                        "sector": stock.sector,
                        "sub_sector": stock.sub_sector,
                        "industry": stock.industry,
                        "face_value": float(stock.face_value) if stock.face_value else None,
                        "listing_date": stock.listing_date.isoformat() if stock.listing_date else None,
                        "market_cap": float(stock.market_cap) if stock.market_cap else None,
                        "company_name": stock.company_name
                    }
                    for stock in stocks
                ]
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Error getting stock master: {e}")
            return []
    
    async def close(self):
        """Close scraper session"""
        await self.scraper.close()

# Create singleton instance
stock_master_service = StockMasterService()

