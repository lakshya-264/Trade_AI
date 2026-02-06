"""
Frontend Data Indicator System
Provides clear indicators for data types and reliability levels
"""

from typing import Dict, Any
from datetime import datetime
from enum import Enum

class DataType(Enum):
    """Data type indicators for frontend"""
    LIVE_DATA = "live_data"
    CACHED_DATA = "cached_data"
    ESTIMATED_DATA = "estimated_data"
    MOCK_DATA = "mock_data"
    ERROR_DATA = "error_data"

class DataStatus(Enum):
    """Data status indicators"""
    REAL_TIME = "real_time"
    NEAR_REAL_TIME = "near_real_time"
    ESTIMATED = "estimated"
    SIMULATED = "simulated"
    ERROR = "error"

class FrontendDataIndicator:
    """Generates frontend indicators for different data types"""
    
    @staticmethod
    def get_live_data_indicator(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate indicators for live NSE data"""
        return {
            "data_type": DataType.LIVE_DATA.value,
            "data_status": DataStatus.REAL_TIME.value,
            "frontend_indicator": "🟢 LIVE",
            "frontend_message": "Live market data from NSE",
            "frontend_color": "#10B981",  # Green
            "frontend_bg_color": "#D1FAE5",  # Light green
            "frontend_border": "2px solid #10B981",
            "reliability_score": 100,
            "data_freshness": "Real-time",
            "last_updated": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_cached_data_indicator(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate indicators for cached data"""
        cache_age = quote_data.get("cache_age_seconds", 0)
        
        return {
            "data_type": DataType.CACHED_DATA.value,
            "data_status": DataStatus.NEAR_REAL_TIME.value,
            "frontend_indicator": "🟡 CACHED",
            "frontend_message": f"Data cached {cache_age} seconds ago",
            "frontend_color": "#F59E0B",  # Amber
            "frontend_bg_color": "#FEF3C7",  # Light amber
            "frontend_border": "2px solid #F59E0B",
            "reliability_score": 85,
            "data_freshness": f"{cache_age}s old",
            "cache_age_seconds": cache_age,
            "last_updated": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_estimated_data_indicator(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate indicators for estimated data"""
        return {
            "data_type": DataType.ESTIMATED_DATA.value,
            "data_status": DataStatus.ESTIMATED.value,
            "frontend_indicator": "🟠 ESTIMATED",
            "frontend_message": "Price estimated from market patterns",
            "frontend_color": "#F97316",  # Orange
            "frontend_bg_color": "#FED7AA",  # Light orange
            "frontend_border": "2px solid #F97316",
            "reliability_score": 70,
            "data_freshness": "Estimated",
            "estimation_method": quote_data.get("estimation_method", "market_pattern_analysis"),
            "last_updated": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_mock_data_indicator(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate indicators for mock data"""
        return {
            "data_type": DataType.MOCK_DATA.value,
            "data_status": DataStatus.SIMULATED.value,
            "frontend_indicator": "🔴 MOCK",
            "frontend_message": "Simulated data - real market data unavailable",
            "frontend_color": "#EF4444",  # Red
            "frontend_bg_color": "#FEE2E2",  # Light red
            "frontend_border": "2px solid #EF4444",
            "reliability_score": 30,
            "data_freshness": "Simulated",
            "fallback_reason": quote_data.get("fallback_reason", "all_real_sources_failed"),
            "last_updated": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_error_data_indicator(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate indicators for error data"""
        return {
            "data_type": DataType.ERROR_DATA.value,
            "data_status": DataStatus.ERROR.value,
            "frontend_indicator": "⚫ ERROR",
            "frontend_message": "Unable to fetch market data",
            "frontend_color": "#6B7280",  # Gray
            "frontend_bg_color": "#F3F4F6",  # Light gray
            "frontend_border": "2px solid #6B7280",
            "reliability_score": 0,
            "data_freshness": "Error",
            "error_message": quote_data.get("error", "Unknown error"),
            "last_updated": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_yahoo_finance_indicator(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate indicators for Yahoo Finance data"""
        return {
            "data_type": DataType.LIVE_DATA.value,
            "data_status": DataStatus.REAL_TIME.value,
            "frontend_indicator": "📈 LIVE",
            "frontend_message": "Live data from Yahoo Finance",
            "frontend_color": "#10B981",  # Green
            "frontend_bg_color": "#D1FAE5",  # Light green
            "frontend_border": "2px solid #10B981",
            "reliability_score": 95,
            "data_freshness": "Real-time",
            "data_source_name": "Yahoo Finance",
            "last_updated": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_alpha_vantage_indicator(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate indicators for Alpha Vantage data"""
        return {
            "data_type": DataType.LIVE_DATA.value,
            "data_status": DataStatus.REAL_TIME.value,
            "frontend_indicator": "🟢 LIVE",
            "frontend_message": "Live data from Alpha Vantage",
            "frontend_color": "#10B981",  # Green
            "frontend_bg_color": "#D1FAE5",  # Light green
            "frontend_border": "2px solid #10B981",
            "reliability_score": 90,
            "data_freshness": "Real-time",
            "data_source_name": "Alpha Vantage",
            "last_updated": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_investing_com_indicator(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate indicators for Investing.com data"""
        return {
            "data_type": DataType.LIVE_DATA.value,
            "data_status": DataStatus.REAL_TIME.value,
            "frontend_indicator": "🔍 LIVE",
            "frontend_message": "Live data from Investing.com",
            "frontend_color": "#10B981",  # Green
            "frontend_bg_color": "#D1FAE5",  # Light green
            "frontend_border": "2px solid #10B981",
            "reliability_score": 85,
            "data_freshness": "Real-time",
            "data_source_name": "Investing.com",
            "last_updated": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_indicator_for_data_source(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get appropriate indicator based on data source"""
        data_source = quote_data.get("data_source", "unknown")
        
        if data_source == "NSE_REAL":
            return FrontendDataIndicator.get_live_data_indicator(quote_data)
        elif data_source == "NSE_CACHED":
            return FrontendDataIndicator.get_cached_data_indicator(quote_data)
        elif data_source in ["YAHOO_FINANCE", "YAHOO_FINANCE_API"]:
            return FrontendDataIndicator.get_yahoo_finance_indicator(quote_data)
        elif data_source == "ALPHA_VANTAGE":
            return FrontendDataIndicator.get_alpha_vantage_indicator(quote_data)
        elif data_source in ["INVESTING_COM", "INVESTING_COM_SCRAPING"]:
            return FrontendDataIndicator.get_investing_com_indicator(quote_data)
        elif data_source == "ESTIMATED":
            return FrontendDataIndicator.get_estimated_data_indicator(quote_data)
        elif data_source in ["MOCK", "MOCK_FALLBACK"]:
            return FrontendDataIndicator.get_mock_data_indicator(quote_data)
        elif data_source == "ERROR":
            return FrontendDataIndicator.get_error_data_indicator(quote_data)
        else:
            # Default to mock data indicator
            return FrontendDataIndicator.get_mock_data_indicator(quote_data)
    
    @staticmethod
    def enhance_quote_with_indicators(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance quote data with frontend indicators"""
        indicators = FrontendDataIndicator.get_indicator_for_data_source(quote_data)
        
        # Merge indicators with quote data
        enhanced_quote = {**quote_data, **indicators}
        
        return enhanced_quote

# Global indicator system
frontend_indicator = FrontendDataIndicator()
