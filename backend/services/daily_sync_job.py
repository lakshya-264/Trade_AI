"""
Daily Sync Job Service
Automated daily/quarterly data synchronization
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from core.database_unified import DailyMarketData, FinancialData, FinancialRatios, SessionLocal
from core.data_service import data_service
from services.financial_ratios_service import financial_ratios_service
from services.stock_master_service import stock_master_service

logger = logging.getLogger(__name__)

class DailySyncJob:
    """Daily market data synchronization"""
    
    def __init__(self):
        pass
    
    async def sync_daily_market_data(self, symbols: list = None) -> Dict:
        """
        Sync daily market data for all symbols
        
        Args:
            symbols: List of symbols to sync (None = all from stock_master)
        
        Returns:
            Sync results
        """
        try:
            logger.info("🔄 Starting daily market data sync...")
            
            db = SessionLocal()
            synced_count = 0
            error_count = 0
            
            try:
                # Get symbols to sync
                if not symbols:
                    stocks = stock_master_service.get_stock_master()
                    symbols = [stock["symbol"] for stock in stocks[:100]]  # Limit to 100 for performance
                
                today = date.today()
                
                for symbol in symbols:
                    try:
                        # Get quote data
                        quote = await data_service.get_quote(symbol, exchange="NSE")
                        
                        if not quote or "error" in quote or quote.get("last_price", 0) <= 0:
                            continue
                        
                        # Check if already synced today
                        existing = db.query(DailyMarketData).filter(
                            DailyMarketData.symbol == symbol,
                            DailyMarketData.date == today
                        ).first()
                        
                        if existing:
                            # Update
                            existing.open_price = float(quote.get("open", 0))
                            existing.high_price = float(quote.get("high", 0))
                            existing.low_price = float(quote.get("low", 0))
                            existing.close_price = float(quote.get("last_price", 0))
                            existing.volume = int(quote.get("volume", 0))
                        else:
                            # Create new
                            daily_data = DailyMarketData(
                                symbol=symbol,
                                date=today,
                                open_price=float(quote.get("open", 0)),
                                high_price=float(quote.get("high", 0)),
                                low_price=float(quote.get("low", 0)),
                                close_price=float(quote.get("last_price", 0)),
                                volume=int(quote.get("volume", 0))
                            )
                            db.add(daily_data)
                        
                        synced_count += 1
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.1)
                    
                    except Exception as e:
                        logger.error(f"Error syncing {symbol}: {e}")
                        error_count += 1
                        continue
                
                db.commit()
                logger.info(f"✅ Daily market data sync completed: {synced_count} synced, {error_count} errors")
                
                return {
                    "success": True,
                    "synced": synced_count,
                    "errors": error_count,
                    "date": today.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Error in daily market data sync: {e}")
            return {
                "success": False,
                "error": str(e),
                "synced": 0
            }
    
    async def sync_financial_ratios(self, symbols: list = None) -> Dict:
        """
        Sync financial ratios for all symbols with financial data
        
        Args:
            symbols: List of symbols to sync
        
        Returns:
            Sync results
        """
        try:
            logger.info("🔄 Starting financial ratios sync...")
            
            db = SessionLocal()
            synced_count = 0
            error_count = 0
            
            try:
                # Get symbols with financial data
                if not symbols:
                    financial_data_query = db.query(FinancialData.symbol).distinct()
                    symbols = [row[0] for row in financial_data_query.all()]
                
                for symbol in symbols:
                    try:
                        # Get latest financial data
                        financial_data = db.query(FinancialData).filter(
                            FinancialData.symbol == symbol
                        ).order_by(FinancialData.period_end.desc()).first()
                        
                        if not financial_data:
                            continue
                        
                        # Get current price
                        quote = await data_service.get_quote(symbol, exchange="NSE")
                        current_price = float(quote.get("last_price", 0)) if quote else 0
                        
                        if current_price <= 0:
                            continue
                        
                        # Prepare financial data dict
                        fd_dict = {
                            "period_end": financial_data.period_end,
                            "revenue": float(financial_data.revenue) if financial_data.revenue else None,
                            "net_profit": float(financial_data.net_profit) if financial_data.net_profit else None,
                            "net_worth": float(financial_data.net_worth) if financial_data.net_worth else None,
                            "total_assets": float(financial_data.total_assets) if financial_data.total_assets else None,
                            "total_liabilities": float(financial_data.total_liabilities) if financial_data.total_liabilities else None,
                            "current_assets": float(financial_data.current_assets) if financial_data.current_assets else None,
                            "current_liabilities": float(financial_data.current_liabilities) if financial_data.current_liabilities else None,
                            "eps": float(financial_data.eps) if financial_data.eps else None,
                            "book_value": float(financial_data.book_value) if financial_data.book_value else None,
                            "ebit": float(financial_data.ebit) if financial_data.ebit else None,
                            "capital_employed": float(financial_data.capital_employed) if financial_data.capital_employed else None,
                            "free_cash_flow": float(financial_data.free_cash_flow) if financial_data.free_cash_flow else None
                        }
                        
                        # Calculate ratios
                        ratios = financial_ratios_service.calculate_ratios(
                            symbol=symbol,
                            current_price=current_price,
                            financial_data=fd_dict
                        )
                        
                        # Store in database
                        existing = db.query(FinancialRatios).filter(
                            FinancialRatios.symbol == symbol,
                            FinancialRatios.period_end == financial_data.period_end
                        ).first()
                        
                        if existing:
                            # Update
                            for key, value in ratios.items():
                                if key not in ["symbol", "calculated_at", "period_end"] and value is not None:
                                    setattr(existing, key, value)
                            existing.calculated_at = datetime.utcnow()
                        else:
                            # Create new
                            new_ratios = FinancialRatios(
                                symbol=symbol,
                                period_end=financial_data.period_end,
                                current_price=current_price,
                                pe_ratio=ratios.get("pe_ratio"),
                                pb_ratio=ratios.get("pb_ratio"),
                                roe=ratios.get("roe"),
                                roce=ratios.get("roce"),
                                debt_to_equity=ratios.get("debt_to_equity"),
                                current_ratio=ratios.get("current_ratio"),
                                operating_margin=ratios.get("operating_margin"),
                                profit_growth_5y=ratios.get("profit_growth_5y"),
                                revenue_growth_5y=ratios.get("revenue_growth_5y")
                            )
                            db.add(new_ratios)
                        
                        synced_count += 1
                        await asyncio.sleep(0.1)
                    
                    except Exception as e:
                        logger.error(f"Error syncing ratios for {symbol}: {e}")
                        error_count += 1
                        continue
                
                db.commit()
                logger.info(f"✅ Financial ratios sync completed: {synced_count} synced, {error_count} errors")
                
                return {
                    "success": True,
                    "synced": synced_count,
                    "errors": error_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Error in financial ratios sync: {e}")
            return {
                "success": False,
                "error": str(e),
                "synced": 0
            }

# Create singleton instance
daily_sync_job = DailySyncJob()

