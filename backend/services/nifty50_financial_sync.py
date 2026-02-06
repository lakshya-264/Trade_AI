"""
Nifty 50 Financial Data Sync Service
Syncs financial data (quarterly/annual) for all Nifty 50 stocks from Screener.in
"""

import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.database_unified import FinancialData, FinancialRatios
from services.screener_scraper import screener_scraper
from services.screener_data_service import screener_data_service
from services.financial_ratios_service import financial_ratios_service
from core.data_service import data_service

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

class Nifty50FinancialSync:
    """Sync financial data for all Nifty 50 stocks"""
    
    def __init__(self):
        self.screener_scraper = screener_scraper
        self.screener_data_service = screener_data_service
    
    def _parse_period(self, period_str: str) -> Optional[date]:
        """Parse period string (e.g., 'Mar 2025', 'Q1 FY25') to date"""
        try:
            # Try "Mar 2025" format
            months = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            
            parts = period_str.strip().split()
            if len(parts) >= 2:
                month_str = parts[0].lower()[:3]
                year_str = parts[-1]
                
                if month_str in months and year_str.isdigit():
                    year = int(year_str)
                    # Handle 2-digit years
                    if year < 100:
                        year = 2000 + year if year < 50 else 1900 + year
                    return date(year, months[month_str], 1)
            
            # Try "YYYY-MM-DD" format
            if '-' in period_str:
                return datetime.strptime(period_str.split()[0], '%Y-%m-%d').date()
            
            return None
        except Exception as e:
            logger.debug(f"Error parsing period '{period_str}': {e}")
            return None
    
    def _save_quarterly_data(
        self, 
        db: Session, 
        symbol: str, 
        quarterly_results: List[Dict]
    ) -> int:
        """Save quarterly financial data to database"""
        saved_count = 0
        
        for q_data in quarterly_results:
            try:
                period_str = q_data.get('period', '')
                if not period_str:
                    continue
                    
                period_end = self._parse_period(period_str)
                
                if not period_end:
                    logger.debug(f"Could not parse period '{period_str}' for {symbol}")
                    continue
                
                # Extract financial values - handle various field names
                revenue = q_data.get('sales') or q_data.get('revenue') or q_data.get('total_income')
                net_profit = q_data.get('net_profit') or q_data.get('profit') or q_data.get('net_profit_after_tax')
                eps = q_data.get('eps') or q_data.get('earnings_per_share')
                ebit = q_data.get('ebit') or q_data.get('operating_profit') or q_data.get('pbit')
                
                # Convert to float if needed
                revenue = self._parse_number(revenue) if revenue else None
                net_profit = self._parse_number(net_profit) if net_profit else None
                eps = self._parse_number(eps) if eps else None
                ebit = self._parse_number(ebit) if ebit else None
                
                # Skip if no meaningful data
                if not revenue and not net_profit:
                    continue
                
                # Check if record exists
                existing = db.query(FinancialData).filter(
                    FinancialData.symbol == symbol.upper(),
                    FinancialData.period_type == "QUARTERLY",
                    FinancialData.period_end == period_end
                ).first()
                
                if existing:
                    # Update existing record
                    if revenue:
                        existing.revenue = revenue
                    if net_profit:
                        existing.net_profit = net_profit
                    if eps:
                        existing.eps = eps
                    if ebit:
                        existing.ebit = ebit
                else:
                    # Create new record
                    financial_data = FinancialData(
                        symbol=symbol.upper(),
                        period_type="QUARTERLY",
                        period_end=period_end,
                        revenue=revenue,
                        net_profit=net_profit,
                        eps=eps,
                        ebit=ebit,
                        created_at=datetime.utcnow()
                    )
                    db.add(financial_data)
                
                saved_count += 1
                
            except IntegrityError:
                db.rollback()
                logger.debug(f"Duplicate quarterly data for {symbol} - {period_str}")
            except Exception as e:
                logger.error(f"Error saving quarterly data for {symbol}: {e}")
                db.rollback()
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error committing quarterly data for {symbol}: {e}")
            db.rollback()
        
        return saved_count
    
    def _parse_number(self, value) -> Optional[float]:
        """Parse number string (e.g., '1,234.56 Cr', '₹1,234.56') to float"""
        if value is None:
            return None
        
        # If already a number, return it
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            return None
        
        try:
            # Remove currency symbols, commas, and text
            cleaned = value.replace('₹', '').replace(',', '').replace('Cr', '').replace('cr', '').strip()
            # Remove any remaining text
            cleaned = ''.join(c for c in cleaned if c.isdigit() or c == '.' or c == '-')
            if cleaned:
                num = float(cleaned)
                # If original had 'Cr', multiply by 10000
                if 'Cr' in value or 'cr' in value:
                    num = num * 10000
                return num
        except Exception:
            pass
        return None
    
    async def sync_stock_financial_data(
        self, 
        db: Session, 
        symbol: str
    ) -> Dict[str, any]:
        """Sync financial data for a single stock"""
        try:
            logger.info(f"🔄 Syncing financial data for {symbol}...")
            
            # Fetch data from Screener.in
            company_data = await self.screener_scraper.get_company_data(symbol, consolidated=True)
            
            if not company_data or "error" in company_data:
                return {
                    "symbol": symbol,
                    "success": False,
                    "error": company_data.get("error", "Failed to fetch data"),
                    "quarterly_saved": 0
                }
            
            # Save quarterly results
            quarterly_results = company_data.get("quarterly_results", [])
            quarterly_saved = 0
            
            if quarterly_results:
                quarterly_saved = self._save_quarterly_data(db, symbol, quarterly_results)
            
            # Also save Screener data (growth metrics, balance sheet, etc.)
            screener_saved = False
            try:
                # Save growth metrics
                if "growth_metrics" in company_data and company_data["growth_metrics"]:
                    self.screener_data_service.save_growth_metrics(
                        db, symbol, company_data["growth_metrics"]
                    )
                
                # Save balance sheet
                if "balance_sheet" in company_data and company_data["balance_sheet"]:
                    self.screener_data_service.save_balance_sheet(
                        db, symbol, company_data["balance_sheet"]
                    )
                
                # Save cash flows
                if "cash_flows" in company_data and company_data["cash_flows"]:
                    self.screener_data_service.save_cash_flows(
                        db, symbol, company_data["cash_flows"]
                    )
                
                # Save shareholding
                if "detailed_shareholding" in company_data and company_data["detailed_shareholding"]:
                    self.screener_data_service.save_shareholding(
                        db, symbol, company_data["detailed_shareholding"]
                    )
                
                screener_saved = True
            except Exception as e:
                logger.warning(f"Error saving screener data for {symbol}: {e}")
            
            # Calculate and save financial ratios if we have financial data
            ratios_calculated = 0
            try:
                from datetime import datetime
                
                # Get latest financial data
                latest_financial = db.query(FinancialData).filter(
                    FinancialData.symbol == symbol.upper()
                ).order_by(FinancialData.period_end.desc()).first()
                
                if latest_financial:
                    # Get current price
                    quote = await data_service.get_quote(symbol, exchange="NSE")
                    current_price = float(quote.get("last_price", 0)) if quote else 0
                    
                    if current_price > 0:
                        # Prepare financial data dict
                        fd_dict = {
                            "period_end": latest_financial.period_end,
                            "revenue": float(latest_financial.revenue) if latest_financial.revenue else None,
                            "net_profit": float(latest_financial.net_profit) if latest_financial.net_profit else None,
                            "net_worth": float(latest_financial.net_worth) if latest_financial.net_worth else None,
                            "eps": float(latest_financial.eps) if latest_financial.eps else None,
                            "book_value": float(latest_financial.book_value) if latest_financial.book_value else None,
                            "ebit": float(latest_financial.ebit) if latest_financial.ebit else None,
                        }
                        
                        # Calculate ratios
                        ratios = financial_ratios_service.calculate_ratios(
                            symbol=symbol,
                            current_price=current_price,
                            financial_data=fd_dict
                        )
                        
                        # Save to database
                        existing = db.query(FinancialRatios).filter(
                            FinancialRatios.symbol == symbol.upper(),
                            FinancialRatios.period_end == latest_financial.period_end
                        ).first()
                        
                        if existing:
                            for key, value in ratios.items():
                                if key not in ["symbol", "calculated_at"] and value is not None:
                                    setattr(existing, key, value)
                            existing.calculated_at = datetime.utcnow()
                        else:
                            new_ratios = FinancialRatios(
                                symbol=symbol.upper(),
                                period_end=latest_financial.period_end,
                                current_price=current_price,
                                pe_ratio=ratios.get("pe_ratio"),
                                pb_ratio=ratios.get("pb_ratio"),
                                roe=ratios.get("roe"),
                                roce=ratios.get("roce"),
                                debt_to_equity=ratios.get("debt_to_equity"),
                            )
                            db.add(new_ratios)
                        
                        db.commit()
                        ratios_calculated = 1
            except Exception as e:
                logger.warning(f"Error calculating financial ratios for {symbol}: {e}")
                db.rollback()
            
            return {
                "symbol": symbol,
                "success": True,
                "quarterly_saved": quarterly_saved,
                "screener_saved": screener_saved,
                "ratios_calculated": ratios_calculated,
                "message": f"Synced {quarterly_saved} quarterly records, ratios: {ratios_calculated}"
            }
            
        except Exception as e:
            logger.error(f"Error syncing {symbol}: {e}")
            return {
                "symbol": symbol,
                "success": False,
                "error": str(e),
                "quarterly_saved": 0
            }
    
    async def sync_all_nifty50(
        self, 
        db: Session, 
        max_concurrent: int = 3  # Reduced to avoid rate limiting
    ) -> Dict[str, any]:
        """Sync financial data for all Nifty 50 stocks"""
        logger.info(f"🚀 Starting sync for {len(NIFTY_50_SYMBOLS)} Nifty 50 stocks...")
        
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)  # Limit concurrent requests
        
        async def sync_with_limit(symbol: str):
            async with semaphore:
                # Add delay to avoid rate limiting (2 seconds between requests)
                await asyncio.sleep(2)
                return await self.sync_stock_financial_data(db, symbol)
        
        # Create tasks for all symbols
        tasks = [sync_with_limit(symbol) for symbol in NIFTY_50_SYMBOLS]
        
        # Execute with progress tracking
        completed = 0
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            completed += 1
            
            if result.get("success"):
                logger.info(f"✅ [{completed}/{len(NIFTY_50_SYMBOLS)}] {result['symbol']}: {result.get('quarterly_saved', 0)} quarters saved")
            else:
                logger.warning(f"❌ [{completed}/{len(NIFTY_50_SYMBOLS)}] {result['symbol']}: {result.get('error', 'Failed')}")
        
        # Summary
        successful = sum(1 for r in results if r.get("success"))
        total_quarters = sum(r.get("quarterly_saved", 0) for r in results)
        
        summary = {
            "success": True,
            "total_symbols": len(NIFTY_50_SYMBOLS),
            "successful": successful,
            "failed": len(NIFTY_50_SYMBOLS) - successful,
            "total_quarters_saved": total_quarters,
            "results": results,
            "message": f"Sync completed: {successful}/{len(NIFTY_50_SYMBOLS)} stocks synced, {total_quarters} quarterly records saved"
        }
        
        logger.info(f"✅ Sync complete: {summary['message']}")
        return summary

# Create singleton instance
nifty50_financial_sync = Nifty50FinancialSync()

