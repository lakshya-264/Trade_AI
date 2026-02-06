"""
Financial Ratios Calculator Service
Calculates all financial ratios from financial data
100% Legal - Your own calculations
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)

class FinancialRatiosService:
    """Calculate financial ratios from financial data"""
    
    def __init__(self):
        pass
    
    def calculate_ratios(
        self,
        symbol: str,
        current_price: float,
        financial_data: Dict,
        previous_financial_data: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate all financial ratios
        
        Args:
            symbol: Stock symbol
            current_price: Current market price
            financial_data: Current period financial data
            previous_financial_data: Previous period for growth calculations
        
        Returns:
            Dictionary with all calculated ratios
        """
        try:
            ratios = {
                "symbol": symbol,
                "current_price": current_price,
                "period_end": financial_data.get("period_end"),
                "calculated_at": datetime.utcnow().isoformat()
            }
            
            # Extract financial data
            revenue = self._safe_float(financial_data.get("revenue"))
            net_profit = self._safe_float(financial_data.get("net_profit"))
            net_worth = self._safe_float(financial_data.get("net_worth"))
            total_assets = self._safe_float(financial_data.get("total_assets"))
            total_liabilities = self._safe_float(financial_data.get("total_liabilities"))
            current_assets = self._safe_float(financial_data.get("current_assets"))
            current_liabilities = self._safe_float(financial_data.get("current_liabilities"))
            eps = self._safe_float(financial_data.get("eps"))
            book_value = self._safe_float(financial_data.get("book_value"))
            ebit = self._safe_float(financial_data.get("ebit"))
            capital_employed = self._safe_float(financial_data.get("capital_employed"))
            free_cash_flow = self._safe_float(financial_data.get("free_cash_flow"))
            
            # 1. PE Ratio = Price / EPS
            if eps and eps > 0:
                ratios["pe_ratio"] = round(current_price / eps, 2)
            else:
                ratios["pe_ratio"] = None
            
            # 2. PB Ratio = Price / Book Value
            if book_value and book_value > 0:
                ratios["pb_ratio"] = round(current_price / book_value, 2)
            else:
                ratios["pb_ratio"] = None
            
            # 3. ROE = Net Profit / Net Worth
            if net_worth and net_worth > 0:
                ratios["roe"] = round((net_profit / net_worth) * 100, 2) if net_profit else None
            else:
                ratios["roe"] = None
            
            # 4. ROCE = EBIT / Capital Employed
            if capital_employed and capital_employed > 0:
                ratios["roce"] = round((ebit / capital_employed) * 100, 2) if ebit else None
            else:
                ratios["roce"] = None
            
            # 5. Debt-to-Equity = Total Liabilities / Net Worth
            if net_worth and net_worth > 0:
                ratios["debt_to_equity"] = round(total_liabilities / net_worth, 2) if total_liabilities else None
            else:
                ratios["debt_to_equity"] = None
            
            # 6. Current Ratio = Current Assets / Current Liabilities
            if current_liabilities and current_liabilities > 0:
                ratios["current_ratio"] = round(current_assets / current_liabilities, 2) if current_assets else None
            else:
                ratios["current_ratio"] = None
            
            # 7. Operating Margin = (EBIT / Revenue) * 100
            if revenue and revenue > 0:
                ratios["operating_margin"] = round((ebit / revenue) * 100, 2) if ebit else None
            else:
                ratios["operating_margin"] = None
            
            # 8. Profit Growth 5Y (if previous data available)
            if previous_financial_data:
                prev_profit = self._safe_float(previous_financial_data.get("net_profit"))
                if prev_profit and prev_profit > 0 and net_profit:
                    profit_growth = ((net_profit - prev_profit) / prev_profit) * 100
                    ratios["profit_growth_5y"] = round(profit_growth, 2)
                else:
                    ratios["profit_growth_5y"] = None
            else:
                ratios["profit_growth_5y"] = None
            
            # 9. Revenue Growth 5Y (if previous data available)
            if previous_financial_data:
                prev_revenue = self._safe_float(previous_financial_data.get("revenue"))
                if prev_revenue and prev_revenue > 0 and revenue:
                    revenue_growth = ((revenue - prev_revenue) / prev_revenue) * 100
                    ratios["revenue_growth_5y"] = round(revenue_growth, 2)
                else:
                    ratios["revenue_growth_5y"] = None
            else:
                ratios["revenue_growth_5y"] = None
            
            # 10. Free Cash Flow (already in data)
            ratios["free_cash_flow"] = free_cash_flow
            
            logger.info(f"✅ Calculated financial ratios for {symbol}")
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating financial ratios for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "calculated_at": datetime.utcnow().isoformat()
            }
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, Decimal):
                return float(value)
            if isinstance(value, str):
                # Remove commas and convert
                cleaned = value.replace(',', '').strip()
                return float(cleaned) if cleaned else None
            return None
        except (ValueError, TypeError):
            return None
    
    def calculate_growth_rates(
        self,
        financial_data_list: List[Dict]
    ) -> Dict:
        """
        Calculate 5-year growth rates from historical data
        
        Args:
            financial_data_list: List of financial data dicts, sorted by period_end (oldest first)
        
        Returns:
            Dictionary with growth rates
        """
        try:
            if len(financial_data_list) < 2:
                return {
                    "profit_growth_5y": None,
                    "revenue_growth_5y": None
                }
            
            # Get first and last periods
            first = financial_data_list[0]
            last = financial_data_list[-1]
            
            first_profit = self._safe_float(first.get("net_profit"))
            last_profit = self._safe_float(last.get("net_profit"))
            first_revenue = self._safe_float(first.get("revenue"))
            last_revenue = self._safe_float(last.get("revenue"))
            
            growth_rates = {}
            
            # Profit growth
            if first_profit and last_profit and first_profit > 0:
                profit_growth = ((last_profit - first_profit) / first_profit) * 100
                growth_rates["profit_growth_5y"] = round(profit_growth, 2)
            else:
                growth_rates["profit_growth_5y"] = None
            
            # Revenue growth
            if first_revenue and last_revenue and first_revenue > 0:
                revenue_growth = ((last_revenue - first_revenue) / first_revenue) * 100
                growth_rates["revenue_growth_5y"] = round(revenue_growth, 2)
            else:
                growth_rates["revenue_growth_5y"] = None
            
            return growth_rates
            
        except Exception as e:
            logger.error(f"Error calculating growth rates: {e}")
            return {
                "profit_growth_5y": None,
                "revenue_growth_5y": None
            }

# Create singleton instance
financial_ratios_service = FinancialRatiosService()

