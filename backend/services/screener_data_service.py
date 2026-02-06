"""
Screener Data Service
Saves screener.in scraped data to database
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from dateutil import parser

from core.database_unified import (
    ScreenerGrowthMetrics,
    ScreenerBalanceSheet,
    ScreenerCashFlow,
    ScreenerShareholding
)

logger = logging.getLogger(__name__)

class ScreenerDataService:
    """Service to save and retrieve screener.in data from database"""
    
    def save_growth_metrics(self, db: Session, symbol: str, growth_metrics: Dict) -> bool:
        """Save growth metrics to database"""
        try:
            symbol_upper = symbol.upper()
            
            # Check if exists
            existing = db.query(ScreenerGrowthMetrics).filter(
                ScreenerGrowthMetrics.symbol == symbol_upper
            ).first()
            
            if existing:
                # Update
                for key, value in growth_metrics.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                # Create new
                new_metrics = ScreenerGrowthMetrics(
                    symbol=symbol_upper,
                    **{k: v for k, v in growth_metrics.items() if hasattr(ScreenerGrowthMetrics, k)}
                )
                db.add(new_metrics)
            
            db.commit()
            return True
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving growth metrics for {symbol}: {e}")
            return False
    
    def save_balance_sheet(self, db: Session, symbol: str, balance_sheet_data: List[Dict]) -> int:
        """Save balance sheet data to database"""
        saved_count = 0
        try:
            symbol_upper = symbol.upper()
            
            for data in balance_sheet_data:
                try:
                    # Parse period to date
                    period = data.get('period', '')
                    period_date = self._parse_period_to_date(period)
                    
                    if not period_date:
                        continue
                    
                    # Check if exists
                    existing = db.query(ScreenerBalanceSheet).filter(
                        and_(
                            ScreenerBalanceSheet.symbol == symbol_upper,
                            ScreenerBalanceSheet.period_end == period_date
                        )
                    ).first()
                    
                    if existing:
                        # Update
                        if data.get('equity_capital') is not None:
                            existing.equity_capital = data['equity_capital']
                        if data.get('reserves') is not None:
                            existing.reserves = data['reserves']
                        if data.get('borrowings') is not None:
                            existing.borrowings = data['borrowings']
                    else:
                        # Create new
                        new_bs = ScreenerBalanceSheet(
                            symbol=symbol_upper,
                            period_end=period_date,
                            equity_capital=data.get('equity_capital'),
                            reserves=data.get('reserves'),
                            borrowings=data.get('borrowings')
                        )
                        db.add(new_bs)
                    
                    saved_count += 1
                except Exception as e:
                    logger.debug(f"Error saving balance sheet entry: {e}")
                    continue
            
            db.commit()
            return saved_count
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving balance sheet for {symbol}: {e}")
            return saved_count
    
    def save_cash_flows(self, db: Session, symbol: str, cash_flow_data: List[Dict]) -> int:
        """Save cash flow data to database"""
        saved_count = 0
        try:
            symbol_upper = symbol.upper()
            
            for data in cash_flow_data:
                try:
                    period = data.get('period', '')
                    period_date = self._parse_period_to_date(period)
                    
                    if not period_date:
                        continue
                    
                    # Check if exists
                    existing = db.query(ScreenerCashFlow).filter(
                        and_(
                            ScreenerCashFlow.symbol == symbol_upper,
                            ScreenerCashFlow.period_end == period_date
                        )
                    ).first()
                    
                    if existing:
                        # Update
                        if data.get('operating_cash_flow') is not None:
                            existing.operating_cash_flow = data['operating_cash_flow']
                        if data.get('investing_cash_flow') is not None:
                            existing.investing_cash_flow = data['investing_cash_flow']
                        if data.get('financing_cash_flow') is not None:
                            existing.financing_cash_flow = data['financing_cash_flow']
                    else:
                        # Create new
                        new_cf = ScreenerCashFlow(
                            symbol=symbol_upper,
                            period_end=period_date,
                            operating_cash_flow=data.get('operating_cash_flow'),
                            investing_cash_flow=data.get('investing_cash_flow'),
                            financing_cash_flow=data.get('financing_cash_flow')
                        )
                        db.add(new_cf)
                    
                    saved_count += 1
                except Exception as e:
                    logger.debug(f"Error saving cash flow entry: {e}")
                    continue
            
            db.commit()
            return saved_count
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving cash flows for {symbol}: {e}")
            return saved_count
    
    def save_shareholding(self, db: Session, symbol: str, shareholding_data: List[Dict]) -> int:
        """Save shareholding pattern data to database"""
        saved_count = 0
        try:
            symbol_upper = symbol.upper()
            
            for data in shareholding_data:
                try:
                    period = data.get('period', '')
                    period_date = self._parse_period_to_date(period)
                    
                    if not period_date:
                        continue
                    
                    # Check if exists
                    existing = db.query(ScreenerShareholding).filter(
                        and_(
                            ScreenerShareholding.symbol == symbol_upper,
                            ScreenerShareholding.period_end == period_date
                        )
                    ).first()
                    
                    if existing:
                        # Update
                        if data.get('promoters') is not None:
                            existing.promoters = data['promoters']
                        if data.get('fiis') is not None:
                            existing.fiis = data['fiis']
                        if data.get('diis') is not None:
                            existing.diis = data['diis']
                        if data.get('government') is not None:
                            existing.government = data['government']
                        if data.get('public') is not None:
                            existing.public = data['public']
                        if data.get('no_of_shareholders') is not None:
                            existing.no_of_shareholders = data['no_of_shareholders']
                    else:
                        # Create new
                        new_sh = ScreenerShareholding(
                            symbol=symbol_upper,
                            period_end=period_date,
                            promoters=data.get('promoters'),
                            fiis=data.get('fiis'),
                            diis=data.get('diis'),
                            government=data.get('government'),
                            public=data.get('public'),
                            no_of_shareholders=data.get('no_of_shareholders')
                        )
                        db.add(new_sh)
                    
                    saved_count += 1
                except Exception as e:
                    logger.debug(f"Error saving shareholding entry: {e}")
                    continue
            
            db.commit()
            return saved_count
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving shareholding for {symbol}: {e}")
            return saved_count
    
    def _parse_period_to_date(self, period: str) -> Optional[date]:
        """Parse period string (e.g., 'Mar 2025', 'Sep 2025') to date"""
        try:
            # Try to parse the period
            parsed_date = parser.parse(period, default=datetime(2025, 1, 1))
            return parsed_date.date()
        except:
            try:
                # Fallback: try to extract month and year
                import re
                match = re.search(r'(\w+)\s+(\d{4})', period)
                if match:
                    month_str = match.group(1)
                    year = int(match.group(2))
                    month_map = {
                        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                    }
                    month = month_map.get(month_str[:3], 1)
                    return date(year, month, 1)
            except:
                pass
        return None
    
    def get_growth_metrics(self, db: Session, symbol: str) -> Optional[ScreenerGrowthMetrics]:
        """Get growth metrics from database"""
        try:
            return db.query(ScreenerGrowthMetrics).filter(
                ScreenerGrowthMetrics.symbol == symbol.upper()
            ).first()
        except Exception as e:
            logger.error(f"Error getting growth metrics for {symbol}: {e}")
            return None
    
    def get_balance_sheet(self, db: Session, symbol: str, limit: int = 10) -> List[ScreenerBalanceSheet]:
        """Get balance sheet data from database"""
        try:
            return db.query(ScreenerBalanceSheet).filter(
                ScreenerBalanceSheet.symbol == symbol.upper()
            ).order_by(ScreenerBalanceSheet.period_end.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting balance sheet for {symbol}: {e}")
            return []
    
    def get_cash_flows(self, db: Session, symbol: str, limit: int = 10) -> List[ScreenerCashFlow]:
        """Get cash flow data from database"""
        try:
            return db.query(ScreenerCashFlow).filter(
                ScreenerCashFlow.symbol == symbol.upper()
            ).order_by(ScreenerCashFlow.period_end.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting cash flows for {symbol}: {e}")
            return []
    
    def get_shareholding(self, db: Session, symbol: str, limit: int = 12) -> List[ScreenerShareholding]:
        """Get shareholding pattern from database"""
        try:
            return db.query(ScreenerShareholding).filter(
                ScreenerShareholding.symbol == symbol.upper()
            ).order_by(ScreenerShareholding.period_end.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting shareholding for {symbol}: {e}")
            return []

# Create singleton instance
screener_data_service = ScreenerDataService()

